import argparse
from pathlib import Path
import time

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

logs = []

print(f'Combine Clustered and Outlier Subnetworks')
print(f'Clustered Network: {clustered_edgelist_fp}')
print(f'Clustering: {clustered_clustering_fp}')
print(f'Outlier Network: {outlier_edgelist_fp}')
print(f'Output folder: {output_dir}')

logs.append(f'Combine Clustered and Outlier Subnetworks')
logs.append(f'Clustered Network: {clustered_edgelist_fp}')
logs.append(f'Clustering: {clustered_clustering_fp}')
logs.append(f'Outlier Network: {outlier_edgelist_fp}')
logs.append(f'Output folder: {output_dir}')
logs.append('')

print('== Output == ')

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
print(f"Combine clustered and outlier subgraphs: {elapsed}")
logs.append(f"Combine clustered and outlier subgraphs: {elapsed}")

assert output_dir.exists()
log_f = open(f'{output_dir}/combine_run.log', 'w')
for log in logs:
    log_f.write(log)
    log_f.write('\n')
log_f.close()