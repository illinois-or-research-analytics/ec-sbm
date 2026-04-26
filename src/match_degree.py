"""Generator-agnostic match-degree stage, with optional --remap mode.

Given an input edgelist (current pipeline output) and a reference
edgelist (defining the target per-node degree), add edges to minimize
the residual degree deficit. Five algorithms:

  - greedy        : heap, static candidate set, `set.pop()` partners (silent gridlock)
  - true_greedy   : heap, dynamic re-push; logs gridlock
  - random_greedy : weighted-random u, weighted-random v
  - rewire        : configuration-model pairing + 2-opt rewire
  - hybrid        : rewire → true_greedy fallback on stuck stubs (default)

Two target-degree modes:

  - Default: target_deg[node] = count of that node's edges in --ref-edgelist.
    Requires input and ref to share a node-ID space (ec-sbm case).

  - --remap: input IDs may not align with ref IDs (abcd / abcd+o / lfr /
    npso). Sort both input and ref node sets by descending degree, pair
    rank-by-rank (rearrangement inequality → L1- and L2-optimal pairing),
    and look up target_deg[input_node] = ref_deg[rank-paired-ref-node].
    The algorithm runs entirely in the input's ID space; match-degree
    edges are emitted in that space. No edges or cluster assignments are
    rewritten on disk.

Output: `degree_matching_edge.csv` with columns (source, target), keyed
by the input edgelist's ID space.
"""
import argparse
import logging
import heapq
import random
from collections import deque

import numpy as np
import pandas as pd

from pipeline_common import standard_setup, timed
from graph_utils import normalize_edge, run_rewire_attempts


def parse_args():
    parser = argparse.ArgumentParser(description="Degree Matching")
    parser.add_argument("--input-edgelist", type=str, required=True)
    parser.add_argument("--ref-edgelist", type=str, required=True)
    parser.add_argument("--output-folder", type=str, required=True)
    parser.add_argument("--remap", action="store_true",
                        help="Pair input node IDs to ref node IDs by "
                             "descending-degree rank instead of assuming a "
                             "shared ID space. Target degree per input node is "
                             "the ref degree of its rank-paired ref node. "
                             "Top-up edges stay in the input's ID space.")
    parser.add_argument(
        "--match-degree-algorithm", dest="match_degree_algorithm", type=str,
        choices=["greedy", "true_greedy", "random_greedy", "rewire", "hybrid"],
        default="hybrid",
    )
    parser.add_argument("--seed", type=int, default=1)
    return parser.parse_args()


def load_reference_topologies(orig_edgelist_fp, input_edgelist_fp=None):
    """Direct-ID mode: node_id2iid + out_degs keyed by ref IDs.

    If an input edgelist path is given, its endpoints are unioned into the
    node set so nodes that are present in the input edgelist but isolated
    in the ref edgelist stay tracked. Such nodes get target degree 0;
    their stage-2 edges still decrement their partners' residuals.
    """
    df_orig_edges = pd.read_csv(orig_edgelist_fp, dtype=str)

    all_orig_nodes = (
        set(df_orig_edges["source"])
        .union(set(df_orig_edges["target"]))
    )
    if input_edgelist_fp is not None:
        df_in = pd.read_csv(input_edgelist_fp, dtype=str)
        all_orig_nodes = all_orig_nodes.union(
            set(df_in["source"]).union(set(df_in["target"]))
        )

    node_id2iid = {u: i for i, u in enumerate(sorted(all_orig_nodes))}
    node_iid2id = {i: u for u, i in node_id2iid.items()}
    out_degs = {iid: 0 for iid in node_iid2id.keys()}

    for src, tgt in zip(df_orig_edges["source"], df_orig_edges["target"]):
        out_degs[node_id2iid[src]] += 1
        out_degs[node_id2iid[tgt]] += 1

    return node_id2iid, node_iid2id, out_degs


