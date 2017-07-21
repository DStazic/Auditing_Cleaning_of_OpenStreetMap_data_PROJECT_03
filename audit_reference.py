# -*- coding: utf-8 -*-

'''
    Executing script in command line (zurich_sample.osm as file):
        python audit_reference.py street_names_zipcodes_zurich_update -p
    
    Executing script in python command:
        from audit_reference import *
        audit("street_names_zipcodes_zurich_update", "ref/crossref_1/crossref_2")
        -> results directly printed
'''

import re
from collections import defaultdict
from audit_street import*
import pprint
import argparse
import pandas as pd
import csv


# expected combinations of districts and quarters
expected_district_quartes = {"Kreis 1" : ["Rathaus", "Hochschulen", "Lindenhof", "City"],
                             "Kreis 2" : ["Wollishofen", "Leimbach", "Enge"],
                             "Kreis 3" : ["Alt-Wiedikon", "Friesenberg", "Sihlfeld"],
                             "Kreis 4" : ["Werd", "Langstrasse", "Hard"],
                             "Kreis 5" : ["Gewerbeschule", "Escher Wyss"],
                             "Kreis 6" : ["Unterstrass", "Oberstrass"],
                             "Kreis 7" : ["Fluntern", "Hottingen", "Hirslanden", "Witikon"],
                             "Kreis 8" : ["Seefeld", "Mühlebach", "Weinegg"],
                             "Kreis 9" : ["Albisrieden", "Altstetten"],
                             "Kreis 10" : ["Höngg", "Wipkingen"],
                             "Kreis 11" : ["Affoltern", "Oerlikon", "Seebach"],
                             "Kreis 12" : ["Saatlen", "Schwamendingen Mitte", "Hirzenbach"]}

# expected combinations of quarters and postcodes
expected_quarters_postcodes = {"Affoltern" : 8046,
                               "Albisrieden" : 8047,
                               "Alt-Wiedikon" : 8003,
                               "Altstetten" : 8048,
                               "City" : 8001,
                               "Enge" : 8002,
                               "Escher Wyss" : 8005,
                               "Fluntern" : 8044,
                               "Friesenberg" : 8045,
                               "Gewerbeschule" : 8005,
                               "Hard" : 8004,
                               "Hirslanden" : 8032,
                               "Hirzenbach" : 8051,
                               "Hochschulen" : 8001,
                               "Höngg" : 8049,
                               "Hottingen" : 8032,
                               "Langstrasse" : 8004,
                               "Leimbach" : 8041,
                               "Lindenhof" : 8001,
                               "Mühlebach" : 8008,
                               "Oberstrass" : 8006,
                               "Oerlikon" : 8050,
                               "Rathaus" : 8001,
                               "Saatlen" : 8050,
                               "Schwamendingen Mitte" : 8051,
                               "Seebach" : 8052,
                               "Seefeld" : 8008,
                               "Sihlfeld" : 8003,
                               "Unterstrass" : 8006,
                               "Weinegg" : 8008,
                               "Werd" : 8004,
                               "Wipkingen" : 8037,
                               "Witikon" : 8053,
                               "Wollishofen" : 8038}

# use only street_names_zipcodes_zurich_update file with audit_district_quarter_crossref() to avoid KeyError
# (in the original file wrong names for some districts)

def audit_reference_data(file):
    '''
    audit street names in the reference dataset using functions from audit_street.py script and check
    for duplicates in street names. for districts and quarters each set is returned
    
    file: either "street_names_zipcodes_zurich" or "street_names_zipcodes_zurich_update"
    '''
    data = pd.read_csv(file, dtype=str)
    #none_unique_street = defaultdict(list)
    for colname in data.columns:
        if colname == "street":
            data["street"].apply(lambda name: [validate_street(name), find_insertions(name, street_expected)])
                
        else:
            print "auditing {}".format(colname)
            print pd.unique(data[colname]).tolist()

    
    print "auditing street names"
    pprint.pprint(dict(invalid_street))
    print "street name duplicates"
    # use bool indexing with .duplicated() method to detect street duplicates. use .unique() method to return
    # the set of non-unique streets (if more than one duplicate for a given street).
    print data[data["street"].duplicated()]["street"].unique()


def audit_district_quarter_crossref(file):
    '''
    uses expected_district_quartes dictionary to check validity of district-quarter combinations
    
    file: either "street_names_zipcodes_zurich" or "street_names_zipcodes_zurich_update"
    '''
    with open(file, "r") as file_in:
        reader = csv.DictReader(file_in)
        header = reader.fieldnames
        for line in reader:
            if line["quarter"] not in expected_district_quartes[line["district"]]:
                print "wrong quarter: {0}-{1}".format(line["quarter"], line["district"])

def audit_quarter_postcode_crossref(file):
    '''
    uses expected_quarters_postcodes to check validity of quarter-postcode combinations
    
    file: either "street_names_zipcodes_zurich" or "street_names_zipcodes_zurich_update"
    '''
    with open(file, "r") as file_in:
        reader = csv.DictReader(file_in)
        header = reader.fieldnames
        for line in reader:
            if int(line["zipcode"]) != expected_quarters_postcodes[line["quarter"]]:
                print "wrong postcode: {0}-{1}".format(line["quarter"], line["zipcode"])

def audit(file,arg):
    '''
    executes one of the three functions for auditing the reference dataset
    
    file: either "street_names_zipcodes_zurich" or "street_names_zipcodes_zurich_update"
    arg (str): ref, crossref_1 or crossref_2 to execute audit_reference_data(), audit_district_quarter_crossref() or
               audit_quarter_postcode_crossref()
    '''
    if arg == "ref":
        audit_reference_data(file)
    elif arg == "crossref_1":
        audit_district_quarter_crossref(file)
    elif arg == "crossref_2":
        audit_quarter_postcode_crossref(file)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'auditing reference file')
    parser.add_argument('file', help='provide osm file (street_names_zipcodes_zurich_update)')
    parser.add_argument('arg', help='provide argument (ref, crossref_1, crossref_2)')
    args = parser.parse_args()
    
    audit(args.file, args.arg)



