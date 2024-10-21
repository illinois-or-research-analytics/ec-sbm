import argparse
from pathlib import Path
import time
import logging
import shutil

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

# ========================

output_dir.mkdir(parents=True, exist_ok=True)
log_path = output_dir / 'combine_run.log'
logging.basicConfig(
    filename=log_path,
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# ========================

logging.info(f'Combine Clustered and Outlier Subnetworks')
logging.info(f'Clustered Network: {clustered_edgelist_fp}')
logging.info(f'Clustering: {clustered_clustering_fp}')
logging.info(f'Outlier Network: {outlier_edgelist_fp}')
logging.info(f'Output folder: {output_dir}')

# ========================

assert clustered_edgelist_fp.exists()
assert clustered_clustering_fp.exists()
assert outlier_edgelist_fp.exists()

start = time.perf_counter()

# Copy clustering to output folder
shutil.copy(clustered_clustering_fp, output_dir / COM_OUT)

elapsed = time.perf_counter() - start
logging.info(f"Replicate clustering: {elapsed}")

# ========================

start = time.perf_counter()

# Concatenate the two edgelists
edgelist_fp_out = output_dir / EDGE
with open(edgelist_fp_out, 'w') as f_out:
    with open(clustered_edgelist_fp, 'r') as f:
        for line in f:
            f_out.write(line)

    with open(outlier_edgelist_fp, 'r') as f:
        for line in f:
            f_out.write(line)

elapsed = time.perf_counter() - start
logging.info(f"Combine clustered and outlier subgraphs: {elapsed}")
