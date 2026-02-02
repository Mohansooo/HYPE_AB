#!/bin/bash
#SBATCH --job-name=AB_easymore
#SBATCH --account=rrg-alpie
#SBATCH --output=%x_%j.log
#SBATCH --error=%x_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=32
#SBATCH --mem=64G
#SBATCH --time=4:00:00

module purge
module restore firmaf
source $HOME/virtual-envs/scienv/bin/activate

python AB-easymore.py