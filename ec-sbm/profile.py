import time
import logging
import argparse
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
from pymincut.pygraph import PyGraph

from utils import setup_logging


def read_clustering(clustering_path):
    df = pd.read_csv(clustering_path, usecols=[0, 1], dtype=str).dropna()

    node2com = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
    cluster_counts = df.iloc[:, 1].value_counts().to_dict()
    nodes = set(node2com.keys())

    return nodes, node2com, cluster_counts


def read_edgelist(edgelist_path, nodes):
    neighbors = defaultdict(set)
    df = pd.read_csv(edgelist_path, usecols=[0, 1], dtype=str).dropna()

    for u, v in zip(df.iloc[:, 0], df.iloc[:, 1]):
        if u != v:  # Ignore self-loops
            neighbors[u].add(v)
            neighbors[v].add(u)
            nodes.add(u)
            nodes.add(v)

    return nodes, neighbors


def compute_node_degree(nodes, neighbors):
    node_degree_sorted = sorted(
        [(u, len(neighbors[u])) for u in nodes], reverse=True, key=lambda x: x[1]
    )
    node_id2iid = {u: i for i, (u, _) in enumerate(node_degree_sorted)}
    return node_degree_sorted, node_id2iid


def compute_comm_size(cluster_counts):
    comm_size_sorted = sorted(cluster_counts.items(), reverse=True, key=lambda x: x[1])
    cluster_id2iid = {c: i for i, (c, _) in enumerate(comm_size_sorted)}
    return comm_size_sorted, cluster_id2iid


def export_node_id(out_dir, node_degree_sorted):
    pd.DataFrame([u for u, _ in node_degree_sorted]).to_csv(
        f"{out_dir}/node_id.csv", index=False, header=False
    )


def export_cluster_id(out_dir, comm_size_sorted):
    pd.DataFrame([c for c, _ in comm_size_sorted]).to_csv(
        f"{out_dir}/cluster_id.csv", index=False, header=False
    )


def export_assignment(out_dir, node_degree_sorted, node2com, cluster_id2iid):
    assignments = [
        cluster_id2iid[node2com.get(u)] if u in node2com else -1
        for u, _ in node_degree_sorted
    ]
    pd.DataFrame(assignments).to_csv(
        f"{out_dir}/assignment.csv", index=False, header=False
    )


def export_degree(out_dir, node_degree_sorted):
    pd.DataFrame([deg for _, deg in node_degree_sorted]).to_csv(
        f"{out_dir}/degree.csv", index=False, header=False
    )


def compute_edge_count(nodes, neighbors, node2com, cluster_id2iid):
    edge_counts = defaultdict(int)
    for u in nodes:
        cu = node2com.get(u)
        if cu is None:
            continue
        c_iid_u = cluster_id2iid[cu]

        for v in neighbors[u]:
            cv = node2com.get(v)
            if cv is not None:
                c_iid_v = cluster_id2iid[cv]
                edge_counts[(c_iid_u, c_iid_v)] += 1
    return edge_counts


def export_edge_count(out_dir, edge_counts):
    data = [[r, c, w] for (r, c), w in edge_counts.items()]
    pd.DataFrame(data).to_csv(f"{out_dir}/edge_counts.csv", index=False, header=False)


def compute_mincut(nodes, neighbors, node2com, comm_size_sorted, node_id2iid):
    clusters_by_id = defaultdict(list)
    for u, c in node2com.items():
        clusters_by_id[c].append(u)

    mcs = []
    for c, _ in comm_size_sorted:
        c_nodes_str = clusters_by_id[c]

        if len(c_nodes_str) <= 1:
            mcs.append([0])
            continue

        c_nodes_iid = [node_id2iid[u] for u in c_nodes_str]
        c_nodes_set = set(c_nodes_iid)
        c_edges = []

        for u in c_nodes_str:
            u_iid = node_id2iid[u]
            for v in neighbors[u]:
                v_iid = node_id2iid.get(v)
                if v_iid is not None and v_iid in c_nodes_set:
                    c_edges.append((u_iid, v_iid))

        sub_G = PyGraph(c_nodes_iid, c_edges)
        min_cut = sub_G.mincut("noi", "bqueue", False)[2]
        mcs.append([min_cut])

    return mcs


