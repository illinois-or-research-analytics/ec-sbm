#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <sstream>
#include <map>
#include <set>
#include <algorithm>
#include <chrono>
#include <cxxopts.hpp>
#include <nlohmann/json.hpp>
#include "spdlog/spdlog.h"
#include "spdlog/sinks/basic_file_sink.h"
#include "spdlog/sinks/stdout_color_sinks.h"

using json = nlohmann::json;

// --- CSV Reader Class ---
class CSVReader {
public:
    CSVReader(std::istream& input, char delimiter = '\t')
        : input_stream(input), delim(delimiter) {}

    bool read_row(std::vector<std::string>& row) {
        row.clear();
        std::string line;
        
        if (!std::getline(input_stream, line)) {
            return false; // End of file
        }

        // Skip empty lines or comment lines
        if (line.empty() || line[0] == '#') {
            return read_row(row); // Recurse to get next valid line
        }

        std::stringstream ss(line);
        std::string cell;
        bool all_empty = true;

        while (ss >> cell) {
            row.push_back(cell);
            all_empty = false;
        }
        
        if(all_empty && !line.empty()) {
            return read_row(row); // Recurse to get next valid line
        }

        return !all_empty;
    }

private:
    std::istream& input_stream;
    char delim;
};

// --- Logging Setup ---
void setup_logging(const std::string& log_file) {
    try {
        auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
        console_sink->set_level(spdlog::level::info);
        auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(log_file, true);
        file_sink->set_level(spdlog::level::info);

        // Use std::vector for sink list (more compatible)
        std::vector<spdlog::sink_ptr> sinks;
        sinks.push_back(console_sink);
        sinks.push_back(file_sink);

        auto logger = std::make_shared<spdlog::logger>("multi_sink", sinks.begin(), sinks.end());
        logger->set_level(spdlog::level::info);
        logger->set_pattern("%Y-%m-%d %H:%M:%S.%e - %l - %v");
        spdlog::register_logger(logger);
        spdlog::set_default_logger(logger);
    } catch (const spdlog::spdlog_ex& ex) {
        std::cerr << "Log init failed: " << ex.what() << std::endl;
    }
}

// --- ID Mapping ---
// Maps for original string IDs to new 1-indexed integer IDs
std::map<std::string, int> node_str_to_iid;
std::map<std::string, int> cluster_str_to_iid;
int next_node_iid = 1;
int next_cluster_iid = 1;

int get_node_iid(const std::string& str_id) {
    if (node_str_to_iid.find(str_id) == node_str_to_iid.end()) {
        node_str_to_iid[str_id] = next_node_iid++;
    }
    return node_str_to_iid[str_id];
}

int get_cluster_iid(const std::string& str_id) {
    if (cluster_str_to_iid.find(str_id) == cluster_str_to_iid.end()) {
        cluster_str_to_iid[str_id] = next_cluster_iid++;
    }
    return cluster_str_to_iid[str_id];
}


