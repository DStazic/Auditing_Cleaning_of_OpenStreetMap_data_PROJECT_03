# -*- coding: utf-8 -*-

'''
    Executing script in command line (zurich_sample.osm as file):
        python audit_coordinates.py zurich_sample.osm -p
    
    Executing script in python command:
        from audit_coordinates import *
        audit("zurich_sample.osm", True/False)
        -> results returned as dictionary and directly printed if True
'''

import xml.etree.cElementTree as ET
import re
import pprint
import argparse
from collections import defaultdict

invalid_coordinates = defaultdict(list)

def validate_coordinates(element):
    '''
    checks if coordinate values (lat or lon attributes in first level element node) can be converted to float type.
    Non-valid entries are stored in the set invalid_coordinates.
    '''
    if "lat" in element.attrib.keys() and "lon" in element.attrib.keys():
        try:
            int(element.attrib["lat"])
            int(element.attrib["lon"])
        except ValueError:
            try:
                float(element.attrib["lat"])
                float(element.attrib["lon"])
            except ValueError:
                invalid_coordinates["invalide coordinates"].append((element.attrib["lat"],element.attrib["lon"]))


def audit(file,p):
    '''
    audit coordinates. parse over OSM file and execute validate_coordinates() function with specified XML element
    '''
    for _,element in ET.iterparse(file):
        if element.tag == "node":
            validate_coordinates(element)


    if p==True:
        pprint.pprint(dict(invalid_coordinates))
    
    return invalid_coordinates



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'auditing OSM file')
    parser.add_argument('file', help='provide osm file (zurich.osm, zurich_sample.osm)')
    parser.add_argument('-p', action="store_true", default=False)
    args = parser.parse_args()
    audit(args.file,args.p)