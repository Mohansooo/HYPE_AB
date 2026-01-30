# HYPE_AB
Hype model for Alberta

# 1. DEM
mrdem30m

# 2. TauDEM
process dem with TauDEM, generating the sub-basins (_watersheds.shp) and river network (_streams.shp)

# 3. datatool
extract the meterological data

···./extract-dataset.sh --dataset=CaSRv3.2 \
  --dataset-dir=/project/rrg-alpie/data/meteorological-data/casrv3.2/ \
  --variable=CaSR_v3.2_P_P0_SFC,CaSR_v3.2_P_TT_09975,CaSR_v3.2_P_UVC_09975,CaSR_v3.2_A_PR0_SFC,CaSR_v3.2_P_FB_SFC,CaSR_v3.2_P_FI_SFC,CaSR_v3.2_P_HU_09975 \
  --output-dir=$SCRATCH/AB_HYPE/datatool-output/ \
  --start-date=2020-01-01 \
  --end-date=2021-01-01 \
  --shape-file="$SCRATCH/delineation-product/AB/AB-basin-watersheds-dissolved.shp" \
  --cache=$SCRATCH/cache/ \
  --prefix="AB_model_" \
  --cluster="$HOME/github-repos/datatool/etc/clusters/drac2.json" \
  --email="m58song@uwaterloo.ca" \
  --submit job···

# 4. gistool
extract the elevation, soil type, and land use data

# 5. easymore
process the meterological data

# 6. hypeflow
prepare for hype input files

# 7. hype
run hype

# 8. calibration
calibrate the hype model
