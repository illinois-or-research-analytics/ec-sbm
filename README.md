# **Edge Connectivity Stochastic Block Model (EC-SBM)**

## **Table of Contents**

- [Overview](#overview)
- [Usage](#usage)
  - [Short version](#short-version)
  - [Long version](#long-version)
    - [Preprocessing: Cleaning the outliers](#preprocessing-cleaning-the-outliers)
    - [Stage 1: Generation of the synthetic clustered subnetwork](#stage-1-generation-of-the-synthetic-clustered-subnetwork)
    - [Stage 2: Generation of the synthetic outlier subnetwork](#stage-2-generation-of-the-synthetic-outlier-subnetwork)
    - [Stage 3: Degree correction](#stage-3-degree-correction)
- [Installation Guide](#installation-guide)

## **Overview**

This repository contains the implementation of the Edge Connectivity Stochastic Block Model (EC-SBM) for generating synthetic networks based on the empirical network and the empirical clustering.

## **Usage**

### **Input** 

We are given 
* an empirical network `<path/to/empirical>/edge.tsv` 
* an empirical clustering `<path/to/empirical>/com.tsv`.

### **Short version**

**Command** We generate the synthetic network with EC-SBM by running the following command:

```bash
bash scripts/run_ecsbm.sh <path/to/empirical>/edge.tsv <path/to/empirical>/com.tsv <path/to/output/folder>
```

**Output** 

The generated synthetic network is stored in `<path/to/output/folder>/ecsbm+o+e/edge.tsv`. 

There are other intermediate results stored in `<path/to/output/folder>`, which is described in [the long version](#long-version).

**Example**

```
bash scripts/run_ecsbm.sh test/input/cit_hepph/edge.tsv test/input/cit_hepph/com.tsv test/output/cit_hepph
```

### **Long version**

The full pipeline to generate EC-SBM synthetic networks is as followed.

<!-- Note: In this implementation, a network (or subnetwork) is always stored along with the corresponding clustering in a folder with two TSV files `edge.tsv` and `com.tsv`. -->

#### **Preprocessing: Cleaning the outliers** 

**Command** We obtain the clustered subnetwork which does not contain outliers from the input network by running the following command:

```bash
python clean_outlier.py \
    --input-network <path/to/empirical>/edge.tsv \
    --input-clustering <path/to/empirical>/com.tsv \
    --output-folder <path/to/empirical_clustered>
```

**Output**

Important files in `path/to/empirical_clustered`:
* `edge.tsv`: same as `path/to/empirical/edge.tsv` but without the edges with at least 1 outlier as its endpoint
* `com.tsv`: same as `path/to/empirical/com.tsv`

**Example**

```bash
python ec-sbm/clean_outlier.py \
    --input-edgelist test/input/cit_hepph/edge.tsv \
    --input-clustering test/input/cit_hepph/com.tsv \
    --output-folder test/output/cit_hepph/emp_wo_o/
```

#### **Stage 1: Generation of the synthetic clustered subnetwork** 

**Command** We generate the EC-SBM synthetic clustered subnetwork by running the following command:

```bash
python gen_ecsbm.py \
    --input-network <path/to/empirical_clustered>/edge.tsv \
    --input-clustering <path/to/empirical_clustered>/com.tsv \
    --output-folder <path/to/synthetic_clustered>
```

**Output**

Important files in `path/to/synthetic_clustered`:
* `edge.tsv`: edge list of the synthetic network
* `com.tsv`: same as `path/to/empirical_clustered/com.tsv`

Other files in `path/to/synthetic_clustered`:
* `run.log`: log file for the generation of the synthetic clustered subnetwork
* `node_id.tsv`: the i-th line contains the node id of the i-th node in the synthetic network (0-based indexing)
* `com_id.tsv`: the i-th line contains the community id of the i-th node in the synthetic network (0-based indexing)
* `deg.tsv`, `cs.tsv`, `mcs.tsv`, `params.json`: network statistics (degree sequence, community size sequence, minimum cut size sequence, random seed, mixing parameter, etc.)

**Example**

```bash
python ec-sbm/gen_ecsbm.py \
    --input-edgelist test/output/cit_hepph/emp_wo_o/edge.tsv \
    --input-clustering test/output/cit_hepph/emp_wo_o/com.tsv \
    --output-folder test/output/cit_hepph/ecsbm/
```

#### **Stage 2: Generation of the synthetic outlier subnetwork**

**Command**: We generate the synthetic outlier subnetwork by running the following commands:

```bash
python ec-sbm/generate_outliers.py \
    --input-edgelist <path/to/empirical>/edge.tsv \
    --input-clustering <path/to/empirical>/com.tsv \
    --output-folder <path/to/synthetic>

python ec-sbm/combine_networks.py \
    --input-edgelist-1 <path/to/synthetic>/edge.tsv \
    --input-edgelist-2 <path/to/synthetic_clustered>/outlier_edge.tsv \
    --input-clustering <path/to/synthetic>/com.tsv \
    --output-folder <path/to/synthetic>
```

The first command generates the outlier subnetwork. The second command combines the synthetic clustered subnetwork and the synthetic outlier subnetwork to form the synthetic network with outliers.

**Output**

Important files in `path/to/synthetic`:
* `edge.tsv`: edge list of the synthetic network (combination of the synthetic clustered subnetwork generated from Step 1 and the synthetic outlier subnetwork generated in the first command)
* `com.tsv`: same as `path/to/empirical/com.tsv`

Other files in `path/to/synthetic`:
* `outlier_edge.tsv`: edge list of the synthetic outlier network
* `outlier_run.log`: log file for the generation of the synthetic outlier subnetwork (first command)
* `combine_run.log`: log file for the combination of the synthetic clustered subnetwork and the synthetic outlier subnetwork (second command)

**Example**

```bash
python ec-sbm/generate_outliers.py \
    --input-edgelist test/input/cit_hepph/edge.tsv \
    --input-clustering test/input/cit_hepph/com.tsv \
    --output-folder test/output/cit_hepph/ecsbm+o/

python ec-sbm/combine_networks.py \
    --input-edgelist-1 test/output/cit_hepph/ecsbm/edge.tsv \
    --input-edgelist-2 test/output/cit_hepph/ecsbm+o/outlier_edge.tsv \
    --input-clustering test/output/cit_hepph/ecsbm/com.tsv \
    --output-folder test/output/cit_hepph/ecsbm+o/
```

#### **Stage 3: Degree correction** 

**Command** We correct the degrees of the vertices of the synthetic network by running the following commands:

```bash
python ec-sbm/correct_degree.py \
    --input-edgelist <path/to/synthetic>/edge.tsv \
    --ref-edgelist <path/to/empirical>/edge.tsv \
    --ref-clustering <path/to/empirical>/com.tsv \
    --output-folder <path/to/synthetic_degcorr>

python ec-sbm/combine_networks.py \
    --input-edgelist-1 <path/to/synthetic>/edge.tsv \
    --input-edgelist-2 <path/to/synthetic_degcorr>/degcorr_edge.tsv \
    --input-clustering <path/to/synthetic>/com.tsv \
    --output-folder <path/to/synthetic_degcorr>
```

The first command computes the additional edges to add to the synthetic network to correct the degrees of the vertices. The second command combines the synthetic network with the additional edges to form the final synthetic network.

**Output**

Important files in `path/to/synthetic_degcorr`:
* `edge.tsv`: edge list of the synthetic network (combination of the synthetic clustered subnetwork generated from Step 1 and the synthetic outlier subnetwork generated in the first command)
* `com.tsv`: same as `path/to/synthetic/com.tsv`

Other files in `path/to/synthetic_degcorr`:
* `degcorr_edge.tsv`: edge list of the additional edges to add to the synthetic network
* `degcorr_run.log`: log file for the computation of the additional edges to add to the synthetic network (first command)
* `combine_run.log`: log file for the combination of the synthetic clustered subnetwork and the additional edges to form the final synthetic network (second command)

**Example**

```bash
python ec-sbm/correct_degree.py \
    --input-edgelist test/output/cit_hepph/ecsbm+o/edge.tsv \
    --ref-edgelist test/input/cit_hepph/edge.tsv \
    --ref-clustering test/input/cit_hepph/com.tsv \
    --output-folder test/output/cit_hepph/ecsbm+o+e/

python ec-sbm/combine_networks.py \
    --input-edgelist-1 test/output/cit_hepph/ecsbm+o/edge.tsv \
    --input-edgelist-2 test/output/cit_hepph/ecsbm+o+e/degcorr_edge.tsv \
    --input-clustering test/output/cit_hepph/ecsbm+o/com.tsv \
    --output-folder test/output/cit_hepph/ecsbm+o+e/
```

## Installation Guide

Follow the steps in [`scripts/install.sh`](scripts/install.sh) to install the necessary dependencies.
