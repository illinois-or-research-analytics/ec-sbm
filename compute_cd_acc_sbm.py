from pathlib import Path
import argparse

import pandas as pd

from network_evaluation import compute_cd_accuracy

# Parse command line arguments
parser = argparse.ArgumentParser(description='Compute CD Accuracy')
parser.add_argument('--mapping_fp', type=str, help='Path to the mapping file')
parser.add_argument('--output_root', type=str, help='Output root directory')
args = parser.parse_args()

mapping_fp = args.mapping_fp
output_root = Path(args.output_root)
output_root.mkdir(parents=True, exist_ok=True)

# Load the mapping file
mapping = pd.read_csv(mapping_fp)

# Iterate over the rows of the mapping file
for i, row in mapping.iterrows():
    print(f'Processing row {i+1}/{len(mapping)}')

    if row['gt_clustering'] == 'infomap':
        row['gt_clustering'] = 'infomap_cc'

    clustering_types = {
        'sbm': 'comm_sbm',
        'sbm_cc': 'comm_sbm_cc',
        'sbm_wcc': 'comm_sbm_wcc',
    }

    for suffix, clustering_key in clustering_types.items():
        # Get the parameters from the mapping file
        input_edgelist = row['network_fp']
        groundtruth_clustering = row['comm_gt']
        estimated_clustering = row[clustering_key]

        output_file = output_root / row['method'] / row['gt_clustering'] / row['network'] / \
            row['gt_resolution'] / '0' / suffix / \
            'sbm' / 'accuracy.txt'
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # If dummy done file exists
        done_file = output_file.parent / 'done'
        if done_file.exists():
            continue

        # Run the min_accuracy function
        compute_cd_accuracy.min_accuracy(
            input_edgelist, groundtruth_clustering,
            estimated_clustering, output_file)

        # Make a done file
        done_file.touch()
