"""
Vector data classes and functions.
"""

from . import geometry
from . import xyfile
from . import geojson
from . import gpx
from . import vtk
from . import quadtree
from . import rtree

from .geometry import (Geometry, Point, Line, Polygon,
                       Multipoint, Multiline, Multipolygon)
from .read import (read_geojson, read_shapefile,
                   read_gpx_waypts, read_gpx_tracks, from_shape)
from .shp import write_shapefile
from .gpx import GPX
from .xyfile import load_xy, xyz2array_reg, array2xyz

__all__ = ["geometry", "xyfile", "geojson", "gpx", "vtk",
           "Point", "Line", "Polygon",
           "Multipoint", "Multiline", "Multipolygon",
           "read_geojson", "read_shapefile", "write_shapefile",
           "GPX",
           "load_xy", "xyz2array_reg", "array2xyz"]

