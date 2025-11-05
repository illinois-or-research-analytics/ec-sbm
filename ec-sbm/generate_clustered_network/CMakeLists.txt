cmake_minimum_required(VERSION 3.16)
project(GraphGenerator CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Add nlohmann/json for JSON support ---
include(FetchContent)
FetchContent_Declare(
  nlohmann_json
  GIT_REPOSITORY https://github.com/nlohmann/json.git
  GIT_TAG v3.11.3
)
FetchContent_MakeAvailable(nlohmann_json)
# ---

# Find required libraries
find_package(Eigen3 3.3 REQUIRED NO_MODULE)
find_package(cxxopts REQUIRED)
find_package(spdlog REQUIRED)

# --- C++ Setup Executable ---
add_executable(setup setup.cpp) 
target_link_libraries(setup
    PRIVATE
    Eigen3::Eigen
    cxxopts::cxxopts
    spdlog::spdlog
    nlohmann_json::nlohmann_json 
)
target_include_directories(setup
    PRIVATE
    ${EIGEN3_INCLUDE_DIR}
    ${CXXOPTS_INCLUDE_DIRS}
    ${SPDLOG_INCLUDE_DIRS}
    ${nlohmann_json_SOURCE_DIR}/include
)

# --- C++ Graph Generation Executable ---
add_executable(generate_graphs generate_graphs.cpp) 
target_link_libraries(generate_graphs
    PRIVATE
    Eigen3::Eigen
    cxxopts::cxxopts
    spdlog::spdlog
    nlohmann_json::nlohmann_json
)
target_include_directories(generate_graphs
    PRIVATE
    ${EIGEN3_INCLUDE_DIR}
    ${CXXOPTS_INCLUDE_DIRS}
    ${SPDLOG_INCLUDE_DIRS}
    ${nlohmann_json_SOURCE_DIR}/include
)


