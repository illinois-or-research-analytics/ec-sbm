input_edgelist=$1
input_clustering=$2
output_dir=$3

if [ ! -f ${input_edgelist} ] || [ ! -f ${input_clustering} ]; then
    echo "The input network or clustering file does not exist."
    exit 1
fi

# Preprocessing: remove outliers

python ec-sbm/clean_outlier.py \
    --input-edgelist ${input_edgelist} \
    --input-clustering ${input_clustering} \
    --output-folder ${output_dir}/emp_wo_o/

# Stage 1: Generation of the synthetic clustered subnetwork

python ec-sbm/generate_clustered.py \
    --input-edgelist ${output_dir}/emp_wo_o/edge.tsv \
    --input-clustering ${output_dir}/emp_wo_o/com.tsv \
    --output-folder ${output_dir}/ecsbm/

# Stage 2: Generation of the synthetic outlier subnetwork

python ec-sbm/generate_outliers.py \
    --input-edgelist ${input_edgelist} \
    --input-clustering ${input_clustering} \
    --output-folder ${output_dir}/ecsbm+o/

python ec-sbm/combine_networks.py \
    --input-edgelist-1 ${output_dir}/ecsbm/edge.tsv \
    --input-edgelist-2 ${output_dir}/ecsbm+o/outlier_edge.tsv \
    --input-clustering ${output_dir}/ecsbm/com.tsv \
    --output-folder ${output_dir}/ecsbm+o/

# Stage 3: Degree correction

python ec-sbm/correct_degree.py \
    --input-edgelist ${output_dir}/ecsbm+o/edge.tsv \
    --ref-edgelist ${input_edgelist} \
    --ref-clustering ${input_clustering} \
    --output-folder ${output_dir}/ecsbm+o+e/

python ec-sbm/combine_networks.py \
    --input-edgelist-1 ${output_dir}/ecsbm+o/edge.tsv \
    --input-edgelist-2 ${output_dir}/ecsbm+o+e/degcorr_edge.tsv \
    --input-clustering ${output_dir}/ecsbm+o/com.tsv \
    --output-folder ${output_dir}/ecsbm+o+e/