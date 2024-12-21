#!/bin/bash
#SBATCH --time=5-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/backup/slurm-%j.out
#SBATCH --job-name="backup_simulators"
#SBATCH --partition=tallis
#SBATCH --mem=8G

echo "Backing up data..."

# echo "Backing up data/networks/orig"
# cp -r data/networks/orig /projects/engrit/chackoge/vltanh/backup/networks/

# echo "Backing up data/networks/orig_wo_outliers"
# cp -r data/networks/orig_wo_outliers /projects/engrit/chackoge/vltanh/backup/networks/

# # data/networks/abcd
# echo "Backing up data/networks/abcd+o"
# cp -r data/networks/abcd+o /projects/engrit/chackoge/vltanh/backup/networks/

# # data/networks/abcdta4
# echo "Backing up data/networks/abcdta4"
# cp -r data/networks/abcdta4 /projects/engrit/chackoge/vltanh/backup/networks/

# # data/networks/abcdta4+o
# echo "Backing up data/networks/abcdta4+o"
# cp -r data/networks/abcdta4+o /projects/engrit/chackoge/vltanh/backup/networks/

# # data/networks/abcdta4+o+eL1
# echo "Backing up data/networks/abcdta4+o+eL1"
# cp -r data/networks/abcdta4+o+eL1 /projects/engrit/chackoge/vltanh/backup/networks/

# # data/networks/abcdta4+o+eL2
# echo "Backing up data/networks/abcdta4+o+eL2"
# cp -r data/networks/abcdta4+o+eL2 /projects/engrit/chackoge/vltanh/backup/networks/

# # data/networks/sbm
# echo "Backing up data/networks/sbm"
# cp -r data/networks/sbm /projects/engrit/chackoge/vltanh/backup/networks/

# # data/networks/sbm+o
# echo "Backing up data/networks/sbm+o"
# cp -r data/networks/sbm+o /projects/engrit/chackoge/vltanh/backup/networks/

# # data/networks/sbmmcsprev1
# echo "Backing up data/networks/sbmmcsprev1"
# cp -r data/networks/sbmmcsprev1 /projects/engrit/chackoge/vltanh/backup/networks/

# # data/networks/sbmmcsprev1+o
# echo "Backing up data/networks/sbmmcsprev1+o"
# cp -r data/networks/sbmmcsprev1+o /projects/engrit/chackoge/vltanh/backup/networks/

# # data/networks/sbmmcsprev1+o+eL1
# echo "Backing up data/networks/sbmmcsprev1+o+eL1"
# cp -r data/networks/sbmmcsprev1+o+eL1 /projects/engrit/chackoge/vltanh/backup/networks/

# data/networks/sbmmcsprev1+o+eL2
echo "Backing up data/networks/sbmmcsprev1+o+eL2"
cp -r data/networks/sbmmcsprev1+o+eL2 /projects/engrit/chackoge/vltanh/backup/networks/

# stats
echo "Backing up data/stats"
cp -r data/stats /projects/engrit/chackoge/vltanh/backup/

echo "Done."