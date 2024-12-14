from pathlib import Path
import json
import argparse

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

parser = argparse.ArgumentParser(description='Plot excess edges for networks.')
parser.add_argument('--root', type=str, required=True,
                    help='Root directory for data')
parser.add_argument('--clustering', type=str,
                    required=True, help='Clustering method')
parser.add_argument('--resolution', type=str, required=True, help='Resolution')
parser.add_argument('--networks_list', type=str,
                    default='data/networks_val.txt', help='File with list of network IDs')
parser.add_argument('--output', type=str, required=True,
                    help='Output folder for edge composition plot')
args = parser.parse_args()

root = Path(args.root)
clustering = args.clustering
resolution = args.resolution
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

for network_id in network_ids:
    network_dir = root / clustering / network_id / resolution / '0'
    if not network_dir.exists():
        print(f'No directory for {network_id}')
        continue

    excess_edges_file = network_dir / 'excess_edges.json'
    if not excess_edges_file.exists():
        print(f'Not found {excess_edges_file}')
        continue

    excess_edges = json.load(excess_edges_file.open())

    n_edges = excess_edges['n_edges']
    n_parallel_edges = excess_edges['n_parallel_edges'] / n_edges
    n_self_loops = excess_edges['n_self_loops'] / n_edges

    normal_edges = 1.0 - n_parallel_edges - n_self_loops

    network_data.append(
        (network_id, normal_edges, n_parallel_edges, n_self_loops, n_edges))

# Sort by number of edges
network_data.sort(key=lambda x: x[0])

for data in network_data:
    network_id, normal_edges, n_parallel_edges, n_self_loops, n_edges = data
    all_normal_edges.append(normal_edges)
    all_parallel_edges.append(n_parallel_edges)
    all_self_loops.append(n_self_loops)
    available_networks.append(network_id)
all_normal_edges = np.array(all_normal_edges)
all_parallel_edges = np.array(all_parallel_edges)
all_self_loops = np.array(all_self_loops)

output_fp.parent.mkdir(parents=True, exist_ok=True)

# Plot area chart
plt.figure(figsize=(10, 6), dpi=200, tight_layout=True)
sns.set_theme(style="whitegrid")
plt.stackplot(
    range(len(available_networks)),
    all_parallel_edges,
    all_self_loops,
    all_normal_edges,
    labels=['Parallel Edges', 'Self Loops', 'Normal Edges'],
    colors=sns.color_palette("Set2", 3))
plt.title('Edge Composition for All Networks')
plt.xlabel('Network')
plt.ylabel('Fraction of Edges')
plt.xticks(range(len(available_networks)), available_networks, rotation=90)
plt.xlim(0, len(available_networks) - 1)
plt.ylim(0, 1)
plt.legend(loc='upper right')
plt.savefig(output_fp / 'edge_composition.pdf')

# Plot histogram of fraction of parallel edges
plt.figure(figsize=(10, 6), dpi=200, tight_layout=True)
sns.histplot(all_parallel_edges, kde=True, stat='probability')
plt.title('Histogram of Fraction of Parallel Edges')
plt.xlabel('Fraction of Parallel Edges')
plt.ylabel('Frequency')
plt.xlim(0, 1)
plt.savefig(output_fp / 'hist_parallel_edges.pdf')

# Plot histogram of fraction of self loops
plt.figure(figsize=(10, 6), dpi=200, tight_layout=True)
sns.histplot(all_self_loops, kde=True, stat='probability')
plt.title('Histogram of Fraction of Self Loops')
plt.xlabel('Fraction of Self Loops')
plt.ylabel('Frequency')
plt.xlim(0, 1)
plt.savefig(output_fp / 'hist_self_loops.pdf')

# Plot histogram of fraction of parallel edges + self loops
plt.figure(figsize=(10, 6), dpi=200, tight_layout=True)
sns.histplot(all_parallel_edges + all_self_loops, kde=True, stat='probability')
plt.title('Histogram of Fraction of Parallel Edges + Self Loops')
plt.xlabel('Fraction of Parallel Edges + Self Loops')
plt.ylabel('Frequency')
plt.xlim(0, 1)
plt.savefig(output_fp / 'hist_parallel_self_loops.pdf')
