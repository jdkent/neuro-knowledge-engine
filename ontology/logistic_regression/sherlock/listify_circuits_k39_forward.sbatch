#!/bin/bash

#SBATCH --job-name=k39f_ncircuits
#SBATCH --output=logs/k39_ncircuits_forward.%j.out
#SBATCH --error=logs/k39_ncircuits_forward.%j.err
#SBATCH --time=00-02:00:00
#SBATCH -p aetkin
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=ebeam@stanford.edu

module load python/3.6
srun python3 listify_circuits_k39_forward.py
