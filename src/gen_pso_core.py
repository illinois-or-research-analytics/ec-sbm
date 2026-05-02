"""Single-cluster PSO subgraph (uniform angular distribution).

Python port of the PSO branch of ``externals/npso/nPSO_model.m`` (i.e. the
``distr == 0`` case). Used by ec-sbm v3 to build per-cluster intra-cluster
subgraphs with a tunable temperature ``T`` knob.

The construction is k-edge-connected by design: when ``m == k`` the first
``k+1`` nodes are connected by the "connect to all existing" branch (a
``K_{k+1}`` clique, which is k-edge-connected), and every subsequent node
attaches to exactly ``m`` existing nodes (so adding it cannot drop the
mincut below ``k``).

This module is self-contained: it does not depend on MATLAB, and is not
byte-equivalent to ``nPSO_model.m`` (different RNG). It is deterministic
given a NumPy seed.
"""
from __future__ import annotations

import math
import numpy as np


def hyperbolic_dist(theta_i, r_i, thetas_j, rs_j):
    """Pairwise hyperbolic distance from one point ``(theta_i, r_i)`` to a
    vector of points ``(thetas_j, rs_j)``.

    Mirrors ``hyperbolic_dist`` from ``nPSO_model.m``: angular distance is
    ``Tij = pi - |pi - |Ti - Tj||``; distance is
    ``arccosh(cosh(Ri)cosh(Rj) - sinh(Ri)sinh(Rj)cos(Tij))``.

    Numerical safety: clip the cosh argument at >= 1 to avoid NaN from
    arccosh(<1) when the analytic value should be exactly 0.
    """
    A = math.pi - np.abs(math.pi - np.abs(theta_i - thetas_j))
    arg = np.cosh(r_i) * np.cosh(rs_j) - np.sinh(r_i) * np.sinh(rs_j) * np.cos(A)
    arg = np.maximum(arg, 1.0)
    return np.arccosh(arg)


def _weighted_sample_without_replacement(weights, k, rng):
    """Efraimidis-Spirakis: pick the ``k`` indices with the smallest
    ``-log(U) / w`` keys. Equivalent in distribution to MATLAB's
    ``datasample(... 'Replace', false, 'Weights', w)``.

    Inputs with non-positive weight are skipped; if fewer than ``k`` valid
    candidates remain, all of them are returned (fallback behaviour for
    extreme T or near-zero probabilities).
    """
    w = np.asarray(weights, dtype=np.float64)
    pos = w > 0
    n_pos = int(pos.sum())
    if n_pos == 0:
        # No positive weights: fall back to uniform draw.
        idxs = rng.choice(len(w), size=min(k, len(w)), replace=False)
        return np.sort(idxs)
    if n_pos <= k:
        return np.flatnonzero(pos)
    u = rng.random(len(w))
    keys = np.full(len(w), np.inf, dtype=np.float64)
    keys[pos] = -np.log(u[pos]) / w[pos]
    idxs = np.argpartition(keys, k - 1)[:k]
    return np.sort(idxs)