def export_mincut(out_dir, mcs):
    pd.DataFrame(mcs).to_csv(f"{out_dir}/mincut.csv", index=False, header=False)


def compute_mixing_parameter(nodes, neighbors, node2com, generator_type):
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)

    for u in nodes:
        u_clustered = u in node2com
        for v in neighbors[u]:
            v_clustered = v in node2com

            if not u_clustered and not v_clustered:
                if generator_type == "abcd+o":
                    out_degree[u] += 1
                continue

            elif not u_clustered or not v_clustered:
                out_degree[u] += 1
                continue

            if node2com[u] == node2com[v]:
                in_degree[u] += 1
            else:
                out_degree[u] += 1

    if generator_type == "lfr":
        mus = [
            (
                out_degree[i] / (in_degree[i] + out_degree[i])
                if (in_degree[i] + out_degree[i]) > 0
                else 0
            )
            for i in nodes
        ]
        return np.mean(mus)
    else:
        outs_sum = sum(out_degree[i] for i in nodes)
        total_sum = sum(in_degree[i] + out_degree[i] for i in nodes)
        return outs_sum / total_sum if total_sum > 0 else 0


def export_comm_size(out_dir, comm_size_sorted):
    pd.DataFrame([size for _, size in comm_size_sorted]).to_csv(
        f"{out_dir}/cluster_sizes.csv", index=False, header=False
    )


def export_mixing_param(out_dir, mixing_param):
    with open(f"{out_dir}/mixing_parameter.txt", "w") as f:
        f.write(str(mixing_param))


def setup_generator_inputs(edgelist_path, clustering_path, output_dir, generator):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    setup_logging(Path(output_dir) / "run.log")

    # 1. Read Inputs
    start = time.perf_counter()
    nodes, node2com, cluster_counts = read_clustering(clustering_path)
    nodes, neighbors = read_edgelist(edgelist_path, nodes)
    logging.info(f"Input reading elapsed: {time.perf_counter() - start:.4f} seconds")

    # 2. Compute Mappings
    start = time.perf_counter()
    node_deg_sorted, node_id2iid = compute_node_degree(nodes, neighbors)
    comm_size_sorted, cluster_id2iid = compute_comm_size(cluster_counts)
    logging.info(
        f"Mappings computation elapsed: {time.perf_counter() - start:.4f} seconds"
    )

    # 3. Export Core Outputs
    start = time.perf_counter()
    export_node_id(output_dir, node_deg_sorted)
    export_cluster_id(output_dir, comm_size_sorted)
    export_assignment(output_dir, node_deg_sorted, node2com, cluster_id2iid)
    export_degree(output_dir, node_deg_sorted)
    logging.info(
        f"Core outputs export elapsed: {time.perf_counter() - start:.4f} seconds"
    )

    # 4. Generator-Specific Flows
    start = time.perf_counter()
    if generator in ["sbm", "ecsbm"]:
        edge_counts = compute_edge_count(nodes, neighbors, node2com, cluster_id2iid)
        export_edge_count(output_dir, edge_counts)

    if generator == "ecsbm":
        mcs = compute_mincut(nodes, neighbors, node2com, comm_size_sorted, node_id2iid)
        export_mincut(output_dir, mcs)

    if generator in ["lfr", "abcd", "abcd+o"]:
        export_comm_size(output_dir, comm_size_sorted)
        mixing_param = compute_mixing_parameter(nodes, neighbors, node2com, generator)
        export_mixing_param(output_dir, mixing_param)

    logging.info(
        f"Generator-specific outputs export elapsed: {time.perf_counter() - start:.4f} seconds"
    )
    logging.info("Setup complete.")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--edgelist", type=str, required=True)
    parser.add_argument("--clustering", type=str, required=True)
    parser.add_argument("--output-folder", type=str, required=True)
    parser.add_argument(
        "--generator",
        type=str,
        default="ecsbm",
        choices=["sbm", "lfr", "abcd", "abcd+o", "ecsbm"],
    )
    return parser.parse_args()


def main():
    args = parse_args()
    setup_generator_inputs(
        args.edgelist, args.clustering, args.output_folder, args.generator
    )


if __name__ == "__main__":
    main()
