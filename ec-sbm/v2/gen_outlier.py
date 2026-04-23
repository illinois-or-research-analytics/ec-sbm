import random
import logging
import argparse
from collections import defaultdict, deque

import numpy as np
import pandas as pd
import graph_tool.all as gt
from scipy.sparse import dok_matrix

from pipeline_common import standard_setup, timed, write_edge_tuples_csv
from params_common import read_params, resolve_param
from graph_utils import normalize_edge, run_rewire_attempts

# Gen-outlier's default is independent of the profile stage.
DEFAULT_OUTLIER_MODE = "combined"


def load_network_data(orig_edgelist_fp, orig_clustering_fp, exist_edgelist_fp):
    df_orig = pd.read_csv(orig_edgelist_fp, dtype=str)
    df_clust = pd.read_csv(orig_clustering_fp, dtype=str)

    try:
        df_exist = pd.read_csv(exist_edgelist_fp, dtype=str)
    except pd.errors.EmptyDataError:
        df_exist = pd.DataFrame(columns=["source", "target"])

    node2cluster_str = dict(zip(df_clust["node_id"], df_clust["cluster_id"]))

    all_nodes = set(df_orig["source"]).union(set(df_orig["target"]))
    outliers = all_nodes - set(node2cluster_str.keys())

    return df_orig, df_exist, node2cluster_str, all_nodes, outliers


def prepare_residual_sbm_inputs(
    df_orig, df_exist, node2cluster_str, all_nodes, outliers, outlier_mode
):
    node_id2iid = {u: i for i, u in enumerate(all_nodes)}
    node_iid2id = {i: u for u, i in node_id2iid.items()}

    unique_clusters = set(node2cluster_str.values())
    cluster_id2iid = {c: i for i, c in enumerate(unique_clusters)}

    b = np.empty(len(all_nodes), dtype=int)
    current_c_iid = len(cluster_id2iid)

    if outliers and outlier_mode == "combined":
        combined_block = current_c_iid
        current_c_iid += 1

    for u in all_nodes:
        u_iid = node_id2iid[u]
        if u in outliers:
            if outlier_mode == "combined":
                b[u_iid] = combined_block
            else:
                b[u_iid] = current_c_iid
                current_c_iid += 1
        else:
            b[u_iid] = cluster_id2iid[node2cluster_str[u]]

    num_clusters = current_c_iid
    num_nodes = len(all_nodes)

    out_degs = np.zeros(num_nodes, dtype=int)

    u_orig = np.where(
        df_orig["source"] < df_orig["target"], df_orig["source"], df_orig["target"]
    )
    v_orig = np.where(
        df_orig["source"] > df_orig["target"], df_orig["source"], df_orig["target"]
    )
    df_orig_dedup = pd.DataFrame({"u": u_orig, "v": v_orig}).drop_duplicates()

    for u_id, v_id in zip(df_orig_dedup["u"], df_orig_dedup["v"]):
        u, v = node_id2iid[u_id], node_id2iid[v_id]
        out_degs[u] += 1
        out_degs[v] += 1

    if not df_exist.empty:
        u_ext = np.where(
            df_exist["source"] < df_exist["target"],
            df_exist["source"],
            df_exist["target"],
        )
        v_ext = np.where(
            df_exist["source"] > df_exist["target"],
            df_exist["source"],
            df_exist["target"],
        )
        df_exist_dedup = pd.DataFrame({"u": u_ext, "v": v_ext}).drop_duplicates()

        for u_id, v_id in zip(df_exist_dedup["u"], df_exist_dedup["v"]):
            if u_id not in node_id2iid or v_id not in node_id2iid:
                continue
            u, v = node_id2iid[u_id], node_id2iid[v_id]
            out_degs[u] = max(0, out_degs[u] - 1)
            out_degs[v] = max(0, out_degs[v] - 1)

    probs = dok_matrix((num_clusters, num_clusters), dtype=int)

    for u_id, v_id in zip(df_orig_dedup["u"], df_orig_dedup["v"]):
        u, v = node_id2iid[u_id], node_id2iid[v_id]
        b_u, b_v = b[u], b[v]
        if b_u != b_v:
            probs[b_u, b_v] += 1
            probs[b_v, b_u] += 1

    probs_csr = probs.tocsr()
    row_sums = np.array(probs_csr.sum(axis=1)).flatten()

    for k in range(num_clusters):
        nodes_in_k = np.where(b == k)[0]
        if len(nodes_in_k) == 0:
            continue

        D_k = np.sum(out_degs[nodes_in_k])
        E_inter_k = row_sums[k]
        diff = D_k - E_inter_k

        if diff < 0:
            deficit = abs(diff)
            for i in range(deficit):
                out_degs[nodes_in_k[i % len(nodes_in_k)]] += 1
            probs[k, k] = 0
        else:
            probs[k, k] = diff
            if probs[k, k] % 2 != 0:
                probs[k, k] += 1
                out_degs[nodes_in_k[0]] += 1

    return b, probs.tocsr(), out_degs, node_iid2id


