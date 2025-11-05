#!/bin/bash

# This script builds the C++ executables.
# It creates a 'build' directory for intermediate files
# and places the final binaries in the 'bin' directory.

# --- Config ---
set -e # Exit immediately if a command exits with a non-zero status.

# --- Logger ---
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO - $1"
}

# --- Build ---
log "Building C++ executables (setup, generate_graphs)..."

# Create build and bin directories
mkdir -p build
mkdir -p bin

# Run CMake and Make from within the build directory
cd build
log "Running CMake..."
cmake ..
log "Running Make..."
make setup generate_graphs
cd .. # Return to root directory

log "Build complete. Binaries are in the 'bin' directory."
