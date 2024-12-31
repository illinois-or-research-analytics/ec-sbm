#!/bin/bash
#SBATCH --time=1-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/backup/slurm-%j.out
#SBATCH --job-name="zip_backup"
#SBATCH --partition=tallis
#SBATCH --mem=8G

zip -r data/commdet.zip data/community_detection/
