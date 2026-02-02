import alive_progress
from contextlib import contextmanager

# 定义一个假的进度条，什么都不做，只保证代码不报错
@contextmanager
def dummy_bar(total=None, *args, **kwargs):
    # 定义一个假的 ticker 函数
    def ticker(*args, **kwargs):
        pass
    yield ticker

alive_progress.alive_bar = dummy_bar

# load packages
import lib.hypeFlow as hf
import os
import glob
import sys
import geopandas as gpd
import pandas as pd
import numpy as np

def fast_sort_geodata(geodata):
    print("  Running Robust Topological Sort...")
    
    # --- 1. 驱逐幽灵 ID (关键修复) ---
    original_len = len(geodata)
    geodata = geodata[geodata['subid'] > 0].copy()
    if len(geodata) < original_len:
        print(f"  Removed {original_len - len(geodata)} invalid rows (ID <= 0).")

    # --- 2. 拓扑排序 ---
    try:
        import networkx as nx
        
        G = nx.DiGraph()
        # 只添加存在的节点
        valid_ids = set(geodata['subid'].values)
        G.add_nodes_from(valid_ids)
        
        edges = []
        for _, row in geodata.iterrows():
            u = row['subid']
            v = row['maindown']
            # 只有下游也在 valid_ids 里才算边 (排除流向出口的情况)
            if v in valid_ids and v != u:
                G.add_edge(u, v)

        # 破环逻辑
        cycles_found = 0
        while True:
            try:
                cycle = nx.find_cycle(G, orientation='original')
                cycles_found += 1
                u_bad, v_bad = cycle[-1][:2]
                print(f"      ⚠️ CRITICAL: Cycle detected! Breaking link: {u_bad} -> {v_bad}")
                G.remove_edge(u_bad, v_bad)
                geodata.loc[geodata['subid'] == u_bad, 'maindown'] = 0
            except nx.NetworkXNoCycle:
                break
        
        if cycles_found > 0:
            print(f"      ✅ Fixed {cycles_found} cycles.")
            
        sorted_ids = list(nx.topological_sort(G))
        
        # 重排
        order_map = {subid: i for i, subid in enumerate(sorted_ids)}
        geodata['sort_order'] = geodata['subid'].map(order_map)
        geodata = geodata.sort_values(by='sort_order').drop(columns=['sort_order']).reset_index(drop=True)
        
        # --- 3. 最终自检 (Self-Check) ---
        print(" Verifying sort order...")
        id_to_idx = {sid: i for i, sid in enumerate(geodata['subid'])}
        errors = 0
        for i, row in geodata.iterrows():
            down = row['maindown']
            if down in id_to_idx:
                down_idx = id_to_idx[down]
                if down_idx <= i: # 下游出现在了上游前面/平行
                    print(f"      ❌ SORT ERROR: Basin {row['subid']} flows to {down}, but {down} is at index {down_idx} (Current {i})")
                    errors += 1
        
        if errors == 0:
            print(f"      ✅ Verification Passed: 100% Upstream -> Downstream.")
        else:
            print(f"      ⚠️ Verification FAILED with {errors} errors. HYPE will crash.")

        return geodata

    except ImportError:
        print("      -> NetworkX not found. Returning unsorted data (Not recommended).")
        return geodata

hf.sort_geodata = fast_sort_geodata
print("🔧 Patch applied: Replaced slow sort algorithm with fast version.")


#cache directory
cache_dir = '/scratch/m58song/cache/'
os.chdir(cache_dir)

# domain subbasins and rivers
raw_subbasins   = '/scratch/m58song/delineation-product/AB/AB-basin-watersheds-dissolved-4326.shp'
rivers_shapefile = '/scratch/m58song/delineation-product/AB/AB-basin-streams.shp'

#subbasin area
gdf = gpd.read_file(raw_subbasins)
gdf['calc_area'] = gdf.to_crs(epsg=3979).area.astype('int64')

if 'DN' in gdf.columns:
    print("   Renaming column 'DN' to 'ID' to match NetCDF data...")
    gdf = gdf.rename(columns={'DN': 'ID'})

fixed_subbasins = '/scratch/m58song/AB_HYPE/temp_subbasins_with_area.shp'
gdf.to_file(fixed_subbasins)

#river
riv_gdf = gpd.read_file(rivers_shapefile)

cols_to_drop = ['DSContArea', 'USContArea', 'Up_Cell', 'Down_Cell']
existing_drop_cols = [c for c in cols_to_drop if c in riv_gdf.columns]
if existing_drop_cols:
    print(f"   -> Dropping corrupted columns: {existing_drop_cols}")
    riv_gdf = riv_gdf.drop(columns=existing_drop_cols)

if 'LINKNO' in riv_gdf.columns:
    print("   -> Found 'LINKNO', renaming to 'ID'...")
    riv_gdf = riv_gdf.rename(columns={'LINKNO': 'ID'})
elif 'ID' in riv_gdf.columns:
    print("   -> 'ID' column already exists.")
else:
    print(f"ERROR: Could not find 'LINKNO' or 'ID'. Available columns: {riv_gdf.columns.tolist()}")
    sys.exit(1)

