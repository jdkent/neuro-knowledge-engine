#!/usr/bin/python

import os, shutil

for k in range(2, 51):
    
    comm = "listify_length.optimize_list_len({})".format(k)
    pyfile = open("listify_length_k{:02d}.py".format(k), "w+")
    pyfile.write("#!/bin/python\n\nimport listify_length\n{}".format(comm))
    pyfile.close()
    
    bashfile = open("listify_length_k{:02d}.sbatch".format(k), "w+")

    time = "01-00:00:00"
    if k > 25:
        time = "02-00:00:00"

    lines = ["#!/bin/bash\n",
             "#SBATCH --job-name=k{:02d}_listlen".format(k),
             "#SBATCH --output=logs/k{:02d}_listlen.%j.out".format(k),
             "#SBATCH --error=logs/k{:02d}_listlen.%j.err".format(k),
             "#SBATCH --time={}".format(time),
             "#SBATCH -p aetkin",
             "#SBATCH --mail-type=FAIL",
             "#SBATCH --mail-user=ebeam@stanford.edu\n",
             "module load python/3.6 py-pytorch/1.0.0_py36",
             "srun python3 listify_length_k{:02d}.py".format(k)]
    for line in lines:
        bashfile.write(line + "\n")
    bashfile.close()