import os
import sys
from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

network_id = sys.argv[1]
resolution = sys.argv[2]
method = sys.argv[3]

print(
    f'Statisctics for {network_id} at resolution {resolution} using {method}')

_dir = f'data/networks/{network_id}_{method}_networks/{network_id}_leiden{resolution}_{method}'

edge = 'edge' if method in ['abcd', 'abcds'] else 'network'
com = 'com' if method in ['abcd', 'abcds'] else 'community'
os.system(
    f'python cluster-statistics/stats.py -i {_dir}/{edge}.dat -e {_dir}/{com}.dat -o {_dir}/stats.csv')

stats = pd.read_csv(f'{_dir}/stats.csv')
c = Counter(stats['connectivity'].tolist())
plt.bar(c.keys(), c.values())

EPS = 1e-8
bins = np.arange(0, max(stats['connectivity']) + EPS, 0.1) + EPS
bins[0] -= EPS
print(bins)

fig, ax = plt.subplots(1, 1, figsize=(8, 8), dpi=300)
ax.hist(stats['connectivity_normalized_log10(n)'].tolist(), bins=bins)
# ax[1].hist(lfr_stats['connectivity_normalized_log2(n)'].tolist())
# ax[2].hist(lfr_stats['connectivity_normalized_sqrt(n)/5'].tolist())
ax.set_xlabel('mincut / log10(n)')
ax.set_ylabel('count')
ax.axvline(1.0, color='red')
fig.tight_layout()
fig.savefig(f'{_dir}/norm_connectivity_hist.pdf')

wellconnected = len(
    [x for x in stats['connectivity_normalized_log10(n)'].tolist() if x > 1.0])
print(
    f'Well connected: {wellconnected} / {len(stats) - 1} = {wellconnected / (len(stats) - 1)}')

disconnected = len(
    [x for x in stats['connectivity_normalized_log10(n)'].tolist() if x < EPS])
print(
    f'Well connected: {disconnected} / {len(stats) - 1} = {disconnected / (len(stats) - 1)}')

os.system(
    f'python cluster-statistics/summarize.py {_dir}/stats.csv {_dir}/{edge}.dat')

lfr_summary = pd.read_csv(f'{_dir}/stats_summary.csv', header=None)
for row in lfr_summary.iterrows():
    k, v = row[1].values
    print(f'{k} \t\t\t {v}')
