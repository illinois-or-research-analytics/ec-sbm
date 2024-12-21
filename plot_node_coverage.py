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
    ('leiden_mod', 'leidenmod'),
    ('leiden_cpm_nofiltcm', 'leiden.1'),
    ('leiden_cpm_nofiltcm', 'leiden.01'),
    ('leiden_cpm_nofiltcm', 'leiden.001'),
    ('leiden_mod_nofiltcm', 'leidenmod'),
    ('sbm', 'sbm'),
    ('sbm_cc', 'sbm'),
    ('sbm_wcc', 'sbm'),
]

parser = argparse.ArgumentParser(
    description='Plot node coverage for networks.')
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

node_coverages = []
available_networks = []

for clustering, resolution in CLUSTERING_RESOLUTION:
    for network_id in network_ids:
        network_dir = root / clustering / network_id / resolution
        if not network_dir.exists():
            print(f'No directory for {network_id} with clustering {
                  clustering} and resolution {resolution}')
            continue

        stat_file = network_dir / 'stats.json'
        if not stat_file.exists():
            print(f'Not found {stat_file}')
            continue

        stat_data = json.load(stat_file.open())
        n_nodes = stat_data['n_nodes']
        node_coverage = 1 - stat_data['n_onodes'] / stat_data['n_nodes']

        node_coverages.append(
            (network_id, clustering, resolution, n_nodes, node_coverage)
        )

# Sort by number of nodes
node_coverages.sort(key=lambda x: x[3])

df = pd.DataFrame(
    node_coverages,
    columns=['network_id', 'clustering',
             'resolution', 'n_nodes', 'node_coverage']
)

df['clustering_resolution'] = df['clustering'] + '_' + df['resolution']

sns.set_theme(style='whitegrid')
plt.figure(figsize=(10, 10))
sns.boxplot(
    x='clustering_resolution',
    y='node_coverage',
    data=df,
    palette='Set3',
    linewidth=1.5,
)
plt.xticks(rotation=90)
plt.ylabel('Node coverage')
plt.tight_layout()
plt.savefig(output_fp / 'node_coverage.pdf')
