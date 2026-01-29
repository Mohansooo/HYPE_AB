# HYPE_AB
Hype model for Alberta

# 1. DEM
mrdem30m

# 2. TauDEM
process dem with TauDEM, generating the sub-basins (_watersheds.shp) and river network (_streams.shp)

# 3. datatool
extract the meterological data

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