// --- Main Function ---
int main(int argc, char** argv) {
    auto start_time = std::chrono::high_resolution_clock::now();

    // --- Argument Parsing ---
    cxxopts::Options options("setup", "Pre-processes graph and clustering for SBM generation.");
    options.add_options()
        ("i,input-edgelist", "Input edgelist file (whitespace-separated)", cxxopts::value<std::string>())
        ("c,input-clustering", "Input clustering file (whitespace-separated)", cxxopts::value<std::string>())
        ("o,output-folder", "Output directory", cxxopts::value<std::string>())
        ("s,seed", "Random seed", cxxopts::value<int>()->default_value("0"))
        ("h,help", "Print usage");
    
    auto result = options.parse(argc, argv);

    if (result.count("help")) {
        std::cout << options.help() << std::endl;
        return 0;
    }

    // --- Argument Validation ---
    if (!result.count("input-edgelist") || !result.count("input-clustering") || !result.count("output-folder")) {
        std::cerr << "Error: Missing one or more required arguments: --input-edgelist, --input-clustering, --output-folder" << std::endl;
        std::cerr << options.help() << std::endl;
        return 1;
    }

    std::string edgelist_fn = result["input-edgelist"].as<std::string>();
    std::string clustering_fn = result["input-clustering"].as<std::string>();
    std::string output_dir = result["output-folder"].as<std::string>();
    int seed = result["seed"].as<int>();

    // --- Logging Setup ---
    std::string log_file = output_dir + "/run_cpp_setup.log";
    setup_logging(log_file);
    spdlog::info("Starting C++ setup...");
    spdlog::info("Input edgelist: {}", edgelist_fn);
    spdlog::info("Input clustering: {}", clustering_fn);
    spdlog::info("Output folder: {}", output_dir);
    spdlog::info("Seed: {}", seed);

    // --- File Paths ---
    std::string node_id_path = output_dir + "/node_id.csv";
    std::string com_id_path = output_dir + "/com_id.csv";
    std::string com_inp_path = output_dir + "/com_inp.csv";
    std::string deg_path = output_dir + "/deg.csv";
    std::string cs_path = output_dir + "/cs.csv";
    std::string full_probs_path = output_dir + "/full_probs.csv";
    std::string progress_path = output_dir + "/progress_tracker.json";

    // --- Data Structures ---
    std::map<std::string, std::string> node_cluster_map_str;
    std::map<std::string, int> cluster_size_map_str;
    std::map<std::string, int> deg_map;
    std::map<std::pair<std::string, std::string>, long long> edge_budget_map_str;

    spdlog::info("Reading graph and clustering...");

    // --- 1. Read Clustering ---
    std::ifstream clustering_file(clustering_fn);
    if (!clustering_file.is_open()) {
        spdlog::error("Failed to open clustering file: {}", clustering_fn);
        return 1;
    }
    CSVReader cluster_reader(clustering_file);
    std::vector<std::string> cluster_row;
    while (cluster_reader.read_row(cluster_row)) {
        if (cluster_row.size() < 2) continue;
        std::string node_id = cluster_row[0];
        std::string cluster_id = cluster_row[1];
        
        node_cluster_map_str[node_id] = cluster_id;
        cluster_size_map_str[cluster_id]++;
    }
    clustering_file.close();
    spdlog::info("Read {} cluster assignments for {} clusters.", node_cluster_map_str.size(), cluster_size_map_str.size());

    // --- 2. Read Edgelist (build deg_map and edge_budget_map) ---
    std::ifstream edgelist_file(edgelist_fn);
    if (!edgelist_file.is_open()) {
        spdlog::error("Failed to open edgelist file: {}", edgelist_fn);
        return 1;
    }
    CSVReader edgelist_reader(edgelist_file);
    std::vector<std::string> edge_row;
    while (edgelist_reader.read_row(edge_row)) {
        if (edge_row.size() < 2) continue;
        std::string src_id = edge_row[0];
        std::string tgt_id = edge_row[1];

        // Increment degrees
        deg_map[src_id]++;
        deg_map[tgt_id]++;

        // Find clusters (if nodes are clustered)
        auto it_src = node_cluster_map_str.find(src_id);
        auto it_tgt = node_cluster_map_str.find(tgt_id);

        if (it_src != node_cluster_map_str.end() && it_tgt != node_cluster_map_str.end()) {
            std::string c1 = it_src->second;
            std::string c2 = it_tgt->second;

            if (c1 == c2) {
                // Intra-cluster edge, contributes 2 to the (c1, c1) budget
                edge_budget_map_str[{c1, c1}] += 2;
            } else {
                // Inter-cluster edge, contributes 1 to both (c1, c2) and (c2, c1)
                edge_budget_map_str[{c1, c2}]++;
                edge_budget_map_str[{c2, c1}]++;
            }
        }
    }
    edgelist_file.close();
    spdlog::info("Graph read complete. {} nodes, {} clusters found.", deg_map.size(), cluster_size_map_str.size());

    // --- 3. Sort Nodes by Degree (descending) ---
    std::vector<std::pair<std::string, int>> sorted_nodes;
    for (const auto& pair : deg_map) {
        sorted_nodes.push_back(pair);
    }
    spdlog::info("Total nodes (from edgelist): {}", sorted_nodes.size());

    // Handle 0-degree nodes that are in clustering but not in edgelist
    for (const auto& pair : node_cluster_map_str) {
        const std::string& node_id = pair.first;
        if (deg_map.find(node_id) == deg_map.end()) {
            sorted_nodes.push_back({node_id, 0});
        }
    }

    std::sort(sorted_nodes.begin(), sorted_nodes.end(), [](const auto& a, const auto& b) {
        return a.second > b.second; // Sort by degree descending
    });

    // --- 4. Sort Clusters by Size (descending) ---
    std::vector<std::pair<std::string, int>> sorted_clusters;
    for (const auto& pair : cluster_size_map_str) {
        sorted_clusters.push_back(pair);
    }
    std::sort(sorted_clusters.begin(), sorted_clusters.end(), [](const auto& a, const auto& b) {
        return a.second > b.second; // Sort by size descending
    });

    // --- 5. Write Files ---
    spdlog::info("Writing budget files...");

    // Write node_id.csv and deg.csv
    std::ofstream node_id_file(node_id_path);
    std::ofstream deg_file(deg_path);
    for (const auto& pair : sorted_nodes) {
        int iid = get_node_iid(pair.first); // Assign 1-indexed IID
        node_id_file << pair.first << "\n";
        deg_file << pair.second << "\n";
    }
    node_id_file.close();
    deg_file.close();

    // Write com_id.csv and cs.csv
    std::ofstream com_id_file(com_id_path);
    std::ofstream cs_file(cs_path);
    for (const auto& pair : sorted_clusters) {
        int iid = get_cluster_iid(pair.first); // Assign 1-indexed IID
        com_id_file << pair.first << "\n";
        cs_file << pair.second << "\n";
    }
    com_id_file.close();
    cs_file.close();

    // Write com_inp.csv
    std::ofstream com_inp_file(com_inp_path);
    for (const auto& pair : node_cluster_map_str) {
        // Use IIDs that were just assigned
        com_inp_file << get_node_iid(pair.first) << "\t" << get_cluster_iid(pair.second) << "\n";
    }
    com_inp_file.close();

    // Write full_probs.csv
    std::ofstream full_probs_file(full_probs_path);
    for (const auto& pair : edge_budget_map_str) {
        full_probs_file << get_cluster_iid(pair.first.first) << "\t"
                          << get_cluster_iid(pair.first.second) << "\t"
                          << pair.second << "\n";
    }
    full_probs_file.close();

    // --- 6. Create Progress Tracker JSON ---
    spdlog::info("Creating progress tracker...");
    json progress;
    progress["status"]["cpp_setup"] = "completed";
    progress["status"]["python_mcs"] = "pending";
    progress["status"]["cpp_graph_gen"] = "pending";
    progress["status"]["python_sbm"] = "pending";
    progress["status"]["combining"] = "pending";

    progress["inputs"]["edgelist_fn"] = edgelist_fn;
    progress["inputs"]["clustering_fn"] = clustering_fn;
    progress["inputs"]["seed"] = seed;

    progress["files"]["node_id"] = "node_id.csv";
    progress["files"]["com_id"] = "com_id.csv";
    progress["files"]["com_inp"] = "com_inp.csv";
    progress["files"]["deg"] = "deg.csv";
    progress["files"]["cs"] = "cs.csv";
    progress["files"]["full_probs"] = "full_probs.csv";
    progress["files"]["mcs"] = "mcs.csv";
    progress["files"]["com_out"] = "com.tsv"; // FIX (2): Already com.tsv
    progress["files"]["remaining_deg"] = "remaining_deg.csv";
    progress["files"]["remaining_probs"] = "remaining_probs.csv";
    progress["files"]["final_edge_list"] = "edge.tsv"; // FIX (2): Changed from edge_out.csv
    progress["files"]["edgelist_index"] = "edgelist_index.json";
    // sbm_edge_file will be added by the python script

    progress["clusters"] = json::object(); // Will be populated by C++ graph gen

    std::ofstream progress_file(progress_path);
    progress_file << progress.dump(4);
    progress_file.close();

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> elapsed = end_time - start_time;
    spdlog::info("C++ setup finished in {} ms.", elapsed.count());

    return 0;
}
