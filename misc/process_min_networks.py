import os
from pathlib import Path
import pandas as pd

root = Path('data/min-networks')
outroot = Path('data/networks/orig/')
resolution = '.001'

networks_dir = root / 'graphs/'
leiden_cpm_clustering_dir = root / f'leiden_cpm_0{resolution}/'
leiden_cpm_cm_clustering_dir = leiden_cpm_clustering_dir / 'cm/'

network_ids = [
    path.stem.replace('-clean', '')
    for path in networks_dir.iterdir()
]

network_with_clustering = []

for network_id in network_ids:
    network_fp = networks_dir / f'{network_id}-clean.tsv'
    leiden_cpm_clustering_fp = leiden_cpm_clustering_dir / \
        network_id / 'output' / 'leiden.clustering'
    leiden_cpm_cm_clustering_fp = leiden_cpm_cm_clustering_dir / \
        network_id / 'output' / 'cm.clustering'

    if not leiden_cpm_cm_clustering_fp.exists():
        print(f'Network {network_id} is missing')
        continue

    network_with_clustering.append(network_id)

    # leiden_cpm_outdir = outroot / 'leiden_cpm' / \
    #     network_id / f'leiden{resolution}'
    # leiden_cpm_outdir.mkdir(parents=True, exist_ok=True)

    # leiden_cpm_out_network_fp = leiden_cpm_outdir / 'edge.dat'
    # leiden_cpm_out_clustering_fp = leiden_cpm_outdir / 'com.dat'
    # os.system(f'cp {network_fp} {leiden_cpm_out_network_fp}')
    # os.system(f'cp {leiden_cpm_clustering_fp} {leiden_cpm_out_clustering_fp}')

    # leiden_cpm_cm_outdir = outroot / 'leiden_cpm_cm' / \
    #     network_id / f'leiden{resolution}'
    # leiden_cpm_cm_outdir.mkdir(parents=True, exist_ok=True)

    # leiden_cpm_cm_out_network_fp = leiden_cpm_cm_outdir / 'edge.dat'
    # leiden_cpm_cm_out_clustering_fp = leiden_cpm_cm_outdir / 'com.dat'
    # os.system(f'cp {network_fp} {leiden_cpm_cm_out_network_fp}')
    # os.system(f'cp {leiden_cpm_cm_clustering_fp} {
    #     leiden_cpm_cm_out_clustering_fp}')

with open('networks.txt', 'w') as f:
    df = pd.DataFrame(network_with_clustering)
    df.to_csv(f, index=False, header=False)