def pso_cluster_edges(N, m, T, gamma, seed):
    """Return a list of ``(u, v)`` edges with ``0 <= u < v < N`` for a PSO
    graph on N nodes.

    Parameters mirror the MATLAB signature: ``m`` is half the average
    degree (also the per-new-node attachment count once t > m+1), ``T >= 0``
    is the temperature (smaller T → higher clustering), ``gamma >= 2`` is
    the power-law exponent.

    For ``N == 1`` returns ``[]``. For ``N <= m+1`` the result is the
    complete graph on N nodes (PSO's "connect to all" branch fires for
    every t).
    """
    if N <= 1:
        return []
    if m < 1:
        raise ValueError("m must be >= 1")
    if gamma < 2:
        raise ValueError("gamma must be >= 2")
    if T < 0:
        raise ValueError("T must be >= 0")

    m = min(m, N - 1)
    rng = np.random.default_rng(int(seed))

    thetas = rng.uniform(0.0, 2.0 * math.pi, size=N)
    rs = np.zeros(N, dtype=np.float64)

    beta = 1.0 / (gamma - 1.0)
    edges = []

    for t in range(2, N + 1):
        # update radial coords for nodes 1..t-1 (1-based) → indices 0..t-2.
        idx = np.arange(1, t, dtype=np.float64)
        rs[: t - 1] = beta * (2.0 * np.log(idx)) + (1.0 - beta) * (2.0 * math.log(t))
        rs[t - 1] = 2.0 * math.log(t)

        if t - 1 <= m:
            for v in range(t - 1):
                edges.append((v, t - 1))
            continue

        d = hyperbolic_dist(thetas[t - 1], rs[t - 1], thetas[: t - 1], rs[: t - 1])

        if T == 0:
            partners = np.argpartition(d, m - 1)[:m]
        else:
            log_t = math.log(t)
            sin_Tpi = math.sin(T * math.pi)
            if sin_Tpi == 0:
                # Pathological T (multiple of 1); fall back to T==0 branch.
                partners = np.argpartition(d, m - 1)[:m]
            else:
                if beta == 1.0:
                    Rt = 2.0 * log_t - 2.0 * math.log(
                        (2.0 * T * log_t) / (sin_Tpi * m)
                    )
                else:
                    inner = (2.0 * T * (1.0 - math.exp(-(1.0 - beta) * log_t))) / (
                        sin_Tpi * m * (1.0 - beta)
                    )
                    Rt = 2.0 * log_t - 2.0 * math.log(inner)
                # p_i = 1 / (1 + exp((d_i - Rt) / (2T))). Guard overflow.
                z = (d - Rt) / (2.0 * T)
                p = 1.0 / (1.0 + np.exp(np.clip(z, -700.0, 700.0)))
                partners = _weighted_sample_without_replacement(p, m, rng)

        for v in partners:
            edges.append((int(v), t - 1))

    return edges


def pso_cluster_edges_remapped(cluster_nodes, m, T, gamma, seed):
    """Convenience wrapper: run ``pso_cluster_edges`` on ``len(cluster_nodes)``
    nodes, then remap the local 0..N-1 ids to the caller's iids using the
    order of ``cluster_nodes``.

    The order of ``cluster_nodes`` controls which empirical iid plays the
    role of "node 1" (the highest-popularity hub). Caller is expected to
    pre-sort by descending residual degree or another popularity proxy.
    """
    n = len(cluster_nodes)
    if n <= 1:
        return []
    edges = pso_cluster_edges(n, m, T, gamma, seed)
    return [
        (cluster_nodes[u], cluster_nodes[v]) if cluster_nodes[u] < cluster_nodes[v]
        else (cluster_nodes[v], cluster_nodes[u])
        for u, v in edges
    ]


def induced_global_ccoeff(N, edges):
    """Global / transitivity clustering coefficient for an undirected
    simple graph defined by ``edges`` on ``N`` nodes.

    Returns ``3 * triangles / triplets`` where ``triplets = sum_v
    deg(v)*(deg(v)-1)/2``. Returns 0.0 when no triplets exist.

    Matches networkit's ``ClusteringCoefficient.exactGlobal`` definition,
    which is what the npso pipeline uses for its T-search.
    """
    if N <= 2:
        return 0.0
    adj = [set() for _ in range(N)]
    for u, v in edges:
        if u == v:
            continue
        adj[u].add(v)
        adj[v].add(u)
    triplets = 0
    for nbrs in adj:
        d = len(nbrs)
        triplets += d * (d - 1) // 2
    if triplets == 0:
        return 0.0
    triangles = 0
    for u in range(N):
        nbrs_u = adj[u]
        for v in nbrs_u:
            if v <= u:
                continue
            common = adj[v] & nbrs_u
            for w in common:
                if w > v:
                    triangles += 1
    return 3.0 * triangles / triplets
