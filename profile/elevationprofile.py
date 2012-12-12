# -*- coding: utf-8 -*-

from flask import Flask
from flask import jsonify
from flask import request
app = Flask(__name__)


from osgeo import gdal
from scipy.ndimage import map_coordinates
from shapely.geometry import shape
from shapely.geometry import asLineString
from shapely.geometry import LineString
from shapely.geometry import Point
from shapely import wkt
from shapely.ops import linemerge

import json
import geojson
import numpy as np
import pyproj
import random

import optparse
import logging
import logging.handlers

from flask import Flask, request, redirect, jsonify, make_response

LOGGER = logging.getLogger('elevationprofile')
DEM_FILE="../data/norge_utsnitt_900913.vrt" # Should be moved to a settingsfile

"""
@app.route('/elevationprofile.kml', methods = ['POST'])
def elevation_profile_wkt():
    
    if request.headers['Content-Type'] == 'text/plain':
        
        try:
            linestrings = wkt.loads(request.data)
        except:
            return "Ikke gyldig KML"
        
        return calcElevProfile(linestrings)
        
    else:
        return "Feil format!"  

@app.route('/elevationprofile.gpx', methods = ['POST'])
def elevation_profile_wkt():
    
    if request.headers['Content-Type'] == 'text/plain':
        
        try:
            linestrings = wkt.loads(request.data)
        except:
            return "Ikke gyldig GPX"
        
        return calcElevProfile(linestrings)
        
    else:
        return "Feil format!"    
"""

@app.route('/elevationprofile.wkt', methods = ['POST'])
def elevation_profile_wkt():
    
    if request.headers['Content-Type'] == 'text/plain':
        
        try:
            linestring = wkt.loads(request.data)
        except:
            return "Ikke gyldig WKT"
            
        return calcElevProfile(linestring)
        
    else:
        return "Feil format!"    


@app.route('/elevationprofile.json', methods = ['POST'])
def elevation_profile_json():

    # Firefox adds charset automatically    
    if request.headers['Content-Type'] == 'application/json' or request.headers['Content-Type'] == 'application/json; charset=UTF-8':   
        try:
            linestring = shape(request.json)
        except:
            return "Ikke gyldig GeoJSON"
        return calcElevProfile(linestring)
    else:
        return "Feil format!"    
        


@app.route("/elevationprofile.test")
def elevation_profile_test():
  
    # Test code to test custom linestring
    lon = 11.21889
    lat = 59.57127
    lon2 = 11.22460
    lat2 = 59.55879
    linestrings = LineString([(lon, lat), (lon2, lat2)])

    return calcElevProfile(linestrings)

   
## Start calculation and creates geojson result    
def calcElevProfile(linestrings):
    
    # Array holding information used in graph
    distArray = []
    elevArray = []
    pointX = []
    pointY = []
        
    # Calculate elevations
    distArray, elevArray, pointX, pointY = calcElev(linestrings)  
        
    # Smooth graph
    elevArray = smoothList(elevArray, 7)  
        
    features = []
    for i in range(len(elevArray)):
        geom = {'type': 'Point', 'coordinates': [pointX[i],pointY[i]]}
        feature = {'type': 'Feature',
                   'geometry': geom,
                   'crs': {'type': 'EPSG', 'properties': {'code':'900913'}},
                   'properties': {'distance': str(distArray[i]), 'elev': str(elevArray[i])}
                   }
        features.append(feature);
        
    geojson = {'type': 'FeatureCollection',
               'features': features}

    return jsonify(geojson)
    
      
#
# Code from http://stackoverflow.com/questions/5515720/python-smooth-time-series-data
#
def smoothList(x,window_len=7,window='hanning'):
    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."
    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."
    if window_len<3:
        return x
    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
    s=np.r_[2*x[0]-x[window_len-1::-1],x,2*x[-1]-x[-1:-window_len:-1]]
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:  
        w=eval('np.'+window+'(window_len)')
    y=np.convolve(w/w.sum(),s,mode='same')

    return y[window_len:-window_len+1]

    
  
def convertGeoLocationToPixelLocation(X, Y, imageData):
    g0, g1, g2, g3, g4, g5 = imageData.GetGeoTransform()
    xGeo, yGeo =  X, Y
    if g2 == 0:
        xPixel = (xGeo - g0) / float(g1)
        yPixel = (yGeo - g3 - xPixel*g4) / float(g5)
    else:
        xPixel = (yGeo*g2 - xGeo*g5 + g0*g5 - g2*g3) / float(g2*g4 - g1*g5)
        yPixel = (xGeo - g0 - xPixel*g1) / float(g2)
    return int(round(xPixel)), int(round(yPixel))

def createRasterArray(ulx, uly, lrx, lry):
    
    source = gdal.Open(DEM_FILE)
    gt = source.GetGeoTransform()
    
    # Calculate pixel coordinates
    upperLeftPixelX, upperLeftPixelY = convertGeoLocationToPixelLocation(ulx, uly, source)
    lowerRightPixelX, lowerRightPixelY = convertGeoLocationToPixelLocation(lrx, lry, source)
    # Get rasterarray
    band_array = source.GetRasterBand(1).ReadAsArray(upperLeftPixelX, upperLeftPixelY , lowerRightPixelX-upperLeftPixelX , lowerRightPixelY-upperLeftPixelY)
    source = None # close raster
    return gt, band_array
    
