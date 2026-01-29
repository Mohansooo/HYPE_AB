#!/bin/bash
#SBATCH --job-name=AB_Delineation
#SBATCH --account=rrg-alpie
#SBATCH --output=slurm_taudem_%j.log
#SBATCH --error=slurm_taudem_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=64
#SBATCH --mem=128G
#SBATCH --time=6:00:00

module purge
module restore firmaf
module load gdal/3.7.2 cmake/3.31.0 gcc/12.3

export PATH="/home/m58song/.local/bin/taudem:$PATH" 

echo "Current Node: $(hostname)"
echo "Allocated Memory: $SLURM_MEM_PER_NODE MB"
which aread8
which gdal_polygonize.py

chmod +x AB-delineation.sh
./AB-delineation.sh