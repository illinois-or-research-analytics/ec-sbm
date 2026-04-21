"""Shared pipeline helpers: logging, timing, CSV writers, probs loader."""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from pathlib import Path

import pandas as pd


def setup_logging(log_filepath: Path):
    """Route root logger to `log_filepath` with timestamps; no console output."""
    log_filepath.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_filepath, mode="w")
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)


def standard_setup(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(output_dir / "run.log")
    return output_dir


@contextmanager
def timed(label):
    start = time.perf_counter()
    yield
    logging.info(f"{label} elapsed: {time.perf_counter() - start:.4f} seconds")


def write_edge_tuples_csv(path, edges, node_iid2id=None):
    if node_iid2id is None:
        rows = [(int(s), int(t)) for s, t in edges]
    else:
        rows = [(node_iid2id[int(s)], node_iid2id[int(t)]) for s, t in edges]
    pd.DataFrame(rows, columns=["source", "target"]).to_csv(path, index=False)


def load_probs_matrix(edge_counts_path, num_clusters):
    """Load (r, c, w) edge-counts CSV into a num_clusters² dok_matrix.
    Empty file → zero matrix.
    """
    from scipy.sparse import dok_matrix

    probs = dok_matrix((num_clusters, num_clusters), dtype=int)
    try:
        df = pd.read_csv(edge_counts_path, header=None, names=["r", "c", "w"])
    except pd.errors.EmptyDataError:
        logging.warning(
            f"Edge counts file ({edge_counts_path}) is empty. "
            "Assuming completely disconnected clusters."
        )
        return probs
    for _, row in df.iterrows():
        probs[int(row["r"]), int(row["c"])] = int(row["w"])
    return probs
