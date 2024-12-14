import os
import csv
import time
import json
import logging
import argparse
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT

from src.utils import set_up
from src.constants import *

CS_WITH_OUTLIERS = 'cs_with_outliers.tsv'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--edgelist', type=str, required=True)
    parser.add_argument('--clustering', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    parser.add_argument('--seed', type=int, required=False, default=0)
    return parser.parse_args()


args = parse_args()
edgelist_fn = args.edgelist
clustering_fn = args.clustering
output_dir = args.output_folder
seed = args.seed

# ========================

Path(output_dir).mkdir(parents=True, exist_ok=True)
log_path = Path(output_dir) / 'run.log'
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

logging.info(f'Method: ABCD+o')
logging.info(f'Network: {edgelist_fn}')
logging.info(f'Clustering: {clustering_fn}')
logging.info(f'Output folder: {output_dir}')
logging.info(f'Seed: {seed}')

# ========================

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
logging.info(f"Setup time: {elapsed}")

# ========================

start = time.perf_counter()

with open(f'{output_dir}/params.json', 'r') as f:
    params = json.load(f)
    seed = params['seed']
    xi = params['xi']
    n_outliers = params['n_outliers']

# add n_outliers as the first line of {output_dir}/{CS}
with open(f'{output_dir}/{CS}', 'r') as f:
    csv_reader = csv.reader(f, delimiter='\t')
    rows = list(csv_reader)
    if n_outliers > 0:
        rows.insert(0, [n_outliers])
with open(f'{output_dir}/{CS_WITH_OUTLIERS}', 'w') as f:
    csv_writer = csv.writer(f, delimiter='\t')
    csv_writer.writerows(rows)

elapsed = time.perf_counter() - start
logging.info(f"Compute ABCD+o parameters time: {elapsed}")

# ========================

start = time.perf_counter()

cmd = f'''
julia ABCDGraphGenerator.jl/utils/graph_sampler.jl \
    {output_dir}/{EDGE} {output_dir}/{COM_OUT} \
    {output_dir}/{DEG} {output_dir}/{CS_WITH_OUTLIERS} \
    xi {xi} false false {seed} {n_outliers}
'''
logging.info(cmd)

os.system(cmd)

elapsed = time.perf_counter() - start
logging.info(f"Generation time: {elapsed}")

# ========================

start = time.perf_counter()

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

    # # append self loop for all nodes (so the evaluation script can run)
    # # TODO: is this necessary?
    # with open(f'{output_dir}/{EDGE}', 'a') as f:
    #     for v in all_vertices:
    #         f.write(f'{v}\t{v}\n')

elapsed = time.perf_counter() - start
logging.info(f"Post-processing time: {elapsed}")
