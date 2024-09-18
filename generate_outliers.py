from pathlib import Path
import argparse
import csv
import copy
import time
import os

import pandas as pd
import numpy as np
import graph_tool.all as gt
from scipy.sparse import dok_matrix

from src.constants import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--orig-edgelist', type=str, required=True)
    parser.add_argument('--orig-clustering', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    return parser.parse_args()


args = parse_args()

orig_edgelist_fp = Path(args.orig_edgelist)
orig_clustering_fp = Path(args.orig_clustering)
output_dir = Path(args.output_folder)

logs = []

print(f'Generation of Outlier Subnetwork')
print(f'Network: {orig_edgelist_fp}')
print(f'Clustering: {orig_clustering_fp}')
print(f'Output folder: {output_dir}')

logs.append(f'Generation of Outlier Subnetwork')
logs.append(f'Network: {orig_edgelist_fp}')
logs.append(f'Clustering: {orig_clustering_fp}')
logs.append(f'Output folder: {output_dir}')
logs.append('')

print('== Output == ')

start = time.perf_counter()

output_dir.mkdir(parents=True, exist_ok=True)

node_id2iid = dict()
node_iid2id = dict()

cluster_id2iid = dict()
cluster_iid2id = dict()

orig_nodeiid_clusteriid = dict()
orig_clusteriid_nodeiids = dict()

with open(orig_clustering_fp, 'r') as f:
    reader = csv.reader(f, delimiter='\t')
    for node_id, cluster_id in reader:
        if node_id not in node_id2iid:
            node_id2iid[node_id] = len(node_id2iid)
            node_iid2id[node_id2iid[node_id]] = node_id
        node_iid = node_id2iid[node_id]

        if cluster_id not in cluster_id2iid:
            cluster_id2iid[cluster_id] = len(cluster_id2iid)
            cluster_iid2id[cluster_id2iid[cluster_id]] = cluster_id
        cluster_iid = cluster_id2iid[cluster_id]

        orig_nodeiid_clusteriid[node_iid] = cluster_iid
        orig_clusteriid_nodeiids.setdefault(cluster_iid, set()).add(node_iid)

clustered_node2cluster = copy.deepcopy(orig_nodeiid_clusteriid)

outliers = set()
orig_neighbor = dict()

with open(orig_edgelist_fp, 'r') as f:
    reader = csv.reader(f, delimiter='\t')
    for src_id, tgt_id in reader:
        if src_id not in node_id2iid:
            node_iid = len(node_id2iid)
            node_id2iid[src_id] = node_iid
            node_iid2id[node_iid] = src_id
            outliers.add(node_iid)

        if tgt_id not in node_id2iid:
            node_iid = len(node_id2iid)
            node_id2iid[tgt_id] = node_iid
            node_iid2id[node_iid] = tgt_id
            outliers.add(node_iid)

        src_iid = node_id2iid[src_id]
        tgt_iid = node_id2iid[tgt_id]

        orig_neighbor.setdefault(src_iid, set()).add(tgt_iid)
        orig_neighbor.setdefault(tgt_iid, set()).add(src_iid)

# Add outliers, each its own cluster
for outlier_iid in outliers:
    cluster_iid = len(cluster_id2iid)
    cluster_id = cluster_iid
    cluster_id2iid[cluster_id] = cluster_iid
    cluster_iid2id[cluster_iid] = cluster_id

    orig_clusteriid_nodeiids.setdefault(
        cluster_iid, set()).add(outlier_iid)
    orig_nodeiid_clusteriid[outlier_iid] = cluster_iid

# Generate with SBM
num_clusters = len(orig_clusteriid_nodeiids)
probs = dok_matrix((num_clusters, num_clusters), dtype=int)
for node_iid, neighbors in orig_neighbor.items():
    cluster_iid = orig_nodeiid_clusteriid[node_iid]
    for neighbor_iid in neighbors:
        if node_iid in outliers or neighbor_iid in outliers:
            tgt_cluster_iid = orig_nodeiid_clusteriid[neighbor_iid]
            probs[cluster_iid, tgt_cluster_iid] += 1
probs = probs.tocsr()

num_nodes = len(node_iid2id)
out_degs = np.zeros(num_nodes, dtype=int)
for node_iid, neighbors in orig_neighbor.items():
    if node_iid in outliers:
        out_degs[node_iid] += len(neighbors)
    else:
        for neighbor_iid in neighbors:
            if neighbor_iid in outliers:
                out_degs[node_iid] += 1

b = np.empty(num_nodes, dtype=int)
for node_iid in range(num_nodes):
    b[node_iid] = orig_nodeiid_clusteriid[node_iid]

elapsed = time.perf_counter() - start
print(f"Setup: {elapsed}")
logs.append(f"Setup: {elapsed}")

# ========================

# print(node_id2iid)
# print(cluster_id2iid)

# print(b)
# print(probs.toarray())
# print(out_degs)

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
# gt.remove_parallel_edges(g)
# gt.remove_self_loops(g)

elapsed = time.perf_counter() - start
print(f"Generation of outlier subgraph: {elapsed}")
logs.append(f"Generation of outlier subgraph: {elapsed}")

# ========================

start = time.perf_counter()

# with open(f'{output_dir}/{OUTLIER_COM}', 'w') as f:
#     df = pd.DataFrame([
#         (node_iid2id[node_iid], cluster_iid2id[cluster_iid])
#         for node_iid, cluster_iid in clustered_node2cluster.items()
#     ],
#         columns=['node_id', 'cluster_id'],
#     )
#     df.to_csv(f, sep='\t', index=False, header=False)

with open(f'{output_dir}/{OUTLIER_EDGE}', 'w') as f:
    df = pd.DataFrame([
        (node_iid2id[src], node_iid2id[tgt])
        for src, tgt in g.iter_edges()
    ],
        columns=['src_id', 'tgt_id'],
    )
    df.to_csv(f, sep='\t', index=False, header=False)

elapsed = time.perf_counter() - start
print(f"Post-process: {elapsed}")
logs.append(f"Post-process: {elapsed}")

# ========================

assert os.path.exists(output_dir)
log_f = open(f'{output_dir}/outlier_run.log', 'w')
for log in logs:
    log_f.write(log)
    log_f.write('\n')
log_f.close()