if 'Slope' in riv_gdf.columns:
    print("   -> Renaming 'Slope' to 'slope' (Case mismatch fix)...")
    riv_gdf = riv_gdf.rename(columns={'Slope': 'slope'})

if 'slope' not in riv_gdf.columns:
    print(f"❌ Critical: No 'slope' column found even after fix. Columns: {riv_gdf.columns.tolist()}")
    sys.exit(1)

fixed_rivers = os.path.join(cache_dir, 'temp_rivers_fixed.shp')
riv_gdf.to_file(fixed_rivers)
print(f"Shapefiles fixed and saved.")

# inputs
# Set the folder path where the easymore mapped nc files are located
easymore_output = '/scratch/m58song/easymore_output/'
# provide the output path where the hype setup is written
output_path = '/home/m58song/AB_HYPE/HYPE/'
timeshift = -7 # time shift in hours
forcing_units= {
    # required variable # name of var in input data, units in input data, required units for HYPE
    'temperature': {'in_varname':'temperature', 'in_units':'celsius', 'out_units': 'celsius'},
    'precipitation': {'in_varname':'precipitation','in_units':'m/hr', 'out_units': 'mm/day'},
}
#mapping geofabric fields to model names
geofabric_mapping ={
    'basinID': {'in_varname':'ID'},
    'nextDownID': {'in_varname':'DSLINKNO'},
    'area': {'in_varname':'calc_area', 'in_units':'m^2', 'out_units':'m^2'},
    'rivlen': {'in_varname':'Length', 'in_units':'m', 'out_units':'m'}
}
# path where all gistool outputs are saved
gistool_output = '/scratch/m58song/AB_HYPE/gistool-output'
frac_threshold = 0.05 # fraction to exclude landcover with coverage less than this value
# spinup period in days
spinup_days = 100

nc_files_found = glob.glob(os.path.join(easymore_output, '*.nc'))
num_files = len(nc_files_found)

print(f"Checking input files in: {easymore_output}")
if num_files == 0:
    print("no .nc files")
    sys.exit(1) 
else:
    print(f" Find {num_files} NetCDF files...")

temp_files = glob.glob('forcing_batch_*.nc') + ['merged_forcing.nc']

for f in temp_files:
    if os.path.exists(f):
        os.remove(f)

print("Step 1: Writing Forcing...")
hf.write_hype_forcing(easymore_output, timeshift, forcing_units, geofabric_mapping, output_path)

csv_files = glob.glob(os.path.join(gistool_output, '**/*.csv'), recursive=True)

if not csv_files:
    print(f"⚠️ Warning: No CSV files found in {gistool_output}")

for csv_file in csv_files:
    try:
        df = pd.read_csv(csv_file)
        modified = False
        filename = os.path.basename(csv_file).lower()
        
        # 1. DN to ID
        if 'DN' in df.columns:
            if 'ID' not in df.columns:
                print(f"   Fixing {filename}: Renaming 'DN' to 'ID'")
                df = df.rename(columns={'DN': 'ID'})
                modified = True
        
        # 2. soil majority
        if 'soil' in filename:
            exclude = ['ID', 'DN', 'COUNT', 'AREA', 'SUM', 'MEAN', 'MIN', 'MAX', 'RANGE', 'STD', 'VARIETY', 'MAJORITY', 'MINORITY', 'MEDIAN']
            data_cols = [c for c in df.columns if str(c).upper() not in exclude and c != 'majority']
            
            if len(data_cols) > 0:
                print(f"   Fixing Soil {filename}: Calculating 'majority'...")
                maj = df[data_cols].apply(pd.to_numeric, errors='coerce').idxmax(axis=1)
                df['majority'] = pd.to_numeric(maj, errors='coerce').fillna(1).astype(int)
                modified = True
            elif 'majority' not in df.columns:
                df['majority'] = 1
                modified = True

        # 3. elevation majority / mean
        elif 'elv' in filename or 'elevation' in filename:
            mean_cols = [c for c in df.columns if 'mean' in c.lower()]
            
            if mean_cols:
                target_col = mean_cols[0] 
                print(f"   Fixing Elevation {filename}: Found Mean column '{target_col}', mapping to 'majority'...")
                df['majority'] = df[target_col] 
                modified = True
            elif 'majority' not in df.columns:
                print(f"      -> Warning: No 'Mean' column found in {filename}. Available: {df.columns.tolist()}")
                df['majority'] = 0 
                modified = True

        if df.isnull().values.any():
            print(f"      -> Found NaN values in {filename}. Filling with -9999.")
            df = df.fillna(-9999)
            modified = True

        if modified:
            df.to_csv(csv_file, index=False)
            print(f"      -> Saved {filename}")
        else:
            print(f"   Skipping {filename}")
            
    except Exception as e:
        print(f"   Error processing {csv_file}: {e}")

print("Step 2: Writing GeoData...")
hf.write_hype_geo_files(gistool_output, fixed_subbasins, fixed_rivers, frac_threshold, geofabric_mapping, output_path)

print("Step 3: Writing Parameters...")
hf.write_hype_par_file(output_path)

print("Step 4: Writing Info...")
hf.write_hype_info_filedir_files(output_path, spinup_days)

print("✅ All Done! HYPE model files generated successfully.")
