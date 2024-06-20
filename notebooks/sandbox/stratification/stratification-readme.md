Little readme for the stratification directory, mostly for Jenna to add notes to.

The stratification process has been split across several notebooks:
- data collection. Using our sensand gis apckage to collect and save the data. This way you don't waste time finding and downloading data every time.
- preprocessing - the data needs to be put in a format that can be used for stratification modellling. This includes:
    - normalising/ scaling the data
    - handling missing data/ nodata
    - stacking the different input data into a single multi-dimensional array
    - making sure all the rasters are aligned correctly in terms of spatial extent and resolution