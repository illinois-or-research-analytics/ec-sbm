#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <sstream>
#include <map>
#include <set>
#include <algorithm>
#include <chrono>
#include <random>
#include <iomanip> // For std::setw
#include <cxxopts.hpp>
#include <nlohmann/json.hpp>
#include "spdlog/spdlog.h"
#include "spdlog/sinks/basic_file_sink.h"
#include "spdlog/sinks/stdout_color_sinks.h"
#include <Eigen/Sparse>

using json = nlohmann::json;
using SpMat = Eigen::SparseMatrix<long long>;
using Triplet = Eigen::Triplet<long long>;

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
        
        // Handle lines that are just whitespace
        if(all_empty && !line.empty()) { 
            return read_row(row);
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

// --- Global RNG ---
std::mt19937 rng;

// --- Graph Generation Logic ---
std::pair<int, int> create_edge(int u, int v) {
    return {std::min(u, v), std::max(u, v)};
}

std::set<std::pair<int, int>> generate_cluster(const std::vector<int>& cluster_nodes, int k, 
                                               std::vector<long long>& deg, SpMat& probs, 
                                               const std::vector<int>& node2cluster) {
    if (k == 0 || cluster_nodes.empty()) {
        return {};
    }

    int n = cluster_nodes.size();
    std::vector<int> cluster_nodes_ordered = cluster_nodes;

    // Sort nodes in this cluster by their current (remaining) degree
    std::sort(cluster_nodes_ordered.begin(), cluster_nodes_ordered.end(), 
        [&](int a, int b) {
            return deg[a] > deg[b];
        }
    );

    std::set<int> processed_nodes;
    std::set<std::pair<int, int>> edges;

    int i = 0;
    while (i <= k && i < n) {
        int u = cluster_nodes_ordered[i];
        for (int v : processed_nodes) {
            if (deg[u] <= 0) break; // Node u has used up its budget

            int u_cluster = node2cluster[u];
            int v_cluster = node2cluster[v];

            if (probs.coeff(u_cluster, v_cluster) > 0) {
                edges.insert(create_edge(u, v));
                deg[u]--;
                deg[v]--;
                probs.coeffRef(u_cluster, v_cluster)--;
                probs.coeffRef(v_cluster, u_cluster)--;
            }
        }
        processed_nodes.insert(u);
        i++;
    }

    while (i < n) {
        int u = cluster_nodes_ordered[i];
        
        std::vector<int> processed_nodes_ordered(processed_nodes.begin(), processed_nodes.end());
        std::sort(processed_nodes_ordered.begin(), processed_nodes_ordered.end(), 
            [&](int a, int b) {
                return deg[a] > deg[b];
            }
        );

        int n_processed = processed_nodes_ordered.size();
        std::set<int> candidates(processed_nodes.begin(), processed_nodes.end());

        int ii = 0; // Edges added for node u
        int iii = 0; // Index into processed_nodes_ordered

        while (ii < k && iii < n_processed && deg[u] > 0) {
            int v = processed_nodes_ordered[iii++];
            int u_cluster = node2cluster[u];
            int v_cluster = node2cluster[v];

            if (deg[v] > 0 && probs.coeff(u_cluster, v_cluster) > 0) {
                edges.insert(create_edge(u, v));
                deg[u]--;
                deg[v]--;
                probs.coeffRef(u_cluster, v_cluster)--;
                probs.coeffRef(v_cluster, u_cluster)--;
                candidates.erase(v);
                ii++;
            }
        }

        // Fallback: connect to remaining candidates randomly
        while (ii < k && !candidates.empty() && deg[u] > 0) {
            std::vector<int> list_candidates(candidates.begin(), candidates.end());
            // Simple uniform random choice
            std::uniform_int_distribution<int> dist(0, list_candidates.size() - 1);
            int v_idx = dist(rng);
            int v = list_candidates[v_idx];

            int u_cluster = node2cluster[u];
            int v_cluster = node2cluster[v];

            if (deg[v] > 0 && probs.coeff(u_cluster, v_cluster) > 0) {
                edges.insert(create_edge(u, v));
                deg[u]--;
                deg[v]--;
                probs.coeffRef(u_cluster, v_cluster)--;
                probs.coeffRef(v_cluster, u_cluster)--;
                ii++;
            }
            candidates.erase(v);
        }
        processed_nodes.insert(u);
        i++;
    }
    return edges;
}


// --- Main Function ---
int main(int argc, char** argv) {
    auto start_time = std::chrono::high_resolution_clock::now();

    cxxopts::Options options("generate_graphs", "Generates k-connected subgraphs and remaining SBM.");
    options.add_options()
        ("o,output-folder", "Output directory", cxxopts::value<std::string>())
        ("s,seed", "Random seed", cxxopts::value<int>()->default_value("0"))
        ("h,help", "Print usage");

    auto result = options.parse(argc, argv);

    if (result.count("help")) {
        std::cout << options.help() << std::endl;
        return 0;
    }

    if (!result.count("output-folder")) {
        std::cerr << "Error: Missing required argument: --output-folder" << std::endl;
        std::cerr << options.help() << std::endl;
        return 1;
    }

    std::string output_dir = result["output-folder"].as<std::string>();
    int seed = result["seed"].as<int>();
    rng.seed(seed); // Seed the global RNG

    std::string log_file = output_dir + "/run_cpp_graph_gen.log";
    setup_logging(log_file);
    spdlog::info("Starting C++ graph generation...");
    spdlog::info("Output folder: {}", output_dir);
    spdlog::info("Seed: {}", seed);

    std::string progress_path = output_dir + "/progress_tracker.json";
    json progress;

    int num_nodes = 0;
    int num_clusters = 0;
    std::map<int, std::vector<int>> clustering; // cluster_iid (0-indexed) -> [node_iid (0-indexed)]
    std::vector<int> mcs; // 0-indexed by cluster_iid
    std::vector<long long> deg; // 0-indexed by node_iid
    std::vector<int> node2cluster; // 0-indexed by node_iid

    try {
        // --- Read Progress Tracker ---
        std::ifstream progress_f(progress_path);
        if (!progress_f.is_open()) {
            spdlog::error("Failed to open progress tracker: {}", progress_path);
            return 1;
        }
        progress_f >> progress;
        progress_f.close();

        // --- Define File Paths from Progress ---
        std::string deg_path = output_dir + "/" + progress["files"]["deg"].get<std::string>();
        std::string mcs_path = output_dir + "/" + progress["files"]["mcs"].get<std::string>();
        std::string com_inp_path = output_dir + "/" + progress["files"]["com_inp"].get<std::string>();
        std::string full_probs_path = output_dir + "/" + progress["files"]["full_probs"].get<std::string>();
        std::string remaining_deg_path = output_dir + "/" + progress["files"]["remaining_deg"].get<std::string>();
        std::string remaining_probs_path = output_dir + "/" + progress["files"]["remaining_probs"].get<std::string>();

        spdlog::info("Loading pre-computed data...");

        std::vector<std::string> row;

        // --- Read Degree (deg.csv) ---
        std::ifstream deg_file(deg_path);
        CSVReader deg_reader(deg_file);
        while (deg_reader.read_row(row)) {
            deg.push_back(std::stoll(row[0]));
        }
        deg_file.close();
        num_nodes = deg.size();
        node2cluster.resize(num_nodes);

        // --- Read MCS (mcs.csv) ---
        std::ifstream mcs_file(mcs_path);
        CSVReader mcs_reader(mcs_file);
        while (mcs_reader.read_row(row)) {
            mcs.push_back(std::stoi(row[0]));
        }
        mcs_file.close();
        num_clusters = mcs.size();

        // --- Read Clustering (com_inp.csv) ---
        std::ifstream com_inp_file(com_inp_path);
        CSVReader com_inp_reader(com_inp_file);
        while (com_inp_reader.read_row(row)) {
            int node_iid_1based = std::stoi(row[0]);
            int cluster_iid_1based = std::stoi(row[1]);
            
            int node_iid = node_iid_1based - 1; // Convert to 0-indexed
            int cluster_iid = cluster_iid_1based - 1; // Convert to 0-indexed

            if (node_iid >= num_nodes) {
                 throw std::runtime_error("Node ID " + row[0] + " is out of bounds (max: " + std::to_string(num_nodes) + ")");
            }
            if (cluster_iid >= num_clusters) {
                 throw std::runtime_error("Cluster ID " + row[1] + " is out of bounds (max: " + std::to_string(num_clusters) + ")");
            }

            clustering[cluster_iid].push_back(node_iid);
            node2cluster[node_iid] = cluster_iid;
        }
        com_inp_file.close();

        // --- Read Probs (full_probs.csv) ---
        SpMat probs(num_clusters, num_clusters);
        std::vector<Triplet> tripletList;
        std::ifstream probs_file(full_probs_path);
        CSVReader probs_reader(probs_file);
        while (probs_reader.read_row(row)) {
            int c1_1based = std::stoi(row[0]);
            int c2_1based = std::stoi(row[1]);
            long long count = std::stoll(row[2]);
            
            tripletList.push_back(Triplet(c1_1based - 1, c2_1based - 1, count)); // 0-indexed
        }
        probs_file.close();
        probs.setFromTriplets(tripletList.begin(), tripletList.end());

        // --- Start Cluster Generation ---
        spdlog::info("Data loaded. Starting subgraph generation for {} clusters...", clustering.size());
        progress["status"]["cpp_graph_gen"] = "running";

        std::string edge_parts_dir = output_dir + "/edge_parts";
        // This relies on run.sh creating the directory.
        // Let's be safe and create it here.
        system(("mkdir -p " + edge_parts_dir).c_str());
        
        // ** CORE FIX: Iterate over the loaded clustering map **
        for (const auto& pair : clustering) {
            int cluster_iid = pair.first; // This is the 0-indexed cluster ID
            std::string cluster_id_str = std::to_string(cluster_iid + 1); // Use 1-based for JSON keys
            
            // Check resume logic
            if (progress["clusters"].contains(cluster_id_str) && progress["clusters"][cluster_id_str]["status"] == "completed") {
                spdlog::info("Skipping cluster {} (already completed).", cluster_id_str);
                continue;
            }
            
            spdlog::info("Generating cluster {}/{}...", cluster_id_str, num_clusters);
            
            const auto& cluster_nodes = pair.second;
            int k = mcs[cluster_iid]; // Get MCS from the 0-indexed vector

            auto local_edges = generate_cluster(cluster_nodes, k, deg, probs, node2cluster);

            // Write edges for this cluster
            std::string cluster_edge_file = edge_parts_dir + "/cluster_" + cluster_id_str + "_edges.csv";
            std::string cluster_edge_file_relative = "edge_parts/cluster_" + cluster_id_str + "_edges.csv";
            std::ofstream edge_out(cluster_edge_file);
            for (const auto& edge : local_edges) {
                edge_out << (edge.first + 1) << "\t" << (edge.second + 1) << "\n"; // Convert 0-indexed back to 1-indexed
            }
            edge_out.close();

            // Update progress tracker
            progress["clusters"][cluster_id_str]["status"] = "completed";
            progress["clusters"][cluster_id_str]["edge_file"] = cluster_edge_file_relative;
            progress["clusters"][cluster_id_str]["mcs"] = k;
            std::ofstream progress_out(progress_path);
            progress_out << std::setw(4) << progress << std::endl;
            progress_out.close();
        }
        
        spdlog::info("Subgraph generation complete.");

        // --- Write Remaining Budgets ---
        spdlog::info("Writing remaining budgets...");
        std::ofstream remaining_deg_file(remaining_deg_path);
        for (long long d : deg) {
            remaining_deg_file << d << "\n";
        }
        remaining_deg_file.close();

        std::ofstream remaining_probs_file(remaining_probs_path);
        for (int k = 0; k < probs.outerSize(); ++k) {
            for (SpMat::InnerIterator it(probs, k); it; ++it) {
                remaining_probs_file << (it.row() + 1) << "\t" << (it.col() + 1) << "\t" << it.value() << "\n";
            }
        }
        remaining_probs_file.close();

        progress["status"]["cpp_graph_gen"] = "completed";
        std::ofstream progress_out(progress_path);
        progress_out << std::setw(4) << progress << std::endl;
        progress_out.close();

    } catch (const std::exception& e) {
        spdlog::error("C++ graph generation failed: {}", e.what());
        progress["status"]["cpp_graph_gen"] = "failed";
        std::ofstream progress_out(progress_path);
        progress_out << std::setw(4) << progress << std::endl;
        progress_out.close();
        return 1;
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> elapsed = end_time - start_time;
    spdlog::info("C++ graph generation finished in {} ms.", elapsed.count());

    return 0;
}

