import sys
import pandas as pd
import json
import matplotlib.pyplot as plt
import numpy as np

network_id = sys.argv[1]
resolution = sys.argv[2]
method = sys.argv[3]
based_on = sys.argv[4]

print(
    f'Statisctics for {network_id} at resolution {resolution} using {method}')

_dir = f'data/networks/{method}/{based_on}/{network_id}/leiden{resolution}/'

df = pd.read_csv(f'{_dir}/stats.csv')
# df.drop(df.tail(1).index, inplace=True)
# df.drop(df.where(df['mindeg'] == 0).index, inplace=True)

# ===============================

mincut_over_mindeg = (df['connectivity'] / df['mindeg']).tolist()
mincut_over_mindeg = [
    x for x in mincut_over_mindeg if x not in [float('nan'), float('inf')]
]

EPS = 1e-8
bins = np.arange(0, 1.1, 0.1) + EPS
bins[0] -= EPS

fig, ax = plt.subplots(1, 1, figsize=(8, 8), dpi=300)
ax.hist(mincut_over_mindeg, bins=bins)
ax.set_xlabel('mincut / min inner deg')
ax.set_ylabel('count')
fig.tight_layout()
fig.savefig(f'{_dir}/wiring_efficiency_hist.pdf')

# =============================================

mindegs = df['mindeg'].tolist()
mincuts = df['connectivity'].tolist()

fig, ax = plt.subplots(1, 1, figsize=(5, 5), dpi=300)
ax.scatter(mindegs, mincuts)
ax.set_xlabel('min inner deg')
ax.set_ylabel('mincut')
m = min(min(mindegs), min(mincuts)) - 0.25
M = max(max(mindegs), max(mincuts)) + 0.25
ax.set_xlim(m, M)
ax.set_ylim(m, M)
ax.set_aspect('equal')
# ax.plot([0, 1], [0, 1], transform=ax.transAxes, color='red')
fig.tight_layout()
fig.savefig(f'{_dir}/wiring_efficiency_scatter.png')

# ==

with open(f'{_dir}/wiring_efficiency.log', 'w') as f:
    efficient = len(
        [x for x in mincut_over_mindeg if 1.0 - x < EPS])
    f.write(
        f'Most efficient: {efficient} / {len(mincut_over_mindeg)} = {efficient / (len(mincut_over_mindeg))}\n')

    inefficient = len(
        [x for x in mincut_over_mindeg if x < EPS])
    f.write(
        f'Inefficient: {inefficient} / {len(mincut_over_mindeg)} = {inefficient / (len(mincut_over_mindeg))}\n')
