# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import re
import pprint
import argparse
from collections import defaultdict

invalid_time = defaultdict(list)
def validate_time(element):
    '''
    function uses regular expression to check if the attribute timestamp (in first level element node, way,
    relation) complies with a valid format for representing dates time. Valid formats are:
    
    1. YYYY-MM-DD hh:mm:ss
    2. YYYY-MM-DDThh:mm:ssZ
    
    Y: Year, M: Month, D: Day, h: Hour, m: Minute, s: second
    T seperated date and time and Z designates UTC (Coordinated Universal Time) time
    '''
    
    time_re = re.compile(r"\d{4}-\d{2}-\d{2}(T|\s)?\d{2}:\d{2}:\d{2}Z?")
    match_time = time_re.search(element.attrib["timestamp"])
    if not match_time:
        invalid_time["invalid time format"].append(element.attrib["timestamp"])


def audit(file,p):
    '''
    audit timestamp. parse over OSM file and execute validate_time() function with specified XML element
    '''
    for _,element in ET.iterparse(file):
        if element.tag == "node" or element.tag == "way" or element.tag == "relation":
            validate_time(element)


    if p==True:
        pprint.pprint(dict(invalid_time))
    
    return invalid_time



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'auditing OSM file')
    parser.add_argument('file', help='provide osm file (zurich.osm, zurich_sample.osm)')
    parser.add_argument('-p', action="store_true", default=False)
    args = parser.parse_args()
    audit(args.file,args.p)