import csv
import time
import logging
import argparse
from pathlib import Path

import numpy as np
from scipy.sparse import dok_matrix
import graph_tool.all as gt
import pandas as pd

from src.utils import set_up
from src.constants import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-edgelist', type=str, required=True)
    parser.add_argument('--input-clustering', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    parser.add_argument('--seed', type=int, required=False, default=0)
    return parser.parse_args()


args = parse_args()
edgelist_fn = args.input_edgelist
clustering_fn = args.input_clustering
output_dir = args.output_folder
seed = args.seed

# ========================

Path(output_dir).mkdir(parents=True, exist_ok=True)
log_path = Path(output_dir) / 'run.log'
logging.basicConfig(
    filename=log_path,
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# ========================

logging.info(f'Network: {edgelist_fn}')
logging.info(f'Clustering: {clustering_fn}')
logging.info(f'Output folder: {output_dir}')
logging.info(f'Seed: {seed}')

# ========================

start = time.perf_counter()

set_up(
    edgelist_fn,
    clustering_fn,
    seed,
    output_dir,
    use_existing_clustering=True,
)

# Compute node and cluster mappings
node_id2iid = dict()
with open(f'{output_dir}/{NODE_ID}') as f:
    reader = csv.reader(f, delimiter='\t')
    for node_iid, (node_id,) in enumerate(reader):
        node_id2iid[node_id] = node_iid

cluster_id2iid = dict()
with open(f'{output_dir}/{COM_ID}') as f:
    reader = csv.reader(f, delimiter='\t')
    for cluster_iid, (cluster_id,) in enumerate(reader):
        cluster_id2iid[cluster_id] = cluster_iid

clustering = dict()
with open(clustering_fn, 'r') as f:
    reader = csv.reader(f, delimiter='\t')
    for node_id, cluster_id in reader:
        if node_id not in node_id2iid:
            node_id2iid[node_id] = len(node_id2iid)
        node_iid = node_id2iid[node_id]

        if cluster_id not in cluster_id2iid:
            cluster_id2iid[cluster_id] = len(cluster_id2iid)
        cluster_iid = cluster_id2iid[cluster_id]

        clustering.setdefault(cluster_iid, []).append(node_iid)

node_iid2id = {
    v: k
    for k, v in node_id2iid.items()
}
cluster_iid2id = {
    v: k
    for k, v in cluster_id2iid.items()
}
node2cluster = {
    node_iid: cluster_iid
    for cluster_iid, nodes_iids in clustering.items()
    for node_iid in nodes_iids
}

all_nodes = list(node_id2iid.values())
all_clusters = list(cluster_id2iid.values())

# Compute neighbor
neighbor = dict()
with open(edgelist_fn, 'r') as f:
    reader = csv.reader(f, delimiter='\t')
    for src_id, tgt_id in reader:
        src_iid = node_id2iid[src_id]
        tgt_iid = node_id2iid[tgt_id]

        neighbor.setdefault(src_iid, set()).add(tgt_iid)
        neighbor.setdefault(tgt_iid, set()).add(src_iid)

mcs = list()
with open(f'{output_dir}/{MCS}') as f:
    reader = csv.reader(f, delimiter='\t')
    for mcs_val, in reader:
        mcs.append(int(mcs_val))

deg = list()
with open(f'{output_dir}/{DEG}') as f:
    reader = csv.reader(f, delimiter='\t')
    for deg_val, in reader:
        deg.append(int(deg_val))
deg = np.array(deg)

# Compute edges between clusters
num_clusters = len(all_clusters)
probs = dok_matrix((num_clusters, num_clusters), dtype=int)
for src_iid, tgt_iids in neighbor.items():
    for tgt_iid in tgt_iids:
        probs[node2cluster[src_iid], node2cluster[tgt_iid]] += 1
# probs = probs.tocsr()

elapsed = time.perf_counter() - start
logging.info(f"Setup: {elapsed}")

# ========================


def create_edge(u, v):
    return (min(u, v), max(u, v))


def generate_cluster(cluster_nodes, k):
    if k == 0:
        return set()

    global deg
    global probs

    int_deg = deg.copy()

    n = len(cluster_nodes)
    cluster_nodes_ordered = sorted(
        cluster_nodes,
        key=lambda node_iid: int_deg[node_iid],
        reverse=True,
    )

    # print(f'Ordered list of nodes: {cluster_nodes_ordered}')
    # print(f'Degree: {int_deg[cluster_nodes_ordered]}')

    processed_nodes = set()
    edges = set()

    i = 0
    while i <= k:
        u = cluster_nodes_ordered[i]
        # print(f'==> Process node {u}')

        for v in processed_nodes:
            assert int_deg[u] > 0

            # print(f'Pick node {v}')
            if probs[node2cluster[u], node2cluster[v]] == 0:
                int_deg[u] += 1
                int_deg[v] += 1
                probs[node2cluster[u], node2cluster[v]] += 1
                probs[node2cluster[v], node2cluster[u]] += 1

            if int_deg[v] == 0:
                int_deg[u] += 1
                int_deg[v] += 1
                probs[node2cluster[u], node2cluster[v]] += 1
                probs[node2cluster[v], node2cluster[u]] += 1

            edges.add(create_edge(u, v))
            int_deg[u] -= 1
            int_deg[v] -= 1
            probs[node2cluster[u], node2cluster[v]] -= 1
            probs[node2cluster[v], node2cluster[u]] -= 1
            # print(f'Add edge {u} {v}')
            # print(f'Probs uv: {probs[node2cluster[u], node2cluster[v]]}')

        processed_nodes.add(u)
        # print(f'Add node {u}')

        i += 1

    while i < n:
        u = cluster_nodes_ordered[i]
        # print(f'==> Process node {u}')

        processed_nodes_ordered = sorted(
            processed_nodes,
            key=lambda node_iid: int_deg[node_iid],
            reverse=True,
        )
        n_processed = len(processed_nodes_ordered)

        candidates = set(x for x in processed_nodes)

        ii = 0
        iii = 0
        while ii < k and iii < n_processed:
            assert int_deg[u] > 0

            v = processed_nodes_ordered[iii]
            iii += 1

            if probs[node2cluster[u], node2cluster[v]] == 0:
                int_deg[u] += 1
                int_deg[v] += 1
                probs[node2cluster[u], node2cluster[v]] += 1
                probs[node2cluster[v], node2cluster[u]] += 1

            # print(f'Pick node {v}')
            if int_deg[v] == 0:
                # print(f'Node {v} has degree 0. Skip.')
                continue

            edges.add(create_edge(u, v))
            int_deg[u] -= 1
            int_deg[v] -= 1
            probs[node2cluster[u], node2cluster[v]] -= 1
            probs[node2cluster[v], node2cluster[u]] -= 1
            # print(f'Add edge {u} {v}')
            # print(f'Probs uv: {probs[node2cluster[u], node2cluster[v]]}')

            candidates.remove(v)

            ii += 1

        while ii < k:
            assert int_deg[u] > 0

            list_candidates = list(candidates)
            weights = deg[list_candidates] / deg[list_candidates].sum()
            v = np.random.choice(list_candidates, p=weights)

            if probs[node2cluster[u], node2cluster[v]] == 0:
                int_deg[u] += 1
                int_deg[v] += 1
                probs[node2cluster[u], node2cluster[v]] += 1
                probs[node2cluster[v], node2cluster[u]] += 1

            if int_deg[v] == 0:
                int_deg[u] += 1
                int_deg[v] += 1
                probs[node2cluster[u], node2cluster[v]] += 1
                probs[node2cluster[v], node2cluster[u]] += 1

            edges.add(create_edge(u, v))
            int_deg[u] -= 1
            int_deg[v] -= 1
            probs[node2cluster[u], node2cluster[v]] -= 1
            probs[node2cluster[v], node2cluster[u]] -= 1
            # print(f'Add edge {u} {v}')
            # print(f'Probs uv: {probs[node2cluster[u], node2cluster[v]]}')

            candidates.remove(v)

            ii += 1

        processed_nodes.add(u)
        # print(f'Add node {u}')

        i += 1

    deg = int_deg

    # print(f'Edges: {edges}')

    return edges


start = time.perf_counter()

edges = set()
for cluster_iid, cluster_nodes in clustering.items():
    info = f"Generation of cluster {cluster_iid} ({len(cluster_nodes)} | {
        mcs[cluster_iid]})"
    logging.info(info)

    sub_start = time.perf_counter()
    # print(f'Generate cluster {cluster_iid}')
    # print(f'List of nodes: {cluster_nodes}')
    # print(f'MCS: {mcs[cluster_iid]}')

    # print(f'Degree (before): {deg[cluster_nodes]}')
    local_edges = generate_cluster(cluster_nodes, mcs[cluster_iid])
    # print(f'Degree (after): {deg[cluster_nodes]}')

    edges.update(local_edges)

    sub_elapsed = time.perf_counter() - sub_start

    logging.info(f"Time: {sub_elapsed}")

