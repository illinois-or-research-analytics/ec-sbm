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

# == Generate ABCD network ==
print(f'Seed: {seed}')

cmd = f'julia ABCDGraphGenerator.jl/utils/graph_sampler_abcdta4.jl \
                {output_dir}/{EDGE} {output_dir}/{COM_OUT} \
                {output_dir}/{DEG} {output_dir}/{CS} \
                xi {xi} false false {seed} 0 \
                {output_dir}/{COM_INP} {output_dir}/{MCS}'

with open(f'{output_dir}/run.log', 'w') as f:
    f.write(cmd)
    f.write('\n')

    start = time.perf_counter()
    os.system(cmd)
    post_process(output_dir)
    elapsed = time.perf_counter() - start

    f.write(f"Generation time: {elapsed}")
