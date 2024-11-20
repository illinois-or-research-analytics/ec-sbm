import os
from pathlib import Path

root = Path('data/SBM_subnetworks_samples/')
output_root = Path('data/networks/sbmmcspost/')

network_ids = set()
for network_id in root.iterdir():
    network_ids.add(network_id.name)

for network_id in network_ids:
    resolution = '.001'

    fp = root / network_id / ('0' + resolution) / 'sbm_mcs'

    out_fp_root = output_root / 'leiden_cpm_cm' / \
        network_id / ('leiden' + resolution)
    out_fp_root.mkdir(parents=True, exist_ok=True)

    for replicate in fp.iterdir():
        rep_id = replicate.name.split('_')[-1]
        out_fp = out_fp_root / rep_id

        # os.system(f'cp -r {replicate} {out_fp}')

        os.system(f'mv {out_fp}/compare_stats.csv {out_fp}/compare_output.csv')
