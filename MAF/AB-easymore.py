# loading EASYMORE
#from easymore import easymore # for version 1 and below
from easymore import Easymore # for version 2 and above

# initializing EASYMORE object
# esmr = easymore() # for version 1 and below
esmr = Easymore() # for version 2 and above

# specifying EASYMORE objects
# name of the case; the temporary, remapping and remapped file names include case name
esmr.case_name                = 'HYPE_AB'              
# temporary path that the EASYMORE generated GIS files and remapped file will be saved
esmr.temp_dir                 = '/scratch/m58song/cache/'
# name of target shapefile that the source netcdf files should be remapped to
esmr.target_shp               = '/scratch/m58song/delineation-product/AB/AB-basin-watersheds-dissolved-4326.shp'
esmr.target_shp_ID            = 'DN' # if not provided easymore give ID according to shape order in shapefile
# name of netCDF file(s); multiple files can be specified with *
esmr.source_nc                = '/scratch/m58song/AB_HYPE/datatool-output/AB_model_*.nc'
# name of variables from source netCDF file(s) to be remapped
esmr.var_names                = ['CaSR_v3.2_P_TT_09975', 'CaSR_v3.2_A_PR0_SFC']
# rename the variables from source netCDF file(s) in the remapped files;
# it will be the same as source if not provided
esmr.var_names_remapped       = ['temperature','precipitation']
# name of variable longitude in source netCDF files
esmr.var_lon                  = 'lon'
# name of variable latitude in source netCDF files
esmr.var_lat                  = 'lat'
# name of variable time in source netCDF file; should be always time
esmr.var_time                 = 'time'
# location where the remapped netCDF file will be saved
esmr.output_dir               = '/scratch/m58song/easymore_output/'
# format of the variables to be saved in remapped files,
# if one format provided it will be expanded to other variables
esmr.format_list              = ['f4']
# fill values of the variables to be saved in remapped files,
# if one value provided it will be expanded to other variables
esmr.fill_value_list          = ['-9999.00']
# if required that the remapped values to be saved as csv as well
esmr.save_csv                 = True
esmr.complevel                = 9
# if uncommented EASYMORE will use this and skip GIS tasks, attributes are only to be checked with remapped so can be assured
#esmr.remap_nc                = esmr.temp_dir+esmr.case_name +'_remapping.nc'
#esmr.attr_nc                 = esmr.temp_dir+esmr.case_name +'_attributes.nc'

# execute EASYMORE
esmr.nc_remapper()