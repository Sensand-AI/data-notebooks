## Directory structure
This is  adraft directory structure for the sandbox (to be renamed development) notebook directory.

|--data
|   |-input-data
|   |-output-data
|   |-test-data

Proposed folders/domains:
 - soil (this will be for the SLGA data. It could be expanded to a broader 'geology' category later on if needed)
 - landscape
 - land cover
 - cadastral (want a better name for this folder, but for now its govt cadastra related data)
 - nonspatial_to_spatial (need better name, but this is for notebooks that take things like practice data, soil tests, that are stored in non-spatial formats like csv, and attach them to spatial data like points/ polygons)
 - climate and weather
 - basemaps
 - spectral indices
 - testbed (nothing in here should be linked or moved to staging. It's a place to keep short-term experimental notebooks that are ephemeral)
 - education and internal resources (may need to go in a separate repo later on)
 - templates (permanent resources that are used as the basis/starting point for creating and testing notebooks. e.g. a viz notebook to check outputs are in the expected location, right CRS)


## File naming conventions
TODO: once folder and domain structure settled on, establish notebook naming convention and re-name existing notebooks

Digital Earth Austrealia adopts a naming convention where they use the source, sensor, and data product:

`ga_ls9c_ard_3` is geoscience australia's (ga) landsat 9 level C processed data (ls9c) analysis ready data (ard) version 3.
`ga_srtm_dem1sv1_0` is geoscience australia's (`ga`) shuttle radar topography mission (`srtm`) digital elevation model (`dem1sv1`) verion 0.

The pattern is:
 - source (either organisation, satellite or sensor)
 - name of the dataset/ parent dataset (e.g. Sentinel-2 l2A, SRTM, Landsat-9 Lc)
 - the final processed dataset (dem, ard, or spectral index)
 - verion number

 So an example notebook name could be:
 `tern_slga_soc_2` for the TERN SLGA soil organis carbon version 2.
 This pattern is meant for naming files, so it won't translate perfectly to a notebook. The SLGA data contains 11 datasets, of which SOC is one of them, but all can be collected in one notebook. So, it may not work to include `soc` in the notebook name if multiple data layers can be retrieved with the notebook.