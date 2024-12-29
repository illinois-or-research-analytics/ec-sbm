import os
import sys
import argparse
from pathlib import Path

import graph_tool.all as gt


def run_best_sbm(input_network, working_directory, output_clustering, num_processors=1):
    gt.openmp_set_num_threads(num_processors)
    g = gt.load_graph_from_csv(input_network, csv_options={'delimiter': '\t'})
    gt.remove_parallel_edges(g)
    gt.remove_self_loops(g)
    num_nodes_total = g.num_vertices()

    min_description_length = None
    best_sbm_model = None
    best_sbm_clustering = None
    sbm_arr = ["dc", "ndc", "pp"]
    with open(f"{working_directory}/get_best_sbm.log", "w") as f:
        f.write(
            f"Running degree corrected (dc), non degree corrected (ndc), and planted partition (pp)\n")
    for current_sbm in sbm_arr:
        current_clustering = None
        current_description_length = None
        if current_sbm == "dc":
            current_clustering = gt.minimize_blockmodel_dl(
                g, state=gt.BlockState, state_args=dict(deg_corr=True))
            current_description_length = current_clustering.entropy()
        elif current_sbm == "ndc":
            current_clustering = gt.minimize_blockmodel_dl(
                g, state=gt.BlockState, state_args=dict(deg_corr=False))
            current_description_length = current_clustering.entropy()
        elif current_sbm == "pp":
            current_clustering = gt.minimize_blockmodel_dl(
                g, state=gt.PPBlockState)
            current_description_length = current_clustering.entropy()

        if min_description_length == None or current_description_length < min_description_length:
            min_description_length = current_description_length
            best_sbm_clustering = current_clustering
            best_sbm_model = current_sbm

        with open(f"{working_directory}/get_best_sbm.log", "a") as f:
            f.write(f"{current_sbm} description length: {
                    current_description_length}\n")

        with open(f"{working_directory}/{current_sbm}.clustering", "w") as f:
            blocks = current_clustering.get_blocks()
            for v in g.vertices():
                nodeId = g.vp.name[v]
                cur_block = blocks[v]
                # Check if block is valid
                if cur_block < 0 or cur_block > num_nodes_total - 1:
                    continue
                f.write(f"{nodeId}\t{cur_block}\n")

    with open(f"{working_directory}/get_best_sbm.log", "a") as f:
        f.write(f"best sbm: {best_sbm_model}\n")

    with open(f"{output_clustering}", "w") as f:
        blocks = best_sbm_clustering.get_blocks()
        for v in g.vertices():
            nodeId = g.vp.name[v]
            cur_block = blocks[v]
            # Check if block is valid
            if cur_block < 0 or cur_block > num_nodes_total - 1:
                continue
            f.write(f"{nodeId}\t{cur_block}\n")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--edgelist', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    return parser.parse_args()


args = parse_args()
edgelist_fn = args.edgelist
output_dir = Path(args.output_folder)

output_dir.mkdir(parents=True, exist_ok=True)

run_best_sbm(
    edgelist_fn,
    str(output_dir),
    str(output_dir / 'com.tsv'),
)
