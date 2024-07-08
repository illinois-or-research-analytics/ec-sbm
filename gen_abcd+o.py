import os
import time
import json
import argparse
import csv

from src.utils import set_up
from src.constants import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--edgelist', type=str, required=True)
    parser.add_argument('--clustering', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    parser.add_argument('--seed', type=int, required=False, default=0)
    return parser.parse_args()


print('== Input == ')

args = parse_args()
edgelist_fn = args.edgelist
clustering_fn = args.clustering
output_dir = args.output_folder
seed = args.seed

print(f'Method: ABCD')
print(f'Network: {edgelist_fn}')
print(f'Clustering: {clustering_fn}')
print(f'Output folder: {output_dir}')
print(f'Seed: {seed}')

print('== Output == ')

logs = []

start = time.perf_counter()
set_up(
    edgelist_fn,
    clustering_fn,
    seed,
    output_dir,
    use_existing_clustering=True,
    is_count_outliers=True,
)
elapsed = time.perf_counter() - start
logs.append(f"Setup time: {elapsed}")

with open(f'{output_dir}/params.json', 'r') as f:
    params = json.load(f)
    seed = params['seed']
    xi = params['xi']
    n_outliers = params['n_outliers']

# add n_outliers as the first line of {output_dir}/{CS}
with open(f'{output_dir}/{CS}', 'r') as f:
    csv_reader = csv.reader(f, delimiter='\t')
    rows = list(csv_reader)
    rows.insert(0, [n_outliers])
with open(f'{output_dir}/{CS}', 'w') as f:
    csv_writer = csv.writer(f, delimiter='\t')
    csv_writer.writerows(rows)

# add 0 n_outliers times to the end of {output_dir}/{DEG}
# TODO: actually, not all outliers have degree 0
with open(f'{output_dir}/{DEG}', 'r') as f:
    csv_reader = csv.reader(f, delimiter='\t')
    rows = list(csv_reader)
    rows.extend([[0]] * n_outliers)
with open(f'{output_dir}/{DEG}', 'w') as f:
    csv_writer = csv.writer(f, delimiter='\t')
    csv_writer.writerows(rows)

cmd = f'''
julia ABCDGraphGenerator.jl/utils/graph_sampler.jl \
    {output_dir}/{EDGE} {output_dir}/{COM_OUT} \
    {output_dir}/{DEG} {output_dir}/{CS} \
    xi {xi} false false {seed} {n_outliers}
'''
logs.append(cmd)

start = time.perf_counter()
os.system(cmd)
elapsed = time.perf_counter() - start
logs.append(f"Generation time: {elapsed}")

# start = time.perf_counter()
# try:
#     post_process(output_dir)
# except Exception as e:
#     logs.append(f"Post-process error: {e}")
# elapsed = time.perf_counter() - start
# logs.append(f"Post-process time: {elapsed}")

if os.path.exists(f'{output_dir}/{COM_OUT}') and n_outliers > 0:
    # TODO: is the 1st cluster always the outlier cluster?
    with open(f'{output_dir}/{COM_OUT}', 'r') as f:
        csv_reader = csv.reader(f, delimiter='\t')
        rows = []
        all_vertices = set()
        for v, c in csv_reader:
            if c != '1':
                rows.append([v, c])
            all_vertices.add(v)
    with open(f'{output_dir}/{COM_OUT}', 'w') as f:
        csv_writer = csv.writer(f, delimiter='\t')
        csv_writer.writerows(rows)

    # append self loop for all nodes
    with open(f'{output_dir}/{EDGE}', 'a') as f:
        for v in all_vertices:
            f.write(f'{v}\t{v}\n')

# TODO: why are there edges inside the outlier cluster?

assert os.path.exists(output_dir)
log_f = open(f'{output_dir}/run.log', 'w')
for log in logs:
    log_f.write(log)
    log_f.write('\n')
log_f.close()
