# Hybrid Graph Generator

This project generates large-scale graphs by combining a high-performance C++ program for intra-cluster graph generation with a Python script for inter-cluster Stochastic Block Model (SBM) generation.

The pipeline is orchestrated by a Bash script (`run.sh`) and uses JSON files (`progress_tracker.json`) for state management, allowing the process to be resumed if interrupted.

## Architecture

The process is managed by `run.sh` and broken into three main stages:

1.  **C++ Subgraph Generation (`generate_subgraphs`)**:
    * Reads the full edgelist and clustering data.
    * Calculates the initial degree and edge budgets.
    * Iterates through each cluster, generates its k-connected subgraph, and writes the edges to a separate file in `edge_parts/`.
    * Updates `progress_tracker.json` after each cluster, allowing resumption.
    * Writes the *remaining* (inter-cluster) degree and edge budgets to `remaining_deg.csv` and `remaining_probs.csv`.

2.  **Python SBM Generation (`generate_sbm.py`)**:
    * Reads the remaining budget files created by the C++ program.
    * Uses `graph-tool` to generate the inter-cluster edges based on the remaining SBM budget.
    * Writes the new inter-cluster edges to `inter_cluster_edges.csv`.
    * Updates `progress_tracker.json` to mark its completion.

3.  **Bash Combine & Index (`run.sh`)**:
    * Concatenates all individual cluster edge files and the SBM edge file into the final `edge_out.csv`.
    * Generates `edgelist_index.json`, a file that maps line numbers in `edge_out.csv` back to their source file (e.g., "cluster_0", "sbm_inter_cluster") for auditing.

## Dependencies

### 1. C++ Dependencies

* **CMake** (>= 3.16)
* A C++17 compiler (e.g., `g++`, `clang++`)
* **Eigen3**: For matrix/vector operations.
* **spdlog**: For logging.
* **cxxopts**: For command-line argument parsing.
* **nlohmann-json**: For JSON state management (Note: This is downloaded automatically by CMake via `FetchContent`).

### 2. Python Dependencies

* Python 3 (>= 3.8)
* `pip`
* `graph-tool` (Note: This has special installation instructions)
* `numpy`
* `scipy`
* `pandas`

### 3. Shell Dependencies

* **`jq`**: A command-line JSON processor used by `run.sh`.

## Installation

### 1. System Dependencies (Ubuntu/Debian)

```

# C/C++ build tools

sudo apt-get update
sudo apt-get install -y build-essential cmake

# C++ libraries

sudo apt-get install -y libeigen3-dev libspdlog-dev libcxxopts-dev

# Shell

sudo apt-get install -y jq

```

### 2. Python: graph-tool

`graph-tool` is not available on PyPI. Follow the official instructions or use the PPA for Ubuntu:

```

conda install -c conda-forge graph-tool

```

### 3. Python: Other Dependencies

A `requirements.txt` file is provided for the remaining Python packages.

```

conda install numpy scipy pandas networkx

```

## How to Run

The entire pipeline is executed through the `run.sh` script.

1.  **Build the C++ executable**:
    The `run.sh` script does this automatically. You can also run it manually:
    ```
    cmake .
    make generate_subgraphs
    ```

2.  **Run the Pipeline**:
    Execute the `run.sh` script, providing the paths to your input edgelist, input clustering, and the desired output directory.
    ```
    ./run.sh <input_edgelist> <input_clustering> <output_dir> [seed]
    ```
    * `<input_edgelist>`: Path to the original graph edgelist (tab-separated `src_id \t tgt_id`).
    * `<input_clustering>`: Path to the node clustering file (tab-separated `node_id \t cluster_id`).
    * `<output_dir>`: The directory where all output will be stored.
    * `[seed]` (Optional): A random seed (default: 0).

    **Example:**
    ```
    ./run.sh data/my_graph.edgelist data/my_clustering.csv ./output_run_1 42
    ```
    If the script is interrupted, you can simply run the *exact same command* again. It will read `progress_tracker.json` and resume from the last completed cluster.

## Main Output Files

All outputs will be in the `<output_dir>` you specify:

* **`edge_out.csv`**: The final, complete edgelist containing both intra-cluster and inter-cluster edges.
* **`com_out.csv`**: The final node-to-community mapping, identical to your input but verified.
* **`progress_tracker.json`**: The state-management file. You can inspect this to see which clusters have been processed.
* **`edgelist_index.json`**: An index mapping line ranges in `edge_out.csv` to their source.
* **`edge_parts/`**: A directory containing all the intermediate edge files (one per cluster, plus the SBM edges).
* **Logs**: `run.log`, `run_cpp.log`, `run_python.log`.