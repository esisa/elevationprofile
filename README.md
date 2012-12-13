elevationprofile
================

A simple app to calculate elevation profiles

Raster files should be added in data directory

Test using curl:

curl -H "Content-type: application/json" -X POST http://localhost:5000/elevationprofile.json -d @example/example.geojson

curl -H "Content-type: text/plain" -X POST http://localhost:5000/elevationprofile.wkt -d @example/example.wkt


