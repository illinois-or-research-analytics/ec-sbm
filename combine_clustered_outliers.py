import argparse
from pathlib import Path

from src.constants import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clustered-edgelist', type=str, required=True)
    parser.add_argument('--clustered-clustering', type=str, required=True)
    parser.add_argument('--outlier-edgelist', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    return parser.parse_args()


args = parse_args()
clustered_edgelist_fp = Path(args.clustered_edgelist)
clustered_clustering_fp = Path(args.clustered_clustering)
outlier_edgelist_fp = Path(args.outlier_edgelist)
output_dir = Path(args.output_folder)

assert clustered_edgelist_fp.exists()
assert clustered_clustering_fp.exists()
assert outlier_edgelist_fp.exists()

output_dir.mkdir(parents=True, exist_ok=True)

# Copy clustering to output folder
clustering_fp_out = output_dir / COM_OUT
with open(clustering_fp_out, 'w') as f_out:
    with open(clustered_clustering_fp, 'r') as f:
        for line in f:
            f_out.write(line)

# Concatenate the two edgelists
edgelist_fp_out = output_dir / EDGE
with open(edgelist_fp_out, 'w') as f_out:
    with open(clustered_edgelist_fp, 'r') as f:
        for line in f:
            f_out.write(line)

    with open(outlier_edgelist_fp, 'r') as f:
        for line in f:
            f_out.write(line)
