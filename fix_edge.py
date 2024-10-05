from pathlib import Path
import argparse
import csv
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
    parser.add_argument('--exist-edgelist', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    return parser.parse_args()


args = parse_args()

orig_edgelist_fp = Path(args.orig_edgelist)
orig_clustering_fp = Path(args.orig_clustering)
exist_edgelist_fp = Path(args.exist_edgelist)
output_dir = Path(args.output_folder)

logs = []

print(f'Fixing degree sequence')
print(f'Network: {orig_edgelist_fp}')
print(f'Clustering: {orig_clustering_fp}')
print(f'Existing network: {exist_edgelist_fp}')
print(f'Output folder: {output_dir}')

logs.append(f'Fixing degree sequence')
logs.append(f'Network: {orig_edgelist_fp}')
logs.append(f'Clustering: {orig_clustering_fp}')
logs.append(f'Existing network: {exist_edgelist_fp}')
logs.append(f'Output folder: {output_dir}')
logs.append('')

print('== Output == ')

output_dir.mkdir(parents=True, exist_ok=True)

start = time.perf_counter()

# Bijective mapping of node ID to node integer ID (two-way)
node_id2iid = dict()
node_iid2id = dict()

# Bijective mapping of cluster ID to cluster integer ID (two-way)
cluster_id2iid = dict()
cluster_iid2id = dict()

# Mapping of vertex to its cluster
orig_nodeiid_clusteriid = dict()
# Mapping of cluster to its vertices
orig_clusteriid_nodeiids = dict()

# Read the original clustering
with open(orig_clustering_fp, 'r') as f:
    reader = csv.reader(f, delimiter='\t')

    for node_id, cluster_id in reader:
        # Add new node
        assert node_id not in node_id2iid
        node_iid = len(node_id2iid)
        node_id2iid[node_id] = node_iid
        node_iid2id[node_iid] = node_id

        # If not exist, create new cluster
        if cluster_id not in cluster_id2iid:
            cluster_iid = len(cluster_id2iid)
            cluster_id2iid[cluster_id] = cluster_iid
            cluster_iid2id[cluster_iid] = cluster_id
        else:
            cluster_iid = cluster_id2iid[cluster_id]

        # Assign node to cluster
        orig_nodeiid_clusteriid[node_iid] = cluster_iid
        orig_clusteriid_nodeiids.setdefault(cluster_iid, set()).add(node_iid)

elapsed = time.perf_counter() - start
print(f"Process original clustering: {elapsed}")
logs.append(f"Process original clustering: {elapsed}")

# ========================

start = time.perf_counter()

# Mapping of node to its neighbors in the original network
orig_neighbor = dict()

# Set of outlier nodes
outliers = set()

# Read the original edgelist
with open(orig_edgelist_fp, 'r') as f:
    reader = csv.reader(f, delimiter='\t')

    for src_id, tgt_id in reader:
        if src_id not in node_id2iid:
            # If not exist, create new node
            src_iid = len(node_id2iid)
            node_id2iid[src_id] = src_iid
            node_iid2id[src_iid] = src_id

            # Add to outlier
            outliers.add(src_iid)
        else:
            # If exist, get the integer ID
            src_iid = node_id2iid[src_id]

        if tgt_id not in node_id2iid:
            # If not exist, create new node
            tgt_iid = len(node_id2iid)
            node_id2iid[tgt_id] = tgt_iid
            node_iid2id[tgt_iid] = tgt_id

            # Add to outlier
            outliers.add(tgt_iid)
        else:
            # If exist, get the integer ID
            tgt_iid = node_id2iid[tgt_id]

        # Add to neighbor
        orig_neighbor.setdefault(src_iid, set()).add(tgt_iid)
        orig_neighbor.setdefault(tgt_iid, set()).add(src_iid)

elapsed = time.perf_counter() - start
print(f"Process original edgelist: {elapsed}")
logs.append(f"Process original edgelist: {elapsed}")

# ========================

start = time.perf_counter()

# Create outlier clusters
# Each outlier is a cluster
for outlier_iid in outliers:
    cluster_iid = len(cluster_id2iid)
    cluster_id = cluster_iid
    cluster_id2iid[cluster_id] = cluster_iid
    cluster_iid2id[cluster_iid] = cluster_id

    orig_clusteriid_nodeiids.setdefault(
        cluster_iid, set()).add(outlier_iid)
    orig_nodeiid_clusteriid[outlier_iid] = cluster_iid

elapsed = time.perf_counter() - start
print(f"Create outlier clusters: {elapsed}")
logs.append(f"Create outlier clusters: {elapsed}")

# ========================

start = time.perf_counter()

# Compute SBM parameters from the original network

# print(node_id2iid)
# print(cluster_id2iid)
# print(orig_nodeiid_clusteriid)
# print(orig_clusteriid_nodeiids)
# print(orig_neighbor)
# print(outliers)

# Number of clusters
num_clusters = len(orig_clusteriid_nodeiids)

# Number of nodes
num_nodes = len(node_iid2id)

# Edge count matrix
probs = dok_matrix((num_clusters, num_clusters), dtype=int)
for node_iid, neighbors in orig_neighbor.items():
    cluster_iid = orig_nodeiid_clusteriid[node_iid]
    for neighbor_iid in neighbors:
        tgt_cluster_iid = orig_nodeiid_clusteriid[neighbor_iid]
        probs[cluster_iid, tgt_cluster_iid] += 1
# probs = probs.tocsr()

# Degree sequence
out_degs = np.zeros(num_nodes, dtype=int)
for node_iid, neighbors in orig_neighbor.items():
    out_degs[node_iid] += len(neighbors)

# Cluster assignment
b = np.empty(num_nodes, dtype=int)
for node_iid in range(num_nodes):
    b[node_iid] = orig_nodeiid_clusteriid[node_iid]

# print(b)
# print(probs.toarray())
# print(out_degs)

elapsed = time.perf_counter() - start
print(f"Compute SBM parameters from original: {elapsed}")
logs.append(f"Compute SBM parameters from original: {elapsed}")

# ========================

start = time.perf_counter()

# Update the parameters with the existing network

deg_copy = out_degs.copy()

# Read the existing edgelist
with open(exist_edgelist_fp, 'r') as f:
    reader = csv.reader(f, delimiter='\t')

    # Update the parameters
    for src_id, tgt_id in reader:
        # Ensure the nodes exist
        assert src_id in node_id2iid
        assert tgt_id in node_id2iid

        # Get the integer ID
        src_iid = node_id2iid[src_id]
        tgt_iid = node_id2iid[tgt_id]

        src_cluster_iid = orig_nodeiid_clusteriid[src_iid]
        tgt_cluster_iid = orig_nodeiid_clusteriid[tgt_iid]

        # Update the parameters
        # out_degs[src_iid] -= 1
        # out_degs[tgt_iid] -= 1
        # probs[src_cluster_iid, tgt_cluster_iid] -= 1
        # probs[tgt_cluster_iid, src_cluster_iid] -= 1

        out_degs[src_iid] = max(0, out_degs[src_iid] - 1)
        out_degs[tgt_iid] = max(0, out_degs[tgt_iid] - 1)
        probs[src_cluster_iid, tgt_cluster_iid] = max(
            0, probs[src_cluster_iid, tgt_cluster_iid] - 1)
        probs[tgt_cluster_iid, src_cluster_iid] = max(
            0, probs[tgt_cluster_iid, src_cluster_iid] - 1)
probs = probs.tocsr()

# print(b)
# print(probs.toarray())
# print(out_degs)

elapsed = time.perf_counter() - start
print(f"Update SBM parameters with existing: {elapsed}")
logs.append(f"Update SBM parameters with existing: {elapsed}")

# ========================

start = time.perf_counter()

for i in range(num_clusters - len(outliers)):
    deg_i = out_degs[b == i].sum()
    num_edges_from_i = probs[i, :].sum()

    if deg_i < num_edges_from_i:
        print(f'Cluster {i}: sum of degrees {deg_i}, #edges {num_edges_from_i}')
        logs.append(f'Cluster {i}: sum of degrees {deg_i}, #edges {num_edges_from_i}')

        add_deg = num_edges_from_i - deg_i
        # Randomly choose from b == i
        candidates = np.where(b == i)[0]
        weights = deg_copy[candidates] / deg_copy[candidates].sum()
        v = np.random.choice(candidates, p=weights, size=add_deg)
        for vv in v:
            out_degs[vv] += 1

elapsed = time.perf_counter() - start
print(f"Ensure consistency of SBM parameters: {elapsed}")
logs.append(f"Ensure consistency of SBM parameters: {elapsed}")

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
gt.remove_parallel_edges(g)
gt.remove_self_loops(g)

elapsed = time.perf_counter() - start
print(f"Generation of subgraph: {elapsed}")
logs.append(f"Generation of subgraph: {elapsed}")

# ========================

start = time.perf_counter()

with open(f'{output_dir}/fix_edge.tsv', 'w') as f:
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
log_f = open(f'{output_dir}/fixedge_run.log', 'w')
for log in logs:
    log_f.write(log)
    log_f.write('\n')
log_f.close()
