from pathlib import Path
import json

import pandas as pd

split = 'val'
root = Path('data/stats/')
networks_list = f'data/networks_{split}.txt'

network_ids = [
    line.strip() for line in open(networks_list)
]

clustering = 'sbm_wcc'
resolution = 'sbm'

out_fp = Path(
    f'output/stats/stats_{split}_{clustering}_{resolution}.csv')
out_fp.parent.mkdir(parents=True, exist_ok=True)

all_stats = []
for network_id in network_ids:
    stats = {
        'network_id': network_id,
    }

    syn_log_fp = root / 'orig' / clustering / \
        network_id / resolution / 'stats.json'

    if not syn_log_fp.exists():
        continue

    with open(syn_log_fp) as f:
        data = json.load(f)

    stats['n_nodes'] = data['n_nodes']
    stats['n_edges'] = data['n_edges']
    stats['n_clusters'] = data['n_clusters']
    stats['n_onodes'] = data['n_onodes']

    all_stats.append(stats)

df = pd.DataFrame(all_stats)
df['node_coverage'] = 1 - df['n_onodes'] / df['n_nodes']
df['n_cnodes'] = df['n_nodes'] - df['n_onodes']
df.sort_values('n_cnodes', inplace=True, ascending=False)
df.to_csv(out_fp, index=False)
