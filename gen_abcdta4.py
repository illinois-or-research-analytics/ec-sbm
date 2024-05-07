import sys
import os
import time
import json

from utils import set_up, post_process
from constants import *


network_id = sys.argv[1]
resolution = sys.argv[2]
method = sys.argv[3]
based_on = sys.argv[4]


output_dir = set_up(method,
                    based_on, network_id, resolution,
                    use_existing_clustering=True)

with open(f'{output_dir}/params.json', 'r') as f:
    params = json.load(f)
    seed = params['seed']
    xi = params['xi']

# == Generate ABCD network
print(
    f'Generating ABCD-TA-p-k network for {network_id} with resolution {resolution}...')
print(f'Mixing parameter (xi) {xi}')

cmd = f'julia ABCDGraphGenerator.jl/utils/graph_sampler_{method}.jl \
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
