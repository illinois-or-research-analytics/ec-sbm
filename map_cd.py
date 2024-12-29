from pathlib import Path

import pandas as pd

split = 'test'
cd_root = Path('data/community_detection')
gt_root = Path('data/networks')
networks_list = f'data/networks_{split}.txt'

network_ids = [
    line.strip() for line in open(networks_list)
]

method = 'sbmmcsprev1+o+eL1'
clustering = 'sbm_wcc'
resolution = 'sbm'

out_fp = Path(f'data/comdet_acc/cd_acc_{split}/mapping_{split}.csv')
out_fp.parent.mkdir(parents=True, exist_ok=True)

cd_clusterings_resolutions = [
    ('leiden_cpm', 'leiden.1'),
    ('leiden_cpm', 'leiden.01'),
    ('leiden_cpm', 'leiden.001'),
    ('leiden_cpm', 'leiden.0001'),
    ('leiden_mod', 'leidenmod'),
    ('infomap', 'infomap'),
]

lines = []

for network_id in network_ids:
    for cd_clustering, cd_resolution in cd_clusterings_resolutions:
        gt_comm = gt_root / method / clustering / \
            network_id / resolution / '0' / 'com.tsv'

        if not gt_comm.exists():
            print(f'Not found: {gt_comm}')
            continue

        cd_dir = cd_root / method / clustering / network_id / \
            resolution / '0' / cd_clustering / cd_resolution
        if not cd_dir.exists():
            print(f'Not found: {cd_dir}')
            continue

        candidates = list(cd_dir.rglob('*S1_*.tsv'))
        if len(candidates) != 1:
            print(f'Not found: {cd_dir}')
            continue
        S1_fp = candidates[0]

        candidates = list(cd_dir.rglob('*S2_*.tsv'))
        if len(candidates) != 1:
            print(f'Not found: {cd_dir}')
            continue
        S2_fp = candidates[0]

        candidates = list(cd_dir.rglob('*S3_*.tsv'))
        if len(candidates) != 1:
            print(f'Not found: {cd_dir}')
            continue
        S3_fp = candidates[0]

        line = {
            'network': network_id,
            'method': method,
            'gt_clustering': clustering,
            'gt_resolution': resolution,
            'cd_clustering': cd_clustering,
            'cd_resolution': cd_resolution,
            'network_fp': S1_fp,
            'comm_gt': gt_comm,
            'comm_cd': S2_fp,
            'comm_cdcm': S3_fp,
        }

        lines.append(line)

for network_id in network_ids:
    # line = {
    #     'network': network_id,
    #     'method': method,
    #     'gt_clustering': clustering,
    #     'gt_resolution': resolution,
    #     'cd_clustering': 'sbm',
    #     'cd_resolution': 'sbm',
    #     'network_fp': '',
    #     'comm_gt': gt_root / method / clustering /
    #     network_id / resolution / '0' / 'com.tsv',
    #     'comm_cd': cd_root / method / clustering /
    #     network_id / resolution / '0' / 'sbm' / 'sbm' / 'com.tsv',
    #     'comm_cdcm': cd_root / method / clustering /
    #     network_id / resolution / '0' / 'sbm_nofiltcm' / 'sbm' / 'sbm' / 'com.tsv',
    # }
    pass

df = pd.DataFrame(lines)
df.to_csv(out_fp, index=False)