elapsed = time.perf_counter() - start
logging.info(f"Generation of k-edge-connected graphs: {elapsed}")

# ========================

start = time.perf_counter()

# print(f'Edges: {edges}')

b = np.array([
    node2cluster[node_iid]
    for node_iid in all_nodes
])
probs = probs.tocsr()
out_degs = deg

# # print(b)
# print(probs.toarray())
# print(out_degs)

elapsed = time.perf_counter() - start
logging.info(f"Computing the input to SBM-NG: {elapsed}")

# ========================

start = time.perf_counter()

if out_degs.sum() > 0:
    g = gt.generate_sbm(
        b,
        probs,
        out_degs=out_degs,
        micro_ers=True,
        micro_degs=True,
        directed=False,
    )
else:
    g = gt.Graph(directed=False)
g.add_edge_list(edges)
gt.remove_parallel_edges(g)
gt.remove_self_loops(g)

elapsed = time.perf_counter() - start
logging.info(f"Generation of the remaining network: {elapsed}")

# ========================

start = time.perf_counter()

with open(f'{output_dir}/{COM_OUT}', 'w') as f:
    df = pd.DataFrame([
        (node_iid2id[node_iid], cluster_iid2id[cluster_iid])
        for node_iid, cluster_iid in node2cluster.items()
    ],
        columns=['node_id', 'cluster_id'],
    )
    df.to_csv(f, sep='\t', index=False, header=False)

with open(f'{output_dir}/{EDGE}', 'w') as f:
    df = pd.DataFrame([
        (node_iid2id[src], node_iid2id[tgt])
        for src, tgt in g.iter_edges()
    ],
        columns=['src_id', 'tgt_id'],
    )
    df.to_csv(f, sep='\t', index=False, header=False)

elapsed = time.perf_counter() - start
logging.info(f"Post-processing: {elapsed}")
