# -*- coding: utf-8 -*-

'''
    Executing script in command line (zurich_sample.osm as file):
        python audit_city.py zurich_sample.osm -p 1/2
        -> choose between regex variant 1 or 2
    
    Executing script in python command:
        from audit_city import *
        audit("zurich_sample.osm", True/False, 1/2)
        -> results returned as dictionary and directly printed if True
        -> choose between regex variant 1 or 2
'''

import xml.etree.cElementTree as ET
import re
import pprint
import argparse
from collections import defaultdict

def is_city(element):
    '''
    checks if XML element encodes the attribute key that describes a city entry
    '''
    return element.attrib["k"] == "addr:city"

city_variants = defaultdict(set)
def validate_city(element, ver):
    '''
    function uses regular expressions to check for irregularities in addr:city attribute values.
        
    ver: define which regular expression version to use (int)
        
    ver = 1: filters and stores values with "z" at the beginning of the string (captures all variants
             of Zurich) or values consisting of all other entries (captures all other city names) as a set.
        
    ver = 2: filters and stores values consisting of more than one word, seperated by different non-word
             characters as a set. specifying expected nonword characters instead of using \W in regex, in order to
             avoid matching muted vowels represented in unicode (e.g "\xfc" representing "ü" in unicode).
    '''
    if is_city(element):
        if ver == 1:
            zurich_re=re.compile(r"^z.+h$", re.IGNORECASE)
            if zurich_re.search(element.attrib["v"]):
                city_variants["zurich variants"].add(element.attrib["v"])
            else:
                city_variants["other variants"].add(element.attrib["v"])
        elif ver == 2:
            spelling_re=re.compile(r"[-|\.|()|{}|/|:|;|\s]")
            if spelling_re.search(element.attrib["v"]):
                city_variants["spelling variants"].add(element.attrib["v"])



def audit(file,p,ver):
    '''
    audit city name variants. parse over OSM file and execute validate_city() function with specified XML element
    '''
    
    for _,element in ET.iterparse(file):
        if element.tag == "node" or element.tag == "way" or element.tag == "relation":
            for tag in element.iter("tag"):
                validate_city(tag,ver)


    if p==True:
        pprint.pprint(dict(city_variants))
    
    return city_variants



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'auditing OSM file')
    parser.add_argument('file', help='provide osm file (zurich.osm, zurich_sample.osm)')
    parser.add_argument('-p', action="store_true", default=False)
    parser.add_argument('ver', help='specify, which regex expression to use for auditing', type=int)
    args = parser.parse_args()
    
    audit(args.file,args.p,args.ver)
