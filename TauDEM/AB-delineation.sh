#!/bin/bash

set -e

TAUDEM_BIN="/home/m58song/.local/bin/taudem"
INPUT_DEM="/home/m58song/github-repos/TauDEM/dem/AB2_mrdem-30-dtm.tif"

JOB_ID=${SLURM_JOB_ID:-manual_test}
SCRATCH_DIR="/scratch/m58song/TauDEM_Work_${JOB_ID}"
INTERIM_DIR="${SCRATCH_DIR}/interim"

FINAL_PRODUCT_DIR="/scratch/m58song/delineation-product/AB/"

mkdir -p "$INTERIM_DIR"
mkdir -p "$FINAL_PRODUCT_DIR"
echo "$(basename $0): Working Directory set to: $SCRATCH_DIR"
echo "$(basename $0): Generating geospatial fabric..."

# remove potential pits from the existing DEM file
srun "$TAUDEM_BIN/pitremove" \
  -z "$INPUT_DEM" \
  -fel "$INTERIM_DIR/AB-fel.tif" -v;
echo "$(basename $0): Pit removal done."
echo "Output file is located at: $INTERIM_DIR/AB-fel.tif"

# calculating slope and flow directions using the d8 routing method
srun "$TAUDEM_BIN/d8flowdir" \
  -fel "$INTERIM_DIR/AB-fel.tif" \
  -sd8 "$INTERIM_DIR/AB-sd8.tif" \
  -p "$INTERIM_DIR/AB-fdir.tif";
echo "$(basename $0): Flow direction calculation done"

# calculating contributing areas using the d8 routing method
srun "$TAUDEM_BIN/aread8" \
  -p "$INTERIM_DIR/AB-fdir.tif" \
  -ad8 "$INTERIM_DIR/AB-ad8.tif" -nc;
echo "$(basename $0): Contributing area calculation done"

# calculating grid order, longest flow path, and total
# length of all flow paths
srun "$TAUDEM_BIN/gridnet" \
  -p "$INTERIM_DIR/AB-fdir.tif" \
  -plen "$INTERIM_DIR/AB-plen.tif" \
  -tlen "$INTERIM_DIR/AB-tlen.tif" \
  -gord "$INTERIM_DIR/AB-gord.tif";
echo "$(basename $0): Calculating grid cell orders done"

# assigning channelization threshold of 3000 contributing grid
# cells, or 25 square kilometers:
srun "$TAUDEM_BIN/threshold" \
  -ssa "$INTERIM_DIR/AB-ad8.tif" \
  -src "$INTERIM_DIR/AB-src.tif" \
  -thresh 3000;
echo "$(basename $0): Channelization thresholding done"
  
# delineating watersheds
srun "$TAUDEM_BIN/streamnet" \
  -fel "$INTERIM_DIR/AB-fel.tif" \
  -p "$INTERIM_DIR/AB-fdir.tif" \
  -ad8 "$INTERIM_DIR/AB-ad8.tif" \
  -src "$INTERIM_DIR/AB-src.tif" \
  -ord "$INTERIM_DIR/AB-gord.tif" \
  -tree "$INTERIM_DIR/AB-basin-tree.dat" \
  -coord "$INTERIM_DIR/AB-basin-coord.dat" \
  -net "$INTERIM_DIR/AB-basin-streams.shp" \
  -w "$INTERIM_DIR/AB-watersheds.tif";
echo "$(basename $0): Extracting stream network and watersheds done"

# transforming watershed rasters to polygons using GDAL
gdal_polygonize.py \
  "$INTERIM_DIR/AB-watersheds.tif" \
  -f "ESRI Shapefile" \
  "$INTERIM_DIR/AB-basin-watersheds.shp";
echo "$(basename $0): Polygonizing watershed raster done"

mkdir -p "$FINAL_PRODUCT_DIR"
echo "$(basename $0): Copying files to '$FINAL_PRODUCT_DIR'"

# copying final results under the "delineation-product"
cp "$INTERIM_DIR/AB-watersheds.tif" "$FINAL_PRODUCT_DIR/"
cp "$INTERIM_DIR/AB-basin-streams."* "$FINAL_PRODUCT_DIR/"
cp "$INTERIM_DIR/AB-basin-watersheds."* "$FINAL_PRODUCT_DIR/"
cp "$INTERIM_DIR/AB-basin-tree.dat" "$FINAL_PRODUCT_DIR/"
cp "$INTERIM_DIR/AB-basin-coord.dat" "$FINAL_PRODUCT_DIR/"
echo "$(basename $0): Copying final outcomes"
  
echo "$(basename $0): Delineation finished at $(date)";

exit 0;