def rewire_invalid_edges(g, b, max_retries=10):
    """2-opt block-preserving rewiring of self-loops/multi-edges.

    Groups edges by (min_block, max_block) pair; swaps within a pair so each
    endpoint stays in its original block. Unresolved after max_retries are dropped.
    """
    edges = g.get_edges()
    valid_pool = defaultdict(list)
    valid_set = set()
    invalid_edges = deque()

    def get_bp(u, v):
        return (int(min(b[u], b[v])), int(max(b[u], b[v])))

    for u, v in edges:
        e = normalize_edge(u, v)
        if u == v or e in valid_set:
            invalid_edges.append((u, v))
        else:
            bp = get_bp(u, v)
            valid_set.add(e)
            valid_pool[bp].append(e)

    logging.info(f"Initial bad edges before rewiring: {len(invalid_edges)}")

    def process_one_edge(raw_edge, invalid_edges):
        """2-opt block-preserving swap for raw_edge. Returns False (always continue)."""
        u, v = raw_edge
        bp = get_bp(u, v)
        pool = valid_pool[bp]

        if not pool:
            invalid_edges.append((u, v))
            return False

        idx = random.randrange(len(pool))
        x, y = pool[idx]
        A, B = bp

        if A != B:
            u_A = u if b[u] == A else v
            u_B = v if b[u] == A else u
            x_A = x if b[x] == A else y
            x_B = y if b[x] == A else x
            new_e1, new_e2 = normalize_edge(u_A, x_B), normalize_edge(x_A, u_B)
        else:
            if random.random() < 0.5:
                new_e1, new_e2 = normalize_edge(u, x), normalize_edge(v, y)
            else:
                new_e1, new_e2 = normalize_edge(u, y), normalize_edge(v, x)

        if (
            new_e1[0] != new_e1[1]
            and new_e2[0] != new_e2[1]
            and new_e1 not in valid_set
            and new_e2 not in valid_set
            and new_e1 != new_e2
        ):
            valid_set.remove(normalize_edge(x, y))
            pool[idx] = pool[-1]
            pool.pop()

            valid_set.add(new_e1)
            valid_set.add(new_e2)
            pool.append(new_e1)
            pool.append(new_e2)
        else:
            invalid_edges.append((u, v))

        return False

    run_rewire_attempts(invalid_edges, process_one_edge, max_retries)
    if invalid_edges:
        logging.warning(
            f"Finished {max_retries} retries. {len(invalid_edges)} bad edges remain unresolved and will be dropped."
        )
    return list(valid_set)


def generate_residual_subnetwork(b, probs, out_degs, edge_correction_mode):
    if out_degs.sum() > 0:
        g = gt.generate_sbm(
            b,
            probs,
            out_degs=out_degs,
            micro_ers=True,
            micro_degs=True,
            directed=False,
        )
    else:
        g = gt.Graph(directed=False)

    if edge_correction_mode == "rewire":
        valid_edges = rewire_invalid_edges(g, b, max_retries=10)
        g.clear_edges()
        g.add_edge_list(valid_edges)

    gt.remove_parallel_edges(g)
    gt.remove_self_loops(g)

    return [(int(src), int(tgt)) for src, tgt in g.iter_edges()]


def export_generated_edges(edges, node_iid2id, output_dir):
    write_edge_tuples_csv(output_dir / "edge_outlier.csv", edges, node_iid2id)


def run_outlier_generation(
    orig_edgelist_fp,
    orig_clustering_fp,
    exist_edgelist_fp,
    outlier_mode,
    edge_correction_mode,
    output_folder,
    seed,
):
    output_dir = standard_setup(output_folder)

    random.seed(seed)
    np.random.seed(seed)
    gt.seed_rng(seed)

    logging.info("Starting Residual SBM Generation...")
    logging.info(
        f"Correction Mode: {edge_correction_mode} | Outlier Mode: {outlier_mode}"
    )

    with timed("Setup"):
        df_orig, df_exist, node2cluster_str, all_nodes, outliers = load_network_data(
            orig_edgelist_fp, orig_clustering_fp, exist_edgelist_fp
        )
        b, probs, out_degs, node_iid2id = prepare_residual_sbm_inputs(
            df_orig, df_exist, node2cluster_str, all_nodes, outliers, outlier_mode
        )

    with timed("Generation of residual subgraph"):
        edges = generate_residual_subnetwork(b, probs, out_degs, edge_correction_mode)

    with timed("Export"):
        export_generated_edges(edges, node_iid2id, output_dir)

    logging.info("Complete.")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orig-edgelist", type=str, required=True)
    parser.add_argument("--orig-clustering", type=str, required=True)
    parser.add_argument("--exist-edgelist", type=str, required=True)
    parser.add_argument(
        "--outlier-mode",
        type=str,
        choices=["combined", "singleton"],
        default=None,
        help="'combined' folds outliers into one block; 'singleton' one block each.",
    )
    parser.add_argument("--params-file", type=str, default=None)
    parser.add_argument(
        "--edge-correction",
        type=str,
        choices=["drop", "rewire"],
        default="rewire",
        help="'drop' removes bad edges (alters degree); 'rewire' swaps them (preserves degree).",
    )
    parser.add_argument("--output-folder", type=str, required=True)
    parser.add_argument("--seed", type=int, default=1)
    return parser.parse_args()


def main():
    args = parse_args()
    file_params = read_params(args.params_file) if args.params_file else None
    outlier_mode = resolve_param(
        args.outlier_mode, file_params, "outlier_mode",
        default=DEFAULT_OUTLIER_MODE,
    )
    if outlier_mode == "excluded":
        raise SystemExit(
            "gen_outlier does not support outlier_mode=excluded (no outlier edges to generate)."
        )
    run_outlier_generation(
        args.orig_edgelist,
        args.orig_clustering,
        args.exist_edgelist,
        outlier_mode,
        args.edge_correction,
        args.output_folder,
        args.seed,
    )


if __name__ == "__main__":
    main()
