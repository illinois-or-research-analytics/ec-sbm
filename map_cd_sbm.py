from pathlib import Path
import argparse

import pandas as pd

parser = argparse.ArgumentParser(
    description='Generate mapping for accuracy computation')
parser.add_argument('--split', type=str, default='test',
                    help='Data split to use')
parser.add_argument('--method', type=str, default='sbmmcsprev1+o+eL1',
                    help='Method to use')
parser.add_argument('--clustering', type=str, default='sbm_wcc',
                    help='Clustering to use')
parser.add_argument('--resolution', type=str, default='sbm',
                    help='Resolution to use')
parser.add_argument('--cd-root', type=str, default='data/community_detection',
                    help='Community detection root directory')
parser.add_argument('--gt-root', type=str, default='data/networks',
                    help='Ground truth root directory')
args = parser.parse_args()

split = args.split
cd_root = Path(args.cd_root)
gt_root = Path(args.gt_root)

method = args.method
clustering = args.clustering
resolution = args.resolution

networks_list = f'data/networks_{split}.txt'
network_ids = [
    line.strip() for line in open(networks_list)
]

out_fp = Path(
    f'data/comdet_acc/cd_acc_{split}_sbm/mapping_{split}_{clustering}_{resolution}.csv')
out_fp.parent.mkdir(parents=True, exist_ok=True)

lines = []
for network_id in network_ids:
    gt_comm = gt_root / method / clustering / \
        network_id / resolution / '0' / 'com.tsv'

    cd_dir = cd_root / method / clustering / network_id / \
        resolution / '0'

    if not cd_dir.exists():
        print(f'Not found: {cd_dir}')
        continue

    network_fp = cd_dir / 'sbm' / 'sbm' / 'edge.tsv'
    sbm_fp = cd_dir / 'sbm' / 'sbm' / 'com.tsv'
    sbm_cc_fp = cd_dir / 'sbm_cc' / 'sbm' / 'com.tsv'
    sbm_wcc_fp = cd_dir / 'sbm_wcc' / 'sbm' / 'com.tsv'

    def process_fp(fp):
        if not fp.exists():
            print(f'Not found: {fp}')
            return None
        return str(fp)

    line = {
        'network': network_id,
        'method': method,
        'gt_clustering': clustering,
        'gt_resolution': resolution,
        'cd_clustering': 'sbm',
        'cd_resolution': 'sbm',
        'network_fp': process_fp(network_fp),
        'comm_gt': process_fp(gt_comm),
        'comm_sbm': process_fp(sbm_fp),
        'comm_sbm_cc': process_fp(sbm_cc_fp),
        'comm_sbm_wcc': process_fp(sbm_wcc_fp),
    }

    lines.append(line)

df = pd.DataFrame(lines)
df.to_csv(out_fp, index=False)
