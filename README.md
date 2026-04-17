# **Edge-Connected Stochastic Block Model (EC-SBM)**

## **Table of Contents**

- [Overview](#overview)
- [Usage](#usage)
  - [Short version](#short-version)
  - [Long version](#long-version)
    - [Preprocessing: Cleaning the outliers](#preprocessing-cleaning-the-outliers)
    - [Profiling: Extracting empirical statistics](#profiling-extracting-empirical-statistics)
    - [Stage 1: Generation of the synthetic clustered subnetwork](#stage-1-generation-of-the-synthetic-clustered-subnetwork)
    - [Stage 2: Generation of the synthetic outlier subnetwork](#stage-2-generation-of-the-synthetic-outlier-subnetwork)
    - [Stage 3: Degree matching](#stage-3-degree-matching)
    - [Combining edgelists](#combining-edgelists)
- [Installation Guide](#installation-guide)

## **Overview**

This repository contains the implementation of the Edge-Connected Stochastic Block Model (EC-SBM) for generating synthetic networks based on an empirical network and its reference clustering.

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
* `--timeout <duration>` — per-stage timeout (default `3d`).
* `--existing-clustered` — reuse an existing `<output-dir>/clustered/edge.csv` and skip Stage 1.
* `--existing-outlier` — additionally reuse `<output-dir>/outlier/edge.csv` and skip Stages 1 and 2.

**Output**

The final synthetic network is `<output-dir>/edge.csv`. Intermediate results are organized as follows:

```
<output-dir>/
├── clustered/
│   ├── clean/          # Cleaned inputs (no singleton clusters)
│   ├── setup/          # Profiled statistics (node_id, cluster_id, assignment, degree, mincut, edge_counts)
│   └── edge.csv        # Stage 1 synthetic clustered subnetwork
├── outlier/
│   ├── edges/          # Stage 2 synthetic outlier subnetwork
│   └── edge.csv        # Clustered + outlier merged
├── match_degree/       # Stage 3 additional edges to match empirical degree
├── edge.csv            # Final synthetic network
└── sources.json        # Provenance map: which rows came from which stage
```

**Example**

```bash
bash scripts/run_ecsbm.sh \
    --input-edgelist examples/input/cit_hepph/edge.csv \
    --input-clustering examples/input/cit_hepph/com.csv \
    --output-dir examples/output/cit_hepph
```

### **Long version**

The full pipeline consists of preprocessing, profiling, and three main stages. All scripts consume and produce CSV files with headers.

#### **Preprocessing: Cleaning the outliers**

Removes singleton clusters and edges incident to them.

```bash
python ec-sbm/clean_outlier.py \
    --edgelist <path/to/empirical>/edge.csv \
    --clustering <path/to/empirical>/com.csv \
    --output-folder <path/to/clean>
```

**Output:** `<clean>/edge.csv`, `<clean>/com.csv`.

#### **Profiling: Extracting empirical statistics**

Computes the inputs needed by Stage 1: node/cluster iid mappings, cluster assignment, degree sequence, per-cluster min-cut, and inter-cluster edge counts.

```bash
python ec-sbm/profile.py \
    --edgelist <path/to/clean>/edge.csv \
    --clustering <path/to/clean>/com.csv \
    --output-folder <path/to/setup> \
    --generator ecsbm
```

**Output:** `node_id.csv`, `cluster_id.csv`, `assignment.csv`, `degree.csv`, `mincut.csv`, `edge_counts.csv`.

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
    --output-folder <path/to/clustered>
```

**Output:** `<clustered>/edge.csv`.

#### **Stage 2: Generation of the synthetic outlier subnetwork**

Generates the outlier subnetwork (edges touching at least one outlier) via SBM.

```bash
python ec-sbm/gen_outlier.py \
    --edgelist <path/to/empirical>/edge.csv \
    --clustering <path/to/empirical>/com.csv \
    --output-folder <path/to/outlier_edges>
```

**Output:** `<outlier_edges>/edge_outlier.csv`.

#### **Stage 3: Degree matching**

Adds edges so that the synthetic per-node degree matches the empirical one.

```bash
python ec-sbm/match_degree.py \
    --input-edgelist <path/to/combined>/edge.csv \
    --ref-edgelist <path/to/empirical>/edge.csv \
    --ref-clustering <path/to/empirical>/com.csv \
    --output-folder <path/to/match_degree>
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

## Installation Guide

### Using conda with the environment file

```bash
conda env create -f env.yml -n ec-sbm
conda activate ec-sbm
```

### Using conda manually

```bash
conda create -n ec-sbm python=3.12
conda activate ec-sbm
bash scripts/install.sh
```
