"""Generator-agnostic graph primitives.

Shared between ec-sbm's constructive core / block-preserving rewire and the
top-level degree-matching tool.
"""
import logging


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
