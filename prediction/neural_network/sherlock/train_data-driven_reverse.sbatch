#!/bin/bash

#SBATCH --job-name=tr_dat_reverse
#SBATCH --output=logs/tr_data-driven_reverse.%j.out
#SBATCH --error=logs/tr_data-driven_reverse.%j.err
#SBATCH --time=07-00:00:00
#SBATCH -p aetkin
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=ebeam@stanford.edu

module load python/3.6 py-pytorch/1.0.0_py36 viz py-matplotlib/3.1.1_py36
srun python3 train_data-driven_reverse.py
