from pathlib import Path
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description='Process network files.')
parser.add_argument('--clustering', type=str,
                    required=True, help='Clustering method')
parser.add_argument('--resolution', type=str, required=True, help='Resolution')
parser.add_argument('--network_id', type=str, required=True, help='Network ID')

args = parser.parse_args()

network_dir = Path(
    f'data/networks/abcd+o/{args.clustering}/{args.network_id}/{args.resolution}/0/')

network_fp = network_dir / 'edge.tsv'
comm_fp = network_dir / 'com.tsv'

# Check if backup exists
if network_fp.with_suffix('.bak.tsv').exists():
    print('Backup exists. Exiting...')
    exit(1)

# Check if network file exists
if not network_fp.exists():
    print(f'Network file {network_fp} does not exist')
    exit(1)

# Load data (no header)
# Each row is an edge between two nodes
# Columns: node1, node2
edges = pd.read_csv(network_fp, sep='\t', header=None)

# Outliers are nodes that are not in any community
# Load data (no header)
# Each row is a node and its community
# Columns: node, community
comm = pd.read_csv(comm_fp, sep='\t', header=None)

# Get nodes that are not in any community
outliers = set(edges[0].unique()).difference(comm[0].unique())
outliers.update(set(edges[1].unique()).difference(comm[0].unique()))

# Number of outliers
n_outliers = len(outliers)

# Save backup of network
edges.to_csv(network_fp.with_suffix('.bak.tsv'),
             sep='\t', header=False, index=False)

# Number of edges
n_edges = edges.shape[0]

# Remove rows with same values on both columns
edges = edges[edges[0] != edges[1]]

# Number of edges after removing self-edges
n_edges_no_self = edges.shape[0]

# Number of self-edges
n_self_edges = n_edges - n_edges_no_self

# Check if number of self edges is equal to the number of nodes when there are outliers
n_nodes = len(set(edges[0].unique()).union(edges[1].unique()))
if n_outliers > 0:
    assert n_self_edges == n_nodes
else:
    assert n_self_edges == 0

# Save fixed network
edges.to_csv(network_fp, sep='\t', header=False, index=False)