def calcElev(linestring):

    # Holds coordinates where we check for elevation
    pointArrayX = []
    pointArrayY = []
    # Holds distance according to above coordinates
    distArray = []
    
    
    #
    # Convert line to spherical mercator
    #
    #print "Starter transformering..."
    # Convert to numpy array
    ag = np.asarray(linestring)
    # Extract one array for lon and one for lat
    lon, lat = zip(*ag)
    # Define projections
    #fromProj = pyproj.Proj(init='epsg:3785')
    fromProj = pyproj.Proj(init='epsg:4326')
    toProj = pyproj.Proj(init='epsg:32633')
    # Reproject the line
    x2, y2 = pyproj.transform(fromProj, toProj, lon, lat)
    # Create new numpy array
    a = np.array(zip(x2,y2))
    # Recreate linestring
    projectedLinestrings = asLineString(a)
    #print projectedLinestrings.length
    #print "Slutt transformering..."
    #
    # Set distance for interpolation on line according to length of route
    # - projectedLinestrings.length defines length of route in meter 
    # - stepDist defines how often we want to extract a height value
    #   i.e. stepDist=50 defines that we should extract an elevation value for 
    #   every 50 meter along the route
    stepDist = 0
    if projectedLinestrings.length < 2000: 
        stepDist = 20
    elif projectedLinestrings.length >1999 and projectedLinestrings.length < 4000:
        stepDist = 100
    elif projectedLinestrings.length >3999 and projectedLinestrings.length < 10000:
        stepDist = 100
    else:
        stepDist = 200
        
    
    
    #
    # Make interpolation point along line with stepDist form above.
    # Add these point to arrays.
    #
    step = 0    
    # Trur ikke multilinestringer kommer inn her lenger
    # så koden kan sannsynligvis fjernes
    
    #print "Starter interpolering..."
    if(projectedLinestrings.geom_type == "LineString"):
        #linestring = projectedLinestrings
        while step<projectedLinestrings.length+stepDist:
            point =  projectedLinestrings.interpolate(step)
            # Project back to spherical mercator coordinates
            x, y = pyproj.transform(toProj, pyproj.Proj(init='epsg:3785'), point.x, point.y)
            #x, y = point.x, point.y
            pointArrayX.append(x)
            pointArrayY.append(y)
            distArray.append(step)
            step = step + stepDist
    #print "Slutt interpolering..."
    
    """    
    for coords in projectedLinestrings.coords:
        point  = Point(coords)
        x, y = pyproj.transform(toProj, fromProj, point.x, point.y)    
        pointArrayX.append(x)
        pointArrayY.append(y)
        distArray.append(projectedLinestrings.project(point))
    """
    
    #
    # Convert line to spherical mercator
    #
    #print "Starter transformering..."
    # Convert to numpy array
    ag = np.asarray(linestring)
    # Extract one array for lon and one for lat
    lon, lat = zip(*ag)
    # Define projections
    #fromProj = pyproj.Proj(init='epsg:3785')
    fromProj = pyproj.Proj(init='epsg:4326')
    toProj = pyproj.Proj(init='epsg:3785')
    # Reproject the line
    x2, y2 = pyproj.transform(fromProj, toProj, lon, lat)
    # Create new numpy array
    a = np.array(zip(x2,y2))
    # Recreate linestring
    projectedLinestrings = asLineString(a)
    #print "Slutt transformering..."
    
            
    # Calculate area in image to get
    # Get bounding box of area
    bbox = projectedLinestrings.bounds 
    # Expand the bounding box with 200 meter on each side
    ulx = bbox[0]-200 
    uly = bbox[3]+200
    lrx = bbox[2]+200
    lry = bbox[1]-200
  
    gt, band_array = createRasterArray(ulx, uly, lrx, lry)
    
    
    nx = len(band_array[0])
    ny = len(band_array)

    # Compute mid-point grid spacings
    ax = np.array([ulx + ix*gt[1] + gt[1]/2.0 for ix in range(nx)])
    ay = np.array([uly + iy*gt[5] + gt[5]/2.0 for iy in range(ny)])

    # Create numpy array
    z = np.array(band_array)

    # Set min/max values of image
    ny, nx = z.shape
    xmin, xmax = ax[0], ax[nx-1] #ax[5136] 
    ymin, ymax = ay[ny-1], ay[0] #ay[5144], ay[0]

    
    # Turn these into arrays of x & y coords
    xi = np.array(pointArrayX, dtype=np.float)
    yi = np.array(pointArrayY, dtype=np.float)

    # Now, we'll set points outside the boundaries to lie along an edge
    xi[xi > xmax] = xmax
    xi[xi < xmin] = xmin
    yi[yi > ymax] = ymax
    yi[yi < ymin] = ymin

    # We need to convert these to (float) indicies
    #   (xi should range from 0 to (nx - 1), etc)
    xi = (nx - 1) * (xi - xmin) / (xmax - xmin)
    yi = -(ny - 1) * (yi - ymax) / (ymax - ymin)

    # Interpolate elevation values
    # map_coordinates does cubic interpolation by default, 
    # use "order=1" to preform bilinear interpolation
    elev = map_coordinates(z, [yi, xi], order=1)

    return (distArray, elev, pointArrayX, pointArrayY)
    
if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('-d', '--debug', dest='debug', default=False,
                      help='turn on Flask debugging', action='store_true')

    options, args = parser.parse_args()

    if options.debug:
        LOGGER.info('Running in debug mode')
        app.debug = True
        print "Debug mode"
    else:
        LOGGER.info('Running in production mode')
    app.run()
