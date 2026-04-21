# **Edge-Connected Stochastic Block Model (EC-SBM)**

## **Table of Contents**

- [Overview](#overview)
- [Usage](#usage)
  - [Short version](#short-version)
  - [Long version](#long-version)
    - [Profiling: Extracting empirical statistics](#profiling-extracting-empirical-statistics)
    - [Stage 1: Generation of the synthetic clustered subnetwork](#stage-1-generation-of-the-synthetic-clustered-subnetwork)
    - [Stage 2: Generation of the synthetic outlier subnetwork](#stage-2-generation-of-the-synthetic-outlier-subnetwork)
    - [Stage 3: Degree matching](#stage-3-degree-matching)
    - [Combining edgelists](#combining-edgelists)
- [Installation](#installation)

## **Overview**

This repository contains the implementation of the Edge-Connected Stochastic Block Model (EC-SBM) for generating synthetic networks based on an empirical network and its reference clustering.

Outliers (nodes not assigned to a cluster, or in singleton clusters) are excluded from the clustered subnetwork and synthesized separately in a dedicated outlier stage.

## **Usage**

### **Input**

We are given
* an empirical network `<path/to/empirical>/edge.csv` (CSV with header `source,target`)
* a reference clustering `<path/to/empirical>/com.csv` (CSV with header `node_id,cluster_id`)

### **Short version**

**Command** We generate the synthetic network with EC-SBM by running:

```bash
bash scripts/run_ecsbm.sh \
    --input-edgelist <path/to/empirical>/edge.csv \
    --input-clustering <path/to/empirical>/com.csv \
    --output-dir <path/to/output>
```

**Optional flags:**
* `--seed <int>` — RNG seed (default `1`). Under a fixed seed, the pipeline is byte-reproducible.
* `--timeout <duration>` — per-stage timeout passed to `timeout(1)` (default `3d`).
* `--n-threads <int>` — sets `OMP_NUM_THREADS` (default `1`).
* `--keep-state` — keep intermediate stage artifacts under `<output-dir>/.state/` after a successful run. Without this flag, `.state/` is deleted on success.

**Caching:** each stage writes a sha256 `done` file over its declared inputs and outputs; reruns short-circuit when hashes still match. A top-level `done` file short-circuits the entire pipeline when nothing has changed.

**Output**

The final synthetic network is `<output-dir>/edge.csv`. The surviving top-level artifacts are:

```
<output-dir>/
├── edge.csv             # Final synthetic network (source,target)
├── com.csv              # Clustering used for generation (outliers removed)
├── sources.json         # Provenance map: which rows came from which stage
├── params.txt           # Pipeline fingerprint (seed, n_threads)
├── run.log              # Consolidated per-stage logs
├── done                 # sha256 fingerprint of pipeline I/O
└── .state/              # (only with --keep-state) per-stage intermediates
    ├── profile/         # Empirical statistics (node_id, cluster_id, assignment,
    │                    #   degree, mincut, edge_counts, com)
    ├── gen_clustered/   # Stage 1 output: clustered subnetwork edge.csv
    ├── gen_outlier/     # Stage 2: outlier subnetwork + combine with stage 1
    │   ├── edges/       #   SBM-synthesized outlier edges (edge_outlier.csv)
    │   └── edge.csv     #   stage 1 + outlier edges (deduped)
    └── match_degree/    # Stage 3: degree matching + combine with stages 1+2
        ├── edges/       #   Added edges (degree_matching_edge.csv)
        └── edge.csv     #   stages 1+2 + degree-matching edges (deduped)
```

Each stage directory also contains `done` (sha256 fingerprint of inputs+outputs), `params.txt` (stage parameters), `run.log`, and `time_and_err.log`.

**Example**

```bash
bash scripts/run_ecsbm.sh \
    --input-edgelist examples/input/dnc/edge.csv \
    --input-clustering examples/input/dnc/com.csv \
    --output-dir examples/output/dnc \
    --seed 1
```

Reference output at `examples/output/dnc/` was generated with `--seed 1 --keep-state`; `examples/output/dnc/edge.csv` has sha256 `e2b5a6914b12…`.

### **Long version**

The full pipeline consists of profiling and three main stages. All scripts consume and produce CSV files with headers. Direct invocations below assume `PYTHONPATH` includes `ec-sbm/` (the shared helpers live there).

#### **Profiling: Extracting empirical statistics**

Computes the inputs needed by Stage 1: node/cluster iid mappings, cluster assignment, degree sequence, per-cluster min-cut, inter-cluster edge counts, and the outlier-cleaned clustering.

Outliers and every incident edge are dropped before any downstream computation.

```bash
python ec-sbm/profile.py \
    --edgelist <path/to/empirical>/edge.csv \
    --clustering <path/to/empirical>/com.csv \
    --output-folder <path/to/setup>
```

**Output:** `node_id.csv`, `cluster_id.csv`, `assignment.csv`, `degree.csv`, `mincut.csv`, `edge_counts.csv`, `com.csv`.

#### **Stage 1: Generation of the synthetic clustered subnetwork**

Generates the k-edge-connected clustered subnetwork from the profiled inputs.

```bash
python ec-sbm/gen_clustered.py \
    --node-id <setup>/node_id.csv \
    --cluster-id <setup>/cluster_id.csv \
    --assignment <setup>/assignment.csv \
    --degree <setup>/degree.csv \
    --mincut <setup>/mincut.csv \
    --edge-counts <setup>/edge_counts.csv \
    --output-folder <path/to/clustered> \
    --seed 1
```

**Output:** `<clustered>/edge.csv`.

#### **Stage 2: Generation of the synthetic outlier subnetwork**

Generates the outlier subnetwork (edges touching at least one outlier) via SBM.

```bash
python ec-sbm/gen_outlier.py \
    --edgelist <path/to/empirical>/edge.csv \
    --clustering <path/to/empirical>/com.csv \
    --output-folder <path/to/outlier_edges> \
    --seed 2
```

**Output:** `<outlier_edges>/edge_outlier.csv`.

#### **Stage 3: Degree matching**

Adds edges so that the synthetic per-node degree matches the empirical one.

```bash
python ec-sbm/match_degree.py \
    --input-edgelist <path/to/combined>/edge.csv \
    --ref-edgelist <path/to/empirical>/edge.csv \
    --ref-clustering <path/to/empirical>/com.csv \
    --output-folder <path/to/match_degree> \
    --seed 3
```

**Output:** `<match_degree>/degree_matching_edge.csv`.

#### **Combining edgelists**

Merges two edgelists (deduplicated as undirected) and tracks provenance in `sources.json`.

```bash
python ec-sbm/combine_edgelists.py \
    --edgelist-1 <path/to/a>/edge.csv --name-1 a \
    --edgelist-2 <path/to/b>/edge.csv --name-2 b \
    --output-folder <path/to/out> \
    --output-filename edge.csv
```

## **Installation**

See [INSTALL.md](INSTALL.md).
