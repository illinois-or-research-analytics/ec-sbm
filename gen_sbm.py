import os
import csv
import time
import argparse

import pandas as pd
import numpy as np
import graph_tool.all as gt
from scipy.sparse import dok_matrix

from src.utils import set_up
from src.constants import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--edgelist', type=str, required=True)
    parser.add_argument('--clustering', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    parser.add_argument('--seed', type=int, required=False, default=0)
    return parser.parse_args()


print('Generation')
print('== Input == ')

args = parse_args()
edgelist_fn = args.edgelist
clustering_fn = args.clustering
output_dir = args.output_folder
seed = args.seed

print(f'Method: ABCD-MCS')
print(f'Network: {edgelist_fn}')
print(f'Clustering: {clustering_fn}')
print(f'Output folder: {output_dir}')
print(f'Seed: {seed}')

print('== Output == ')

logs = []

start = time.perf_counter()
set_up(
    edgelist_fn,
    clustering_fn,
    seed,
    output_dir,
    use_existing_clustering=True,
)
elapsed = time.perf_counter() - start
logs.append(f"Setup time: {elapsed}")

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

# Compute clustering
b = np.array([
    node2cluster[node_iid]
    for node_iid in all_nodes
])

# Compute edges between clusters
num_clusters = len(all_clusters)
probs = dok_matrix((num_clusters, num_clusters), dtype=int)
for src_iid, tgt_iids in neighbor.items():
    for tgt_iid in tgt_iids:
        probs[node2cluster[src_iid], node2cluster[tgt_iid]] += 1
probs = probs.tocsr()

# Compute degree sequence
out_degs = np.array([
    len(neighbor[node_iid])
    for node_iid in all_nodes
])

elapsed = time.perf_counter() - start
logs.append(f"Setup time: {elapsed}")

start = time.perf_counter()

# Generate SBM
start = time.perf_counter()
g = gt.generate_sbm(
    b,
    probs,
    out_degs=out_degs,
    micro_ers=True,
    micro_degs=True,
    directed=False,
)
# gt.remove_parallel_edges(g)
# gt.remove_self_loops(g)

elapsed = time.perf_counter() - start
logs.append(f"Generation time: {elapsed}")

start = time.perf_counter()

# Copy clustering file
with open(f'{output_dir}/{COM_OUT}', 'w') as f:
    df = pd.DataFrame([
        (node_iid2id[node_iid], cluster_iid2id[cluster_iid])
        for node_iid, cluster_iid in node2cluster.items()
    ],
        columns=['node_id', 'cluster_id'],
    )
    df.to_csv(f, sep='\t', index=False, header=False)

# Save edge list
with open(f'{output_dir}/{EDGE}', 'w') as f:
    df = pd.DataFrame([
        (node_iid2id[src], node_iid2id[tgt])
        for src, tgt in g.iter_edges()
    ],
        columns=['src_id', 'tgt_id'],
    )
    df.to_csv(f, sep='\t', index=False, header=False)

elapsed = time.perf_counter() - start
logs.append(f"Post-process time: {elapsed}")

assert os.path.exists(output_dir)
log_f = open(f'{output_dir}/run.log', 'w')
for log in logs:
    log_f.write(log)
    log_f.write('\n')
log_f.close()
