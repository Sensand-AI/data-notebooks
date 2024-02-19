#The postgis/postgis image provides tags for running Postgres with PostGIS extensions installed. 
#This image is based on the official postgres image 

#the following are included: postgis, postgis_topology, postgis_tiger_geocoder, postgis_raster, postgis_sfcgal, address_standardizer, address_standardizer_data_us
FROM postgis/postgis:16-3.4

# Set environment variables
ENV POSTGRES_DB=POSTGRES_DB
ENV POSTGRES_USER=POSTGRES_USER
ENV POSTGRES_PASSWORD=POSTGRES_PW