def load_remap_topologies(input_edgelist_fp, ref_edgelist_fp):
    """Remap mode: node_id2iid keyed by INPUT IDs; target degrees come from
    pairing input and ref nodes rank-by-rank on descending degree.
    """
    in_df = pd.read_csv(input_edgelist_fp, dtype=str)
    ref_df = pd.read_csv(ref_edgelist_fp, dtype=str)

    in_endpoints = pd.concat([in_df["source"], in_df["target"]], ignore_index=True)
    ref_endpoints = pd.concat([ref_df["source"], ref_df["target"]], ignore_index=True)

    in_deg_series = in_endpoints.value_counts()
    ref_deg_series = ref_endpoints.value_counts()

    in_nodes = sorted(in_deg_series.index, key=lambda n: (-int(in_deg_series[n]), n))
    ref_nodes = sorted(ref_deg_series.index, key=lambda n: (-int(ref_deg_series[n]), n))

    if len(in_nodes) != len(ref_nodes):
        logging.warning(
            f"Remap: |input nodes|={len(in_nodes)} vs |ref nodes|={len(ref_nodes)}; "
            f"pairing first {min(len(in_nodes), len(ref_nodes))} ranks, dropping excess."
        )

    n_pair = min(len(in_nodes), len(ref_nodes))
    node_id2iid = {u: i for i, u in enumerate(in_nodes[:n_pair])}
    node_iid2id = {i: u for u, i in node_id2iid.items()}

    out_degs = {
        node_id2iid[in_nodes[i]]: int(ref_deg_series[ref_nodes[i]])
        for i in range(n_pair)
    }
    return node_id2iid, node_iid2id, out_degs


def subtract_existing_edges(exist_edgelist_fp, node_id2iid, out_degs):
    df_exist_edges = pd.read_csv(exist_edgelist_fp, dtype=str)
    exist_neighbor = {iid: set() for iid in node_id2iid.values()}

    for src, tgt in zip(df_exist_edges["source"], df_exist_edges["target"]):
        src_iid, tgt_iid = node_id2iid[src], node_id2iid[tgt]
        if tgt_iid in exist_neighbor[src_iid]:
            continue

        exist_neighbor[src_iid].add(tgt_iid)
        exist_neighbor[tgt_iid].add(src_iid)

        out_degs[src_iid] = max(0, out_degs[src_iid] - 1)
        out_degs[tgt_iid] = max(0, out_degs[tgt_iid] - 1)

    return exist_neighbor, out_degs


def match_missing_degrees_random_greedy(out_degs, exist_neighbor):
    logging.info("Starting Randomized Greedy matching algorithm...")

    available_degrees = {k: v for k, v in sorted(out_degs.items()) if v > 0}
    available_nodes = list(available_degrees.keys())

    initial_missing_stubs = sum(available_degrees.values())
    logging.info(
        f"Initial missing stubs: {initial_missing_stubs} (Target edges: {initial_missing_stubs // 2})"
    )

    degree_edges = set()
    stuck_nodes = set()

    while available_nodes:
        weights = [available_degrees[n] for n in available_nodes]
        u = random.choices(available_nodes, weights=weights, k=1)[0]

        invalid_targets = exist_neighbor.get(u, set())
        valid_targets = [
            n for n in available_nodes if n != u and n not in invalid_targets
        ]

        if not valid_targets:
            available_nodes.remove(u)
            stuck_nodes.add(u)
            continue

        v_weights = [available_degrees[n] for n in valid_targets]
        v = random.choices(valid_targets, weights=v_weights, k=1)[0]

        degree_edges.add((min(u, v), max(u, v)))
        exist_neighbor[u].add(v)
        exist_neighbor[v].add(u)

        available_degrees[u] -= 1
        available_degrees[v] -= 1

        if available_degrees[u] == 0:
            available_nodes.remove(u)
        if available_degrees[v] == 0:
            available_nodes.remove(v)

    if stuck_nodes:
        stuck_stubs = sum(available_degrees[n] for n in stuck_nodes)
        logging.warning(
            f"Finished with {len(stuck_nodes)} physically gridlocked nodes. {stuck_stubs} missing stubs dropped."
        )

    return degree_edges


def match_missing_degrees_greedy(out_degs, exist_neighbor):
    logging.info("Starting Original Greedy matching algorithm...")
    available_node_set = {node_iid for node_iid, deg in out_degs.items() if deg > 0}
    available_node_degrees = {
        node_iid: deg for node_iid, deg in out_degs.items() if deg > 0
    }

    initial_missing_stubs = sum(available_node_degrees.values())
    logging.info(f"Initial missing stubs: {initial_missing_stubs}")

    max_heap = [(-degree, node) for node, degree in available_node_degrees.items()]
    heapq.heapify(max_heap)

    degree_edges = set()

    while max_heap:
        _, available_c_node = heapq.heappop(max_heap)

        if available_c_node not in available_node_degrees:
            continue

        invalid_targets = exist_neighbor.get(available_c_node, set()).copy()
        invalid_targets.add(available_c_node)
        available_non_neighbors = available_node_set - invalid_targets

        avail_k = min(
            available_node_degrees[available_c_node], len(available_non_neighbors)
        )

        # `set.pop()` returns hash-slot order; pick the smallest id instead so
        # the algorithm is deterministic across PYTHONHASHSEED values and
        # matches the JS port at vltanh.github.io/netgen/matcher.html.
        sorted_non_neighbors = sorted(available_non_neighbors)
        for k in range(avail_k):
            edge_end = sorted_non_neighbors[k]
            degree_edges.add((available_c_node, edge_end))

            exist_neighbor[available_c_node].add(edge_end)
            exist_neighbor[edge_end].add(available_c_node)

            available_node_degrees[edge_end] -= 1
            if available_node_degrees[edge_end] == 0:
                available_node_set.remove(edge_end)
                del available_node_degrees[edge_end]

        del available_node_degrees[available_c_node]
        available_node_set.remove(available_c_node)

    return degree_edges


