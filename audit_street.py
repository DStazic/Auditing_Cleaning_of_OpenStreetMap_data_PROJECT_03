# -*- coding: utf-8 -*-

'''
    Executing script in command line (zurich_sample.osm as file):
        python audit_street.py zurich_sample.osm -p
    
    Executing script in python command:
        from audit_street import *
        audit("zurich_sample.osm", True/False)
        -> results returned as dictionary and directly printed if True
'''

import xml.etree.cElementTree as ET
import re
import pprint
import argparse
from collections import defaultdict


street_expected = ["Strasse", "Weg", "Platz", "Allee", "Tor", "Gasse", "Ufer", "Berg", "Steig", "Bach",\
                   "Steg", "Ring", "Halde", "Hof", "Rain"]


invalid_street = defaultdict(set)

def is_street(element):
    '''
    checks if XML element encodes the attribute key that describes a street name
    '''
    return element.attrib["k"] == "addr:street"

def find_insertions(street_name, street_expected):
    '''
    function uses a recursive approach to check for misspelling in street names by insertion of word-characters. 
    Identification of misspelling is restricted to the street type within street names. Expected street types are
    defined in the "street_expected" list.
    
    '''
    
    def recursive_search(street_name_iter, street_expected, insertion = 0, path = "", current_letter = "", next_letter = ""):
        
        # define current and next letter until reaching end of string. In this case here both variables are the same
        try:
            current_letter = street_name_iter[0]
            next_letter = street_name_iter[1]
        except IndexError:
            next_letter = current_letter
        
        if path == "":
            path = path + current_letter
        
        # check if path matches any of the expected street names and if same successive letters occured
        #(insertion > 1)
        if (sum([path.lower() == street_type.lower() for street_type in street_expected]) == 1) and insertion > 0:
            return path
                
        # no insertion found if end of street name reached
        if len(street_name_iter) == 1:
            return None
    
        # extends path if next letter different from current letter
        if next_letter != path[-1]:
            path = path + next_letter
            return recursive_search(street_name_iter[1:], street_expected, insertion, path, current_letter\
                                    ,next_letter)
        
        # specific case of path extension
        # Ignores ss in strasse (correct spelling) as insertion. Insertions after the first s in strasse (sstrasse)
        # will be ignored as well, because successive s is common in german language and, thus, many street names
        # would be returned, for which it is not immediately clear whether the spelling is correct or
        # incorrect. E.g both "Heliosstrasse" and "Heliostrasse" are semantically valid!!
        if next_letter == "s" and ("ss" not in path):
            path = path + next_letter
            return recursive_search(street_name_iter[1:], street_expected,insertion, path, current_letter\
                                        ,next_letter)

        insertion += 1
        return recursive_search(street_name_iter[1:], street_expected, insertion, path, current_letter,next_letter)

    for i in range(len(street_name)):
        street_name_iter = street_name[i:]
        match = recursive_search(street_name_iter, street_expected)
        if match != None:
            invalid_street["insertion in name"].add(street_name)

def validate_street(street_name):
    '''
    uses regular expression to return street names that match at least the first 2 word-characters of any of the
    expected street types, optionally extended for 3-4 additional word-characters, at the end of the string, but 
    only if street name has no match with expected street types (street_expected list). Additionally regular 
    expression is used to return street names containing digits or street names consisting of two words
    (separated by ",")
    
    '''
    
    strasse_re = re.compile(r"st\w{0,4}\.?$", re.IGNORECASE)
    other_street_types_re = re.compile(r"(we|pl|al|ga|st|be|ba|ri|ra|ha)\w{0,3}\.?$", re.IGNORECASE)
    digit_re = re.compile(r"\d")
    
    first_match = 0
    for name in street_expected:
        street_types_re = re.compile("{}$".format(name), re.IGNORECASE)
        match = street_types_re.search(street_name)
        if match:
            first_match += 1

    match_str = strasse_re.search(street_name)
    match_other = other_street_types_re.search(street_name)
    match_digit = digit_re.search(street_name)
    
    if (len(street_name.split(",")) != 1):
        invalid_street["array_type"].add(street_name)
    
    elif first_match == 0 and  match_str:
        invalid_street["deletion/abreviation in strasse"].add(street_name)

    elif first_match == 0 and match_other:
        invalid_street["deletion/abreviation in other types"].add(street_name)
    
    elif match_digit:
        invalid_street["digits in name"].add(street_name)





def audit(file,p):
    '''
    audit street names. parse over OSM file and execute validate_street() and find_insertions() functions with 
    specified XML element if the element contains a tag element with street information.
    '''
    for _,element in ET.iterparse(file):
        if element.tag == "node" or element.tag == "way" or element.tag == "relation":
            for tag in element.iter("tag"):
                if is_street(tag):
                    find_insertions(tag.attrib["v"], street_expected)
                    validate_street(tag.attrib["v"])


    if p==True:
        pprint.pprint(dict(invalid_street))
    
    return invalid_street



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'auditing OSM file')
    parser.add_argument('file', help='provide osm file (zurich.osm, zurich_sample.osm)')
    parser.add_argument('-p', action="store_true", default=False)
    args = parser.parse_args()
    audit(args.file,args.p)
