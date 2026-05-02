"""Generator-agnostic graph primitives.

Shared between ec-sbm's constructive core / block-preserving rewire and the
top-level degree-matching tool.
"""
import logging
import random


def normalize_edge(u, v):
    return (min(u, v), max(u, v))


def run_rewire_attempts(invalid_edges, process_one_edge, max_retries=10):
    """Retry loop for 2-opt edge rewiring.

    Stagnation (deque size unchanged after a full pass) ends the inner loop.
    Callback must re-append `e` if unresolved; return True to break early.
    """
    for attempt in range(max_retries):
        if not invalid_edges:
            logging.info("All bad edges resolved! Exiting rewiring loop early.")
            break

        last_recycle = len(invalid_edges)
        recycle_counter = last_recycle

        while invalid_edges:
            recycle_counter -= 1
            if recycle_counter < 0:
                if len(invalid_edges) < last_recycle:
                    last_recycle = len(invalid_edges)
                    recycle_counter = last_recycle
                else:
                    break

            e = invalid_edges.popleft()
            if process_one_edge(e, invalid_edges):
                break

        logging.info(
            f"After attempt {attempt + 1}: {len(invalid_edges)} bad edges remain."
        )


def cluster_preserving_2opt_rewire(invalid_edges, valid_pool, b, max_retries=10):
    """2-opt block-preserving rewire of self-loops and duplicates.

    Lifts the rewire body of ``gen_outlier.rewire_invalid_edges`` so degree
    matchers can reuse the same per-bp 2-opt swap.

    Args:
        invalid_edges: deque of ``(u_iid, v_iid)`` raw pairs needing fixup.
        valid_pool: defaultdict-like keyed by ``(min_block, max_block)``;
            values are lists of normalized edges currently accepted.
        b: array, block assignment per node iid.
        max_retries: passes over ``invalid_edges``.

    Returns:
        ``(sbm_only_sorted, rewired_sorted)`` — partition of the final valid
        edges into pre-swap survivors vs swap-introduced edges.
    """
    valid_set = set()
    for pool in valid_pool.values():
        valid_set.update(pool)
    initial_valid_set = frozenset(valid_set)

    logging.info(f"Initial bad edges before rewiring: {len(invalid_edges)}")

    def get_bp(u, v):
        return (int(min(b[u], b[v])), int(max(b[u], b[v])))

    def process_one_edge(raw_edge, invalid_edges):
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
            f"Finished {max_retries} retries. {len(invalid_edges)} bad edges "
            "remain unresolved and will be dropped."
        )
    sbm_only = sorted(valid_set & initial_valid_set)
    rewired = sorted(valid_set - initial_valid_set)
    return sbm_only, rewired
