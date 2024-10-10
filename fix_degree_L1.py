import argparse
import logging
import heapq
import time
import csv
from pathlib import Path

import pandas as pd
import numpy as np
from scipy.sparse import dok_matrix
from graph_tool.all import *


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

# ========================

output_dir.mkdir(parents=True, exist_ok=True)
log_path = output_dir / 'fix_edge.log'
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

logging.info(f'Fixing degree sequence')
logging.info(f'Network: {orig_edgelist_fp}')
logging.info(f'Clustering: {orig_clustering_fp}')
logging.info(f'Existing network: {exist_edgelist_fp}')
logging.info(f'Output folder: {output_dir}')
logging.info('')

# ========================

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
logging.info(f"Process original clustering: {elapsed}")

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
logging.info(f"Process original edgelist: {elapsed}")

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
logging.info(f"Create outlier clusters: {elapsed}")

# ========================

start = time.perf_counter()

# Compute SBM parameters from the original network

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

# Degree sequence
out_degs = np.zeros(num_nodes, dtype=int)
for node_iid, neighbors in orig_neighbor.items():
    out_degs[node_iid] += len(neighbors)

# Cluster assignment
b = np.empty(num_nodes, dtype=int)
for node_iid in range(num_nodes):
    b[node_iid] = orig_nodeiid_clusteriid[node_iid]

elapsed = time.perf_counter() - start
logging.info(f"Compute SBM parameters from original: {elapsed}")

# ========================

start = time.perf_counter()

exist_neighbor = dict()

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

        # Add to the neighbor set
        exist_neighbor.setdefault(src_iid, set())
        exist_neighbor.setdefault(tgt_iid, set())

        # Check for duplicates
        if tgt_iid in exist_neighbor[src_iid]:
            assert src_iid in exist_neighbor[tgt_iid]
            continue
        exist_neighbor[src_iid].add(tgt_iid)
        exist_neighbor[tgt_iid].add(src_iid)

        # Get the cluster integer ID
        src_cluster_iid = orig_nodeiid_clusteriid[src_iid]
        tgt_cluster_iid = orig_nodeiid_clusteriid[tgt_iid]

        # Update the degree
        out_degs[src_iid] = max(0, out_degs[src_iid] - 1)
        out_degs[tgt_iid] = max(0, out_degs[tgt_iid] - 1)

        # Update the edge count matrix
        probs[src_cluster_iid, tgt_cluster_iid] = max(
            0, probs[src_cluster_iid, tgt_cluster_iid] - 1)
        probs[tgt_cluster_iid, src_cluster_iid] = max(
            0, probs[tgt_cluster_iid, src_cluster_iid] - 1)

elapsed = time.perf_counter() - start
logging.info(f"Update SBM parameters with existing: {elapsed}")

# ========================

start = time.perf_counter()

# Find all avaliable nodes
available_node_set = set()
available_node_degrees = dict()
for node_iid, neighbors in exist_neighbor.items():
    degree = out_degs[node_iid]
    if degree > 0:
        available_node_set.add(node_iid)
        available_node_degrees[node_iid] = degree

# Convert available_node_degrees to a max-heap
max_heap = [
    (-degree, node)
    for node, degree in available_node_degrees.items()
]
heapq.heapify(max_heap)

degree_edges = set()
nodes_processed = 0
degree_corrected = 0
while max_heap:
    # Get the node with the highest degree
    _, available_c_node = heapq.heappop(max_heap)

    # Check if the node is still available
    if available_c_node not in available_node_degrees:
        continue

    # Get the neighbors of the node
    neighbors = exist_neighbor.get(available_c_node, set())
    neighbors.add(available_c_node)

    # Get the available non-neighbors
    available_non_neighbors = available_node_set.copy()
    for neighbor in neighbors:
        available_non_neighbors.discard(neighbor)

    # Compute the missing degree
    avail_k = min(
        available_node_degrees[available_c_node],
        len(available_non_neighbors),
    )

    # Add edges to the node to correct the degree
    for i in range(avail_k):
        # Get a node with available degree
        edge_end = available_non_neighbors.pop()

        # Add edge between the nodes
        degree_edges.add((available_c_node, edge_end))

        # Update neighbors
        exist_neighbor[available_c_node].add(edge_end)
        exist_neighbor[edge_end].add(available_c_node)

        # Update the degree of the chosen node
        available_node_degrees[edge_end] -= 1
        if available_node_degrees[edge_end] == 0:
            available_node_set.remove(edge_end)
            del available_node_degrees[edge_end]
        degree_corrected += 1

    del available_node_degrees[available_c_node]
    available_node_set.remove(available_c_node)
    nodes_processed += 1

# ========================

start = time.perf_counter()

with open(f'{output_dir}/fix_edge.tsv', 'w') as f:
    df = pd.DataFrame([
        (node_iid2id[src], node_iid2id[tgt])
        for src, tgt in degree_edges
    ],
        columns=['src_id', 'tgt_id'],
    )
    df.to_csv(f, sep='\t', index=False, header=False)

elapsed = time.perf_counter() - start
logging.info(f"Post-process: {elapsed}")
