import os
import argparse
from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from src.constants import *

EPS = 1e-8


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--network-folder', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    return parser.parse_args()


print('Evaluation')
print('== Input == ')

args = parse_args()
network_dir = args.network_folder
output_dir = args.output_folder

print(f'Network/Clustering: {network_dir}')
print(f'Output: {output_dir}')

print('== Output == ')

assert os.path.exists(network_dir)
os.makedirs(output_dir, exist_ok=True)

assert os.path.exists(f'{network_dir}/cluster_stats.csv'), \
    'cluster_stats.csv not found. Please run network_evaluation/compute_stats.py first.'
stats = pd.read_csv(f'{network_dir}/cluster_stats.csv')
stats.drop(stats.tail(1).index, inplace=True)

c = Counter(stats['connectivity'].tolist())
plt.bar(c.keys(), c.values())

bins = EPS + np.arange(
    0,
    max(stats['connectivity_normalized_log10(n)']) + EPS,
    0.2
)
bins[0] -= EPS

fig, ax = plt.subplots(1, 1, figsize=(8, 8), dpi=300)
ax.hist(stats['connectivity_normalized_log10(n)'].tolist(), bins=bins)
# ax[1].hist(lfr_stats['connectivity_normalized_log2(n)'].tolist())
# ax[2].hist(lfr_stats['connectivity_normalized_sqrt(n)/5'].tolist())
ax.set_xlabel('mincut / log10(n)')
ax.set_ylabel('count')
ax.axvline(1.0, color='red')
fig.tight_layout()
fig.savefig(f'{network_dir}/norm_connectivity_hist.pdf')

num_clusters = len(stats)

wc_count = stats[stats['connectivity_normalized_log10(n)'] > 1.0].shape[0]
wc_ratio = wc_count / num_clusters

dc_count = stats[stats['connectivity_normalized_log10(n)'] < EPS].shape[0]
dc_perc = dc_count / num_clusters * 100

with open(f'{network_dir}/connectivity.log', 'w') as f:
    f.write(f'n_clusters, {num_clusters}\n')
    f.write(f'well_connected, {wc_count}\n')
    f.write(f'well_connected_ratio, {wc_ratio}\n')
    f.write(f'disconnected, {dc_count}\n')
    f.write(f'disconnected_percentage, {dc_perc}\n')
