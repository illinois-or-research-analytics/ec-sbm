#!/bin/bash

# This script orchestrates the entire graph generation pipeline.
# It calls C++ and Python scripts in sequence and manages state via a JSON file.

# --- Config ---
set -e # Exit immediately if a command exits with a non-zero status.

# --- Logger ---
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO - $1"
}

# --- Helper Functions ---
update_status() {
    # $1: step name (e.g., "cpp_setup")
    # $2: status (e.g., "running")
    jq --arg step "$1" --arg status "$2" '.status[$step] = $status' "$PROGRESS_FILE" > tmp.$$.json && mv tmp.$$.json "$PROGRESS_FILE"
}

check_status() {
    # $1: step name
    # Returns 0 if "completed", 1 otherwise
    local status=$(jq -r --arg step "$1" '.status[$step]' "$PROGRESS_FILE")
    [ "$status" == "completed" ]
}

check_fail() {
    # $1: step name
    local status=$(jq -r --arg step "$1" '.status[$step]' "$PROGRESS_FILE")
    if [ "$status" == "failed" ]; then
        log "ERROR: Step '$1' failed. Check logs."
        exit 1
    fi
}

# --- Argument Parsing ---
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <input_edgelist> <input_clustering> <output_dir> [seed]"
    exit 1
fi

INPUT_EDGELIST=$1
INPUT_CLUSTERING=$2
OUTPUT_DIR=$3
SEED=${4:-0} # Default seed is 0

# --- Setup ---
log "Pipeline started."
mkdir -p "$OUTPUT_DIR"
PROGRESS_FILE="$OUTPUT_DIR/progress_tracker.json"
MAIN_LOG="$OUTPUT_DIR/run.log"
exec > >(tee -a "$MAIN_LOG") 2>&1 # Redirect stdout/stderr to file and console

# Check for jq
if ! command -v jq &> /dev/null; then
    log "ERROR: 'jq' is not installed. Please install it to continue."
    exit 1
fi

# --- 1. Build C++ ---
log "Building C++ executables (setup, generate_graphs)..."
cmake .
make setup generate_graphs
log "Build complete."

# --- 2. Run C++ Setup ---
if [ -f "$PROGRESS_FILE" ] && check_status "cpp_setup"; then
    log "Skipping C++ setup (already completed)."
else
    log "Running C++ setup..."
    
    # FIX: Create an empty JSON file if it doesn't exist, so jq doesn't fail
    if [ ! -f "$PROGRESS_FILE" ]; then
        log "Creating new progress file: $PROGRESS_FILE"
        echo "{ \"status\": {} }" > "$PROGRESS_FILE"
    fi
    
    update_status "cpp_setup" "running"
    ./setup --input-edgelist "$INPUT_EDGELIST" \
            --input-clustering "$INPUT_CLUSTERING" \
            --output-folder "$OUTPUT_DIR" \
            --seed "$SEED"
    check_fail "cpp_setup"
    log "C++ setup finished."
fi

# --- 3. Run Python MCS Calculation ---
if check_status "python_mcs"; then
    log "Skipping Python MCS calculation (already completed)."
else
    log "Running Python to calculate MCS..."
    update_status "python_mcs" "running"
    python3 calculate_mcs.py --output-dir "$OUTPUT_DIR"
    check_fail "python_mcs"
    log "Python MCS calculation finished."
fi

# --- 4. Run C++ Graph Generation (K-Graphs) ---
if check_status "cpp_graph_gen"; then
    log "Skipping C++ graph generation (already completed)."
else
    log "Running C++ to generate k-connected subgraphs..."
    mkdir -p "$OUTPUT_DIR/edge_parts" # Ensure dir exists
    update_status "cpp_graph_gen" "running"
    ./generate_graphs --output-folder "$OUTPUT_DIR" --seed "$SEED"
    check_fail "cpp_graph_gen"
    log "C++ graph generation finished."
fi

# --- 5. Run Python SBM Generation ---
if check_status "python_sbm"; then
    log "Skipping Python SBM generation (already completed)."
else
    log "Running Python to generate SBM..."
    update_status "python_sbm" "running"
    python3 generate_sbm.py --output-dir "$OUTPUT_DIR"
    check_fail "python_sbm"
    log "Python SBM generation finished."
fi

# --- 6. Combine all edge files and create index ---
log "Combining all edge files and creating index..."
update_status "combining" "running"

FINAL_EDGE_LIST_NAME=$(jq -r '.files.final_edge_list' "$PROGRESS_FILE")
EDGELIST_INDEX_NAME=$(jq -r '.files.edgelist_index' "$PROGRESS_FILE")
SBM_EDGE_FILE_NAME=$(jq -r '.files.sbm_edge_file' "$PROGRESS_FILE")

# Get all cluster edge files
CLUSTER_EDGE_FILES=$(jq -r '.clusters | to_entries[] | .value.edge_file' "$PROGRESS_FILE" | grep -v null | sort -V | awk -v dir="$OUTPUT_DIR/" '{print dir $0}')
SBM_EDGE_PATH="$OUTPUT_DIR/$SBM_EDGE_FILE_NAME"
FINAL_EDGE_PATH="$OUTPUT_DIR/$FINAL_EDGE_LIST_NAME"

# Combine all files
log "Concatenating edge files to $FINAL_EDGE_PATH..."
cat $CLUSTER_EDGE_FILES $SBM_EDGE_PATH > "$FINAL_EDGE_PATH"
log "Concatenation complete."

# Create edgelist index
log "Creating edgelist index at $EDGELIST_INDEX_NAME..."
current_line=1
INDEX_FILE_PATH="$OUTPUT_DIR/$EDGELIST_INDEX_NAME"
echo "{" > "$INDEX_FILE_PATH" # Start JSON

# Index cluster files
comma=""
for f in $CLUSTER_EDGE_FILES; do
    line_count=$(wc -l < "$f")
    cluster_key=$(basename "$f" | sed -e 's/_edges.csv//' -e 's/cluster_//')
    
    echo "$comma" >> "$INDEX_FILE_PATH" # Add comma before this entry
    echo "  \"cluster_${cluster_key}\": { \"start\": $current_line, \"end\": $(($current_line + $line_count - 1)) }" >> "$INDEX_FILE_PATH"
    current_line=$(($current_line + $line_count))
    comma=","
done

# Index SBM file
line_count=$(wc -l < "$SBM_EDGE_PATH")
if [ "$line_count" -gt 0 ]; then
    echo "$comma" >> "$INDEX_FILE_PATH" # Add comma if needed
    echo "  \"sbm_inter_cluster\": { \"start\": $current_line, \"end\": $(($current_line + $line_count - 1)) }" >> "$INDEX_FILE_PATH"
fi

echo "}" >> "$INDEX_FILE_PATH" # End JSON
log "Edgelist index created."

update_status "combining" "completed"
log "Pipeline finished successfully."