def match_missing_degrees_true_greedy(out_degs, exist_neighbor):
    logging.info("Starting True Dynamic Greedy matching algorithm...")

    current_degrees = {n: d for n, d in out_degs.items() if d > 0}

    initial_missing_stubs = sum(current_degrees.values())
    logging.info(
        f"Initial missing stubs: {initial_missing_stubs} (Target edges: {initial_missing_stubs // 2})"
    )

    heap = [(-deg, n) for n, deg in current_degrees.items()]
    heapq.heapify(heap)

    degree_edges = set()
    stuck_nodes = set()

    while heap:
        neg_deg, u = heapq.heappop(heap)
        deg_u = -neg_deg

        # Lazy deletion: skip stale heap entries.
        if u not in current_degrees or deg_u != current_degrees[u]:
            continue

        invalid_targets = exist_neighbor.get(u, set())
        valid_targets = [
            n for n in current_degrees if n != u and n not in invalid_targets
        ]

        if not valid_targets:
            stuck_nodes.add(u)
            del current_degrees[u]
            continue

        # Tie-break on id ascending so the choice is deterministic across
        # dict-iteration order and matches the JS port.
        v = max(valid_targets, key=lambda x: (current_degrees[x], -x))

        degree_edges.add((min(u, v), max(u, v)))
        exist_neighbor[u].add(v)
        exist_neighbor[v].add(u)

        current_degrees[u] -= 1
        current_degrees[v] -= 1

        if current_degrees[u] > 0:
            heapq.heappush(heap, (-current_degrees[u], u))
        else:
            del current_degrees[u]

        if current_degrees[v] > 0:
            heapq.heappush(heap, (-current_degrees[v], v))
        elif v in current_degrees:
            del current_degrees[v]

    if stuck_nodes:
        stuck_stubs = sum(out_degs[n] for n in stuck_nodes) - sum(
            current_degrees.get(n, 0) for n in stuck_nodes
        )
        logging.warning(f"Finished with {len(stuck_nodes)} gridlocked nodes.")

    return degree_edges


def match_missing_degrees_rewire(out_degs, exist_neighbor, max_retries=10):
    """Configuration-model pairing + 2-opt rewire for conflicts.

    Returns (valid_edges, invalid_edges). Self-loops, duplicates, and
    pre-existing neighbors are queued for rewiring; hybrid caller falls
    back to true-greedy on whatever remains invalid.
    """
    logging.info("Starting Rewire (Configuration Model) matching algorithm...")

    stubs = []
    for node_iid, deg in sorted(out_degs.items()):
        stubs.extend([node_iid] * int(deg))

    if len(stubs) % 2 != 0:
        logging.warning(
            "Odd number of total missing stubs. Dropping one to maintain parity."
        )
        stubs.pop()

    logging.info(
        f"Total missing stubs to pair: {len(stubs)} (Target edges: {len(stubs)//2})"
    )
    random.shuffle(stubs)

    valid_edges = set()
    invalid_edges = deque()

    for i in range(0, len(stubs), 2):
        u, v = stubs[i], stubs[i + 1]
        e = normalize_edge(u, v)

        if u == v or e in valid_edges or v in exist_neighbor.get(u, set()):
            invalid_edges.append(e)
        else:
            valid_edges.add(e)

    logging.info(
        f"Initial pairing complete -> Valid edges: {len(valid_edges)} | Bad edges to rewire: {len(invalid_edges)}"
    )

    valid_pool = sorted(valid_edges)

    def is_valid(e):
        u, v = e
        return u != v and e not in valid_edges and v not in exist_neighbor.get(u, set())

    def process_one_edge(e1, invalid_edges):
        """2-opt swap e1 against a random valid edge. Returns True to break outer pass."""
        if not valid_pool:
            invalid_edges.append(e1)
            return True

        idx = random.randrange(len(valid_pool))
        e2 = valid_pool[idx]

        if random.random() < 0.5:
            new_e1 = normalize_edge(e1[0], e2[0])
            new_e2 = normalize_edge(e1[1], e2[1])
        else:
            new_e1 = normalize_edge(e1[0], e2[1])
            new_e2 = normalize_edge(e1[1], e2[0])

        if is_valid(new_e1) and is_valid(new_e2) and new_e1 != new_e2:
            valid_edges.remove(e2)
            valid_pool[idx] = valid_pool[-1]
            valid_pool.pop()

            valid_edges.add(new_e1)
            valid_edges.add(new_e2)
            valid_pool.append(new_e1)
            valid_pool.append(new_e2)
        else:
            invalid_edges.append(e1)

        return False

    run_rewire_attempts(invalid_edges, process_one_edge, max_retries)
    if invalid_edges:
        logging.warning(
            f"Finished {max_retries} retries. {len(invalid_edges)} bad edges remain unresolved."
        )
    return valid_edges, list(invalid_edges)


def match_missing_degrees_hybrid(out_degs, exist_neighbor):
    logging.info("Starting Hybrid (Rewire -> True Greedy) matching algorithm...")

    valid_edges, invalid_edges = match_missing_degrees_rewire(
        out_degs, exist_neighbor, max_retries=10
    )

    if not invalid_edges:
        return valid_edges

    logging.info(
        f"Hybrid transition: Passing {len(invalid_edges)} gridlocked edges "
        f"({len(invalid_edges) * 2} stubs) to True Greedy deterministic fallback."
    )

    remaining_out_degs = {n: 0 for n in sorted(out_degs.keys())}
    for u, v in invalid_edges:
        remaining_out_degs[u] += 1
        remaining_out_degs[v] += 1

    remaining_out_degs = {n: d for n, d in remaining_out_degs.items() if d > 0}

    for u, v in valid_edges:
        exist_neighbor[u].add(v)
        exist_neighbor[v].add(u)

    greedy_edges = match_missing_degrees_true_greedy(remaining_out_degs, exist_neighbor)

    return valid_edges.union(greedy_edges)


def export_degree_matched_edgelist(degree_edges, node_iid2id, output_dir):
    df_out = pd.DataFrame(
        [(node_iid2id[src], node_iid2id[tgt]) for src, tgt in degree_edges],
        columns=["source", "target"],
    )
    df_out.to_csv(output_dir / "degree_matching_edge.csv", index=False)


def main():
    args = parse_args()
    out_dir = standard_setup(args.output_folder)

    random.seed(args.seed)
    np.random.seed(args.seed)

    logging.info(
        f"--- Starting Degree Matching ({args.match_degree_algorithm.upper()}"
        f"{' + remap' if args.remap else ''} mode) ---"
    )

    if args.remap:
        with timed("Loaded rank-paired target degrees"):
            node_id2iid, node_iid2id, out_degs = load_remap_topologies(
                args.input_edgelist, args.ref_edgelist
            )
    else:
        with timed("Loaded reference topologies"):
            node_id2iid, node_iid2id, out_degs = load_reference_topologies(
                args.ref_edgelist, args.input_edgelist
            )

    with timed("Subtracted existing edges"):
        exist_neighbor, updated_out_degs = subtract_existing_edges(
            args.input_edgelist, node_id2iid, out_degs
        )

    with timed("Degree matching"):
        if args.match_degree_algorithm == "greedy":
            degree_edges = match_missing_degrees_greedy(updated_out_degs, exist_neighbor)
        elif args.match_degree_algorithm == "true_greedy":
            degree_edges = match_missing_degrees_true_greedy(
                updated_out_degs, exist_neighbor
            )
        elif args.match_degree_algorithm == "random_greedy":
            degree_edges = match_missing_degrees_random_greedy(
                updated_out_degs, exist_neighbor
            )
        elif args.match_degree_algorithm == "rewire":
            degree_edges, _ = match_missing_degrees_rewire(
                updated_out_degs, exist_neighbor, max_retries=10
            )
        elif args.match_degree_algorithm == "hybrid":
            degree_edges = match_missing_degrees_hybrid(updated_out_degs, exist_neighbor)
        else:
            logging.error(f"Unknown algorithm choice: {args.match_degree_algorithm}")
            return

        logging.info(f"Added {len(degree_edges)} edges")

    with timed("Exported edgelist"):
        export_degree_matched_edgelist(degree_edges, node_iid2id, out_dir)


if __name__ == "__main__":
    main()
