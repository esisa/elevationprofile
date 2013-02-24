A simple app to calculate elevation profiles

Installation
============

elevationprofile uses the Python Flask framework and a handful of other python modules. See `elevationprofile.py` for the modules needed, and use [pip](https://pypi.python.org/pypi/pip) to install them. You may use the provided `runserver.wsgi` to "connect" the app with your webserver.

Usage
=====

Raster files should be added in the `demdata` directory.

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
