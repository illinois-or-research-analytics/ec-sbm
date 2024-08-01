from pathlib import Path
import json

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import pandas as pd

plt.rcParams.update({'font.size': 20})

large_network_ids = [
    'cit_hepph',
    'cit_patents',
    'wiki_talk',
    'wiki_topcats',
    'orkut',
    'cen'
]

root = Path('data/stats/orig/leiden_cpm_cm/')
resolution = 'leiden.001'

data_dict = []
for fp in root.iterdir():
    if not fp.is_dir():
        continue
    
    network_id = fp.name
    stats_fp = fp / resolution / 'stats.json'

    if not stats_fp.exists():
        continue

    stats = json.loads(stats_fp.read_text())
    stats['network_id'] = network_id
    stats['is_special'] = network_id in large_network_ids
    data_dict.append(stats)

df = pd.DataFrame(data_dict)

flatui = ["#9b59b6", "#3498db", "#95a5a6", "#e74c3c", "#34495e", "#2ecc71"]
my_cmap = ListedColormap(sns.color_palette(flatui).as_hex())

fig, ax = plt.subplots(1, 1, figsize=(10, 7), dpi=300)
ax.scatter(
    data=df,
    x='n_nodes',
    y='n_edges',
    c='is_special',
    cmap=my_cmap,
)
plt.xscale('log')
plt.yscale('log')
plt.xlabel('Number of nodes (log scale)')
plt.ylabel('Number of edges (log scale)')
plt.title('Number of nodes and edges in networks')
plt.grid()
plt.tight_layout()
plt.savefig('n_nodes_edges.pdf')