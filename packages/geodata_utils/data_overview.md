
# Data Overview

## Soil Data SLGA

Description: Range of digital soil attribute products as Soil and Landscape Grid of Australia (SLGA). Each product contains six digital soil attribute maps, and their upper and lower confidence limits, representing the soil attribute at six depths: 0-5cm, 5-15cm, 15-30cm, 30-60cm, 60-100cm and 100-200cm. 

Resolution: 3 arcsec

Source: https://www.clw.csiro.au/aclep/soilandlandscapegrid/ProductDetails-SoilAttributes.html

License: Creative Commons Attribution 3.0 (CC By)

Attribution: CSIRO Australia, TERN (University of Queensland), and Geoscience Australia

Layernames:

- 'Bulk_Density' :
   - Title: Bulk Density (whole earth)
   - Description: Bulk Density of the whole soil (including coarse fragments) in mass per unit volume by a method equivalent to the core method
   - Unit: g/cm3
- 'Organic_Carbon' :
   - Title: Organic Carbon
   - Description: Mass fraction of carbon by weight in the < 2 mm soil material as determined by dry combustion at 900 Celcius
   - Unit: %
- 'Clay' :
   - Title: Clay
   - Description: < 2 um mass fraction of the < 2 mm soil material determined using the pipette method
   - Unit: %
- 'Silt' :
   - Title: Silt
   - Description: 2-20 um mass fraction of the < 2 mm soil material determined using the pipette method
   - Unit: %
- 'Sand' :
   - Title: Sand
   - Description: 20 um - 2 mm mass fraction of the < 2 mm soil material determined using the pipette method
   - Unit: %
- 'pH_CaCl2' :
   - Title: pH (CaCl2)
   - Description: pH of 1:5 soil/0.01M calcium chloride extract
   - Unit: none
- 'Available_Water_Capacity' :
   - Title: Available Water Capacity
   - Description: Available water capacity computed for each of the specified depth increments
   - Unit: %
- 'Total_Nitrogen' :
   - Title: Total Nitrogen
   - Description: Mass fraction of total nitrogen in the soil by weight
   - Unit: %
- 'Total_Phosphorus' :
   - Title: Total Phosphorus
   - Description: Mass fraction of total phosphorus in the soil by weight
   - Unit: %
- 'Effective_Cation_Exchange_Capacity' :
   - Title: Effective Cation Exchange Capacity
   - Description: Cations extracted using barium chloride (BaCl2) plus exchangeable H + Al
   - Unit: meq/100g
- 'Depth_of_Regolith' :
   - Title: Depth of Regolith
   - Description: Depth to hard rock. Depth is inclusive of all regolith.
   - Unit: m
- 'Depth_of_Soil' :
   - Title: Depth of Soil
   - Description: Depth of soil profile (A & B horizons)
   - Unit: m


## National Digital Elevation Model 1 Second Hydrologically Enforced

Description: Digital Elevation Model (DEM) of Australia derived from STRM with 1 Second Grid - Hydrologically Enforced

Updates: None

Resolution: native: 1 arcsec

Source: https://www.clw.csiro.au/aclep/soilandlandscapegrid/ProductDetails.html

License: Creative Commons Attribution 4.0 International (CC BY 4.0)

Attribution: Commonwealth of Australia (Geoscience Australia)

Layernames:

- 'DEM_1s'
   - Title: DEM SRTM 1 Second Hydro Enforced
   - Description: The 1 second SRTM derived hydrologically enforced DEM (DEM-H Version 1.0) is a 1 arc second (~30 m) gridded digital elevation model (DEM) that has been hydrologically conditioned and drainage enforced. The DEM-H captures flow paths based on SRTM elevations and mapped stream lines, and supports delineation of catchments and related hydrological attributes.