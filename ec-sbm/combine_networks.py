import argparse
from pathlib import Path
import time
import logging
import shutil

from src.constants import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-edgelist-1', type=str, required=True)
    parser.add_argument('--input-edgelist-2', type=str, required=True)
    parser.add_argument('--input-clustering', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    return parser.parse_args()


args = parse_args()

edgelist_1_fp = Path(args.input_edgelist_1)
edgelist_2_fp = Path(args.input_edgelist_2)
clustering_fp = Path(args.input_clustering)
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

logging.info(f'Combine two subnetworks')
logging.info(f'First subnetwork: {edgelist_1_fp}')
logging.info(f'Second subnetwork: {edgelist_2_fp}')
logging.info(f'Clustering: {clustering_fp}')
logging.info(f'Output folder: {output_dir}')

# ========================

assert edgelist_1_fp.exists()
assert edgelist_2_fp.exists()
assert clustering_fp.exists()

start = time.perf_counter()

# Copy clustering to output folder
shutil.copy(clustering_fp, output_dir / COM_OUT)

elapsed = time.perf_counter() - start
logging.info(f"Replicate clustering: {elapsed}")

# ========================

start = time.perf_counter()

# Concatenate the two edgelists
edgelist_fp_out = output_dir / EDGE
with open(edgelist_fp_out, 'w') as f_out:
    with open(edgelist_1_fp, 'r') as f:
        for line in f:
            f_out.write(line)

    with open(edgelist_2_fp, 'r') as f:
        for line in f:
            f_out.write(line)

elapsed = time.perf_counter() - start
logging.info(f"Combine clustered and outlier subgraphs: {elapsed}")
