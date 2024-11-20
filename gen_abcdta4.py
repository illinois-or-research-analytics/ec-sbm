import os
import time
import json
import logging
import argparse
from pathlib import Path

from src.utils import set_up, post_process
from src.constants import *


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

logging.info(f'Method: ABCD-MCS(pre)')
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
)

with open(f'{output_dir}/params.json', 'r') as f:
    params = json.load(f)
    seed = params['seed']
    xi = params['xi']

elapsed = time.perf_counter() - start
logging.info(f"Setup time: {elapsed}")

# ========================

is_run_cmd = True

# Check if DEG is empty
with open(f'{output_dir}/{DEG}', 'r') as f:
    if len(f.readlines()) == 0:
        is_run_cmd = False

# Check if CS is empty
with open(f'{output_dir}/{CS}', 'r') as f:
    if len(f.readlines()) == 0:
        is_run_cmd = False

# ========================

start = time.perf_counter()

cmd = f'''
julia ABCDGraphGenerator.jl/utils/graph_sampler_abcdta4.jl \\
    {output_dir}/{EDGE} {output_dir}/{COM_OUT} \\
    {output_dir}/{DEG} {output_dir}/{CS} \\
    xi {xi} false false {seed} 0 \\
    {output_dir}/{COM_INP} {output_dir}/{MCS}
'''
logging.info(cmd)

if is_run_cmd:
    os.system(cmd)
else:
    # Create empty {EDGE} and {COM_OUT}
    with open(f'{output_dir}/{EDGE}', 'w') as f:
        f.write('')
    with open(f'{output_dir}/{COM_OUT}', 'w') as f:
        f.write('')
    logging.info("Skip due to empty input files.")

elapsed = time.perf_counter() - start
logging.info(f"Generation time: {elapsed}")

# ========================

start = time.perf_counter()

try:
    post_process(output_dir)
except Exception as e:
    logging.info(f"Post-process error: {e}")

elapsed = time.perf_counter() - start
logging.info(f"Post-process time: {elapsed}")
