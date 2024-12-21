from pathlib import Path
import json

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import pandas as pd

plt.rcParams.update({'font.size': 15})

name = 'sbm+o'
root = Path(f'data/stats/{name}/leiden_cpm')
resolution = 'leiden.001'

data_dict = []
for fp in root.iterdir():
    if not fp.is_dir():
        continue

    network_id = fp.name
    net_res_fp = fp / resolution
    if not net_res_fp.exists():
        continue

    for rep_fp in net_res_fp.iterdir():
        if not rep_fp.is_dir():
            continue

        rep_id = rep_fp.name

        stats_fp = rep_fp / 'stats.json'

        if not stats_fp.exists():
            continue

        stats = json.loads(stats_fp.read_text())
        stats['network_id'] = network_id
        stats['rep_id'] = rep_id
        data_dict.append(stats)
df_raw = pd.DataFrame(data_dict)

df = df_raw.groupby(['network_id', 'n_clusters'])['n_disconnects'].max()
df = df.reset_index()
df.sort_values('n_clusters', inplace=True)
print(df)

flatui = ["#9b59b6", "#3498db", "#95a5a6", "#e74c3c", "#34495e", "#2ecc71"]
my_cmap = ListedColormap(sns.color_palette(flatui).as_hex())

fig, ax = plt.subplots(1, 1, figsize=(10, 6), dpi=300)
ax.stackplot(
    df['network_id'],
    df['n_disconnects'],
    df['n_clusters'] - df['n_disconnects'],
    labels=['Disconnected clusters', 'Connected clusters'],
    colors=flatui,
)
ax.legend(loc='upper left')
ax.set_yscale('log')
ax.set_ylabel('Number of clusters')
ax.set_xlabel('Networks')
ax.set_xticks([])
ax.set_xlim(0, len(df) - 1)
plt.grid()
plt.tight_layout()
plt.savefig(f'{name}_disconnected_clusters.pdf')

df = df_raw.groupby(['network_id', 'n_clusters'])[
    'n_wellconnected_clusters'].min()
df = df.reset_index()
df.sort_values('n_clusters', inplace=True)
print(df)

flatui = ["#9b59b6", "#3498db", "#95a5a6", "#e74c3c", "#34495e", "#2ecc71"]
my_cmap = ListedColormap(sns.color_palette(flatui).as_hex())

fig, ax = plt.subplots(1, 1, figsize=(10, 6), dpi=300)
ax.stackplot(
    df['network_id'],
    df['n_wellconnected_clusters'],
    df['n_clusters'] - df['n_wellconnected_clusters'],
    labels=['Not well-connected clusters', 'Well-connected clusters'],
    colors=flatui,
)
ax.legend(loc='upper left')
ax.set_yscale('log')
ax.set_ylabel('Number of clusters')
ax.set_xlabel('Networks')
ax.set_xticks([])
ax.set_xlim(0, len(df) - 1)
plt.grid()
plt.tight_layout()
plt.savefig(f'{name}_wellconnected_clusters_{resolution}.pdf')
