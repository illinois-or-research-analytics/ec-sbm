cmake_minimum_required(VERSION 3.16)
project(GraphGenerator CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# --- Fetch Compatible Libraries (fmt, spdlog, json) ---
# This is the standard, modern way to handle dependencies.
# It guarantees we get versions that work together, avoiding system conflicts.
include(FetchContent)

# Fetch Eigen (v3.4.0)
FetchContent_Declare(
  Eigen3
  GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
  GIT_TAG 3.4.0
)
FetchContent_MakeAvailable(Eigen3)

# Fetch cxxopts (v3.1.1)
FetchContent_Declare(
  cxxopts
  GIT_REPOSITORY https://github.com/jarro2783/cxxopts.git
  GIT_TAG v3.1.1
)
FetchContent_MakeAvailable(cxxopts)

# Fetch {fmt} (v9.1.0)
FetchContent_Declare(
  fmt
  GIT_REPOSITORY https://github.com/fmtlib/fmt.git
  GIT_TAG 9.1.0 # A stable version compatible with spdlog v1.11.0
)
FetchContent_MakeAvailable(fmt)

# Fetch spdlog (v1.11.0)
FetchContent_Declare(
  spdlog
  GIT_REPOSITORY https://github.com/gabime/spdlog.git
  GIT_TAG v1.11.0 # A stable version
)
FetchContent_MakeAvailable(spdlog)

# Fetch nlohmann_json (which we were already doing)
FetchContent_Declare(
  nlohmann_json
  GIT_REPOSITORY https://github.com/nlohmann/json.git
  GIT_TAG v3.11.3
)
FetchContent_MakeAvailable(nlohmann_json)


# --- Build Executable: setup ---
add_executable(setup setup.cpp)
target_link_libraries(setup
  PRIVATE
  Eigen3::Eigen
  cxxopts::cxxopts
  nlohmann_json::nlohmann_json
  spdlog::spdlog # This now links both spdlog and fmt
)


# --- Build Executable: generate_graphs ---
add_executable(generate_graphs generate_graphs.cpp)
target_link_libraries(generate_graphs
  PRIVATE
  Eigen3::Eigen
  cxxopts::cxxopts
  nlohmann_json::nlohmann_json
  spdlog::spdlog # This now links both spdlog and fmt
)

