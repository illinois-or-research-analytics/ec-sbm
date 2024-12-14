from pathlib import Path
import json
import argparse

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

CLUSTERING_RESOLUTION = [
    ('ikc_cc', 'k10'),
    ('ikc_nofiltcm', 'k10'),
    ('infomap_cc', 'infomap'),
    ('infomap_nofiltcm', 'infomap'),
    ('leiden_cpm', 'leiden.1'),
    ('leiden_cpm', 'leiden.01'),
    ('leiden_cpm', 'leiden.001'),
    ('leiden_cpm_nofiltcm', 'leiden.1'),
    ('leiden_cpm_nofiltcm', 'leiden.01'),
    ('leiden_cpm_nofiltcm', 'leiden.001'),
    ('leiden_mod', 'leidenmod'),
    ('leiden_mod_nofiltcm', 'leidenmod'),
    ('sbm', 'sbm'),
    ('sbm_cc', 'sbm'),
    ('sbm_wcc', 'sbm'),
]

parser = argparse.ArgumentParser(description='Plot excess edges for networks.')
parser.add_argument('--root', type=str, required=True,
                    help='Root directory for data')
parser.add_argument('--networks_list', type=str,
                    default='data/networks_val.txt', help='File with list of network IDs')
parser.add_argument('--output', type=str, required=True,
                    help='Output folder')
args = parser.parse_args()

root = Path(args.root)
networks_list = args.networks_list
output_fp = Path(args.output)

network_ids = [
    line.strip() for line in open(networks_list)
]

all_normal_edges = []
all_parallel_edges = []
all_self_loops = []
available_networks = []

network_data = []

for clustering, resolution in CLUSTERING_RESOLUTION:
    for network_id in network_ids:
        network_dir = root / clustering / network_id / resolution / '0'
        if not network_dir.exists():
            print(f'No directory for {network_id} with clustering {
                  clustering} and resolution {resolution}')
            continue

        excess_edges_file = network_dir / 'excess_edges.json'
        if not excess_edges_file.exists():
            print(f'Not found {excess_edges_file} for {network_id} with clustering {
                  clustering} and resolution {resolution}')
            continue

        excess_edges = json.load(excess_edges_file.open())

        n_edges = excess_edges['n_edges']
        n_parallel_edges = excess_edges['n_parallel_edges'] / n_edges
        n_self_loops = excess_edges['n_self_loops'] / n_edges

        normal_edges = 1.0 - n_parallel_edges - n_self_loops

        network_data.append(
            (network_id, clustering, resolution, normal_edges, n_parallel_edges, n_self_loops, n_edges))

df = pd.DataFrame(network_data, columns=[
    'network_id', 'clustering', 'resolution', 'normal_edges', 'parallel_edges', 'self_loops', 'n_edges'])

# Create a new column combining clustering and resolution for easier plotting
df['clustering_resolution'] = df['clustering'] + '_' + df['resolution']

# Set up the matplotlib figure for normal edges
plt.figure(figsize=(15, 10))
sns.boxplot(x='clustering_resolution',
            y='normal_edges', data=df, palette="Set3")
plt.xticks(rotation=90)
plt.xlabel('Clustering-Resolution')
plt.ylabel('Proportion of Normal Edges')
plt.title('Box Plot of Normal Edges for Different Clustering-Resolution Pairs')
plt.tight_layout()
plt.savefig(output_fp / 'normal_edges_boxplot.pdf')
plt.close()

# Set up the matplotlib figure for parallel edges
plt.figure(figsize=(15, 10))
sns.boxplot(x='clustering_resolution',
            y='parallel_edges', data=df, palette="Set2")
plt.xticks(rotation=90)
plt.xlabel('Clustering-Resolution')
plt.ylabel('Proportion of Parallel Edges')
plt.title('Box Plot of Parallel Edges for Different Clustering-Resolution Pairs')
plt.tight_layout()
plt.savefig(output_fp / 'parallel_edges_boxplot.pdf')
plt.close()

# Set up the matplotlib figure for self loops
plt.figure(figsize=(15, 10))
sns.boxplot(x='clustering_resolution', y='self_loops', data=df, palette="Set1")
plt.xticks(rotation=90)
plt.xlabel('Clustering-Resolution')
plt.ylabel('Proportion of Self Loops')
plt.title('Box Plot of Self Loops for Different Clustering-Resolution Pairs')
plt.tight_layout()
plt.savefig(output_fp / 'self_loops_boxplot.pdf')
plt.close()

# Set up the matplotlib figure for sum of parallel edges + self loops
df['parallel_self'] = df['parallel_edges'] + df['self_loops']
plt.figure(figsize=(15, 10))
sns.boxplot(x='clustering_resolution',
            y='parallel_self', data=df, palette="Set1")
plt.xticks(rotation=90)
plt.xlabel('Clustering-Resolution')
plt.ylabel('Proportion of Parallel Edges + Self Loops')
plt.title(
    'Box Plot of Parallel Edges + Self Loops for Different Clustering-Resolution Pairs')
plt.tight_layout()
plt.savefig(output_fp / 'parallel_self_boxplot.pdf')
