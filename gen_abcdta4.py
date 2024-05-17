import os
import time
import json
import argparse

from src.utils import set_up, post_process
from src.constants import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--edgelist', type=str, required=True)
    parser.add_argument('--clustering', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    parser.add_argument('--seed', type=int, required=False, default=0)
    parser.add_argument('--id', type=str, required=False, default='default_id')
    return parser.parse_args()


args = parse_args()
edgelist_fn = args.edgelist
clustering_fn = args.clustering
output_dir = args.output_folder
seed = args.seed

logs = []

start = time.perf_counter()
set_up(
    edgelist_fn,
    clustering_fn,
    seed,
    output_dir,
    use_existing_clustering=True,
)
elapsed = time.perf_counter() - start
logs.append(f"Setup time: {elapsed}")

with open(f'{output_dir}/params.json', 'r') as f:
    params = json.load(f)
    seed = params['seed']
    xi = params['xi']

cmd = f'''
julia ABCDGraphGenerator.jl/utils/graph_sampler_abcdta4.jl \\
    {output_dir}/{EDGE} {output_dir}/{COM_OUT} \\
    {output_dir}/{DEG} {output_dir}/{CS} \\
    xi {xi} false false {seed} 0 \\
    {output_dir}/{COM_INP} {output_dir}/{MCS}
'''
logs.append(cmd)

start = time.perf_counter()
os.system(cmd)
elapsed = time.perf_counter() - start
logs.append(f"Generation time: {elapsed}")

start = time.perf_counter()
post_process(output_dir)
elapsed = time.perf_counter() - start
logs.append(f"Post-process time: {elapsed}")

assert os.path.exists(output_dir)
log_f = open(f'{output_dir}/run.log', 'w')
for log in logs:
    log_f.write(log)
    log_f.write('\n')
log_f.close()
