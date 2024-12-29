from pathlib import Path
import argparse
import logging

import pandas as pd

from network_evaluation import compute_cd_accuracy

# Parse command line arguments
parser = argparse.ArgumentParser(description='Compute CD Accuracy')
parser.add_argument('--mapping_fp', type=str,
                    default='output/cd_acc_filt/mapping.csv', help='Path to the mapping file')
parser.add_argument('--output_root', type=str,
                    default='output/cd_acc_filt/', help='Output root directory')
parser.add_argument('--whitelist', type=str,
                    help='Whitelist of cd_clustering and cd_resolution pairs')
args = parser.parse_args()

mapping_fp = args.mapping_fp
output_root = Path(args.output_root)
output_root.mkdir(parents=True, exist_ok=True)

# Load the mapping file
mapping = pd.read_csv(mapping_fp)

# Parse whitelist from command line arguments
whitelist = [
    tuple(item.split(','))
    for item in args.whitelist.split(';')
]

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

for i, row in mapping.iterrows():
    if row['gt_clustering'] == 'infomap':
        row['gt_clustering'] = 'infomap_cc'

    if (row['cd_clustering'], row['cd_resolution']) not in whitelist:
        continue

    logging.info(f'Processing {row["method"]} {row["gt_clustering"]} {row["network"]} {
                 row["gt_resolution"]} {row["cd_clustering"]} {row["cd_resolution"]}')

    clustering_types = {
        'S2': 'comm_cd',
        'S3': 'comm_cd_filt',
        'S4': 'comm_cm',
        'S5': 'comm_cm_filt',
    }

    for suffix, clustering_key in clustering_types.items():
        # Get the parameters from the mapping file
        input_edgelist = row['network_fp']
        groundtruth_clustering = row['comm_gt']
        estimated_clustering = row[clustering_key]

        output_file = output_root / row['method'] / row['gt_clustering'] / row['network'] / \
            row['gt_resolution'] / '0' / row['cd_clustering'] / \
            row['cd_resolution'] / suffix / 'accuracy.txt'
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # If dummy done file exists
        done_file = output_file.parent / 'done'
        if done_file.exists():
            logging.info(f'({clustering_key}) Skipping as done file exists...')
            continue

        # Run the min_accuracy function
        logging.info(f'({clustering_key}) Computing accuracy...')
        try:
            compute_cd_accuracy.min_accuracy(
                input_edgelist, groundtruth_clustering,
                estimated_clustering, output_file)
        except Exception as e:
            logging.error(f'({clustering_key}) Error: {e}')
            continue

        logging.info(f'({clustering_key}) Created done file...')
        # Make a done file
        done_file.touch()

        logging.info(f'({clustering_key}) Done')
