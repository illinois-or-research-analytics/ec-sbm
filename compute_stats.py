import os
import sys
from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from constants import *

network_id = sys.argv[1]
resolution = sys.argv[2]
method = sys.argv[3]
based_on = sys.argv[4]

print(
    f'Statisctics for {network_id} at resolution {resolution} using {method}')

_dir = f'data/networks/{method}/{based_on}/{network_id}/leiden{resolution}/'

edge = EDGE if 'abcd' in method else 'network.dat'
com = COM_OUT if 'abcd' in method else 'community.dat'
os.system(
    f'python cluster-statistics/stats.py -i {_dir}/{edge} -e {_dir}/{com} -o {_dir}/stats.csv')

stats = pd.read_csv(f'{_dir}/stats.csv')
c = Counter(stats['connectivity'].tolist())
plt.bar(c.keys(), c.values())

EPS = 1e-8
bins = np.arange(
    0, max(stats['connectivity_normalized_log10(n)']) + EPS, 0.1) + EPS
bins[0] -= EPS

fig, ax = plt.subplots(1, 1, figsize=(8, 8), dpi=300)
ax.hist(stats['connectivity_normalized_log10(n)'].tolist(), bins=bins)
# ax[1].hist(lfr_stats['connectivity_normalized_log2(n)'].tolist())
# ax[2].hist(lfr_stats['connectivity_normalized_sqrt(n)/5'].tolist())
ax.set_xlabel('mincut / log10(n)')
ax.set_ylabel('count')
ax.axvline(1.0, color='red')
fig.tight_layout()
fig.savefig(f'{_dir}/norm_connectivity_hist.pdf')

with open(f'{_dir}/connectivity.log', 'w') as f:
    wellconnected = len(
        [x for x in stats['connectivity_normalized_log10(n)'].tolist() if x > 1.0])
    f.write(
        f'Well connected: {wellconnected} / {len(stats)} = {wellconnected / (len(stats))}\n')

    disconnected = len(
        [x for x in stats['connectivity_normalized_log10(n)'].tolist() if x < EPS])
    f.write(
        f'Disconnected: {disconnected} / {len(stats)} = {disconnected / (len(stats))}\n')

os.system(
    f'python cluster-statistics/summarize.py {_dir}/stats.csv {_dir}/{edge}.dat')
