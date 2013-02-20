Usage
=====

A simple app to calculate elevation profiles

Raster files should be added in data directory

Test using curl:

Start server like this:
python elevationprofile.py --debug

curl -H "Content-type: application/json" -X POST http://localhost:5000/elevationprofile.json -d @example/example.geojson

curl -H "Content-type: text/plain" -X POST http://localhost:5000/elevationprofile.wkt -d @example/example.wkt

Example use
===========
A web service running this code is available at [kresendo.no](http://verktoy.kresendo.no/hoydeprofil.html), and [turkompisen.no](http://turkompisen.no) an example of an application using it.


Acknowledgements
================

Parts of the elevation profile code was first developed in a cooperation between [Kresendo](http://www.kresendo.no) and the [TG4NP](http://tg4np.eu/) project at the [Western Norway Research Institute](http://www.vestforsk.no/).
