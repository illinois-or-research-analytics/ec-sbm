import csv
import time
from pathlib import Path
import argparse

import pandas as pd
import numpy as np
import graph_tool.all as gt
from scipy.sparse import dok_matrix

COLORS = [
    "#1c71d8",
    "#2ec27e",
    "#f7a325",
    "#f04844",
    "#8a2be2",
    "#ff4500",
    "#00bfff",
    "#ff1493",
    "#00ff00",
    "#ff0000",
    "#0000ff",
    "#ff00ff",
    "#00ffff",
    "#ffff00",
    "#000000",
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--edgelist',
        type=Path,
        required=True,
        help='Path to the edge list file',
    )
    parser.add_argument(
        '--clustering',
        type=Path,
        required=True,
        help='Path to the clustering file',
    )
    parser.add_argument(
        '--output-folder',
        type=Path,
        required=True,
        help='Path to the output folder',
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=0,
        help='Random seed',
    )
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Visualize the generated SBM',
    )
    return parser.parse_args()


args = parse_args()
edgelist_fp = args.edgelist
clustering_fp = args.clustering
output_folder = args.output_folder
seed = args.seed
visualize = args.visualize

assert edgelist_fp.exists(), f'{edgelist_fp} does not exist'
assert clustering_fp.exists(), f'{clustering_fp} does not exist'
output_folder.mkdir(parents=True, exist_ok=True)

# Compute node and cluster mappings
node_id2iid = dict()
cluster_id2iid = dict()
clustering = dict()
with open(clustering_fp, 'r') as f:
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
with open(edgelist_fp, 'r') as f:
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

# Generate SBM
np.random.seed(seed)
start = time.perf_counter()
g = gt.generate_sbm(
    b,
    probs,
    out_degs=out_degs,
    micro_ers=True,
    micro_degs=True,
    directed=False,
)
gt.remove_parallel_edges(g)
gt.remove_self_loops(g)
print(f'Elapsed time: {time.perf_counter() - start:.3f} sec')

# Copy clustering file
with open(output_folder / 'com.tsv', 'w') as f:
    df = pd.DataFrame([
        (node_iid2id[node_iid], cluster_iid2id[cluster_iid])
        for node_iid, cluster_iid in node2cluster.items()
    ],
        columns=['node_id', 'cluster_id'],
    )
    df.to_csv(f, sep='\t', index=False, header=False)

# Save edge list
with open(output_folder / 'edge.tsv', 'w') as f:
    df = pd.DataFrame([
        (node_iid2id[src], node_iid2id[tgt])
        for src, tgt in g.iter_edges()
    ],
        columns=['src_id', 'tgt_id'],
    )
    df.to_csv(f, sep='\t', index=False, header=False)

if visualize:
    # Draw graph
    vcolor = g.new_vp("string")
    for v in g.vertices():
        vcolor[v] = COLORS[node2cluster[v]]

    vid = g.new_vp('string')
    for v in g.vertices():
        vid[v] = node_iid2id[v]

    gt.graph_draw(
        g,
        output=str(output_folder / 'sbm.png'),
        bg_color='white',
        vertex_text=vid,
        vertex_fill_color=vcolor,
    )
