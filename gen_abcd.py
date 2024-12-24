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

logging.info(f'Method: ABCD')
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
    for_abcd=True,
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

# add n_outliers 1s at the end of {output_dir}/{CS}
with open(f'{output_dir}/{CS}', 'r') as f:
    csv_reader = csv.reader(f, delimiter='\t')
    rows = list(csv_reader)
    # if n_outliers > 0:
    #     rows.insert(0, [n_outliers])
    for _ in range(n_outliers):
        rows.append(['1'])

with open(f'{output_dir}/{CS_WITH_OUTLIERS}', 'w') as f:
    csv_writer = csv.writer(f, delimiter='\t')
    csv_writer.writerows(rows)

elapsed = time.perf_counter() - start
logging.info(f"Compute ABCD parameters time: {elapsed}")

# ========================

start = time.perf_counter()

cmd = f'''
julia ABCDGraphGenerator.jl/utils/graph_sampler.jl \
    {output_dir}/{EDGE} {output_dir}/{COM_OUT} \
    {output_dir}/{DEG} {output_dir}/{CS_WITH_OUTLIERS} \
    xi {xi} false false {seed} 0
'''
logging.info(cmd)

os.system(cmd)

elapsed = time.perf_counter() - start
logging.info(f"Generation time: {elapsed}")

# ========================

# start = time.perf_counter()

# if os.path.exists(f'{output_dir}/{COM_OUT}'):
#     with open(f'{output_dir}/{COM_OUT}', 'r') as f:
#         csv_reader = csv.reader(f, delimiter='\t')
#         rows = []
#         for v, c in csv_reader:
#             rows.append([v, c])

#     with open(f'{output_dir}/{COM_OUT}', 'w') as f:
#         csv_writer = csv.writer(f, delimiter='\t')
#         csv_writer.writerows(rows)

# elapsed = time.perf_counter() - start
# logging.info(f"Post-processing time: {elapsed}")
