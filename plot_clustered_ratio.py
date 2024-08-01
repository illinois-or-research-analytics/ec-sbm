from pathlib import Path
import json

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import pandas as pd

plt.rcParams.update({'font.size': 15})

large_network_ids = [
    'cit_hepph',
    'cit_patents',
    'wiki_talk',
    'wiki_topcats',
    'orkut',
    'cen'
]

clustered_root = Path('data/stats/orig_wo_outliers/leiden_cpm_cm')
orig_root = Path('data/stats/orig/leiden_cpm_cm')
resolution = 'leiden.001'

data_dict = []
for fp in clustered_root.iterdir():
    if not fp.is_dir():
        continue
    
    network_id = fp.name

    stats_fp = fp / resolution / 'stats.json'
    if not stats_fp.exists():
        continue
    stats = json.loads(stats_fp.read_text())
    stats['network_id'] = network_id
    stats['is_special'] = network_id in large_network_ids

    orig_fp = orig_root / network_id / resolution / 'stats.json'
    if not orig_fp.exists():
        continue
    orig_stats = json.loads(orig_fp.read_text())
    stats['orig_n_nodes'] = orig_stats['n_nodes']

    data_dict.append(stats)
df = pd.DataFrame(data_dict)
df['proportion'] = df['n_nodes'] / df['orig_n_nodes']
df.sort_values('proportion', inplace=True)

flatui = ["#9b59b6", "#3498db", "#95a5a6", "#e74c3c", "#34495e", "#2ecc71"]
my_cmap = ListedColormap(sns.color_palette(flatui).as_hex())

fig, ax = plt.subplots(1, 1, figsize=(10, 6), dpi=300)
ax.stackplot(
    df['network_id'],
    df['n_nodes'],
    df['orig_n_nodes'] - df['n_nodes'],
    labels=['Clustered', 'Outliers'],
    colors=flatui,
)
ax.legend(loc='upper left')
ax.set_yscale('log')
ax.set_ylabel('Number of vertices (log scale)')
ax.set_xlabel('Networks')
ax.set_xticks([])
ax.set_xlim(0, len(df) - 1)
plt.title('Number of clustered and outlier vertices in networks')
plt.grid()
plt.tight_layout()
plt.savefig('clustered_ratio.pdf')

fig, ax = plt.subplots(1, 1, figsize=(10, 6), dpi=300)
ax.stackplot(
    df['network_id'],
    df['proportion'],
    1 - df['proportion'],
    labels=['Clustered', 'Outliers'],
    colors=flatui,
)
ax.legend(loc='upper left')
# ax.set_yscale('log')
ax.set_ylabel('Proportion of clustered vertices')
ax.set_ylim(0, 1)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
ax.set_xlabel('Networks')
ax.set_xticks([])
ax.set_xlim(0, len(df) - 1)
# plt.title('Proportion of clustered vertices in networks with Leiden-CPM at resolution $0.001$')
plt.grid()
plt.tight_layout()
plt.savefig('clustered_ratio_plus.pdf')