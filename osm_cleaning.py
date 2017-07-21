# -*- coding: utf-8 -*-

import re
from collections import defaultdict

def city_clean(element):
    element = element.attrib["v"]
    
    '''
    checks for any of the following irregularities for the value of attr:city and returns a corrected value.
    if no correction required the attr:city value will be returned.
    
    1. city name consisting of digits only (e.g 8002)
    2. different spelling styles for the same city name (e.g "Uitikon-Waldegg" and "Uitikon Waldegg")
    3. city name with two-letter extension representing state affiliation (e.g "Buchs (ZH)")
    4. different spelling variations for the city name Zurich (e.g "Zürich", "Zurich", "Zuerich")
    5. abreviations in city name (e.g "Affoltern a.A.")
    '''
    # regular expression to check if city name has state affiliation extension (Buchs (ZH))
    state_re = re.compile(r"\W+\w{2}\W?$")
    match_state = state_re.search(element)
    
    # regular expression to check if city name is invalid variant of Zürich
    # -spelling (zuerich) or extension by district name (Zürich-Oerlikon)-
    zurich_variant_re = re.compile(ur"zürich|zurich|zuerich", re.IGNORECASE)
    match_zurich_variant = zurich_variant_re.search(element)
    
    #-----------------------------------------------
    # discard city name consisting of digits
    try:
        int(element)
        return None
    except ValueError:
        pass

    #-----------------------------------------------
    # correct different spelling styles
    mapping = {u"Aathal - Seegr\xe4ben" : u"Aathal-Seegr\xe4ben",
        "Uitikon Waldegg" : "Uitikon-Waldegg"}
    if element in mapping:
        return mapping[element]
    
    #-----------------------------------------------
    # correct city name with state affiliation extension
    if match_state:
        state_letters = re.compile(r"\w{2}")
        match_state_letters = state_letters.search(match_state.group())
        return re.sub(state_re, " ({})".format(match_state_letters.group()), element)

    #-----------------------------------------------
    # correct zurich variants (spelling or extension by district name)
    elif match_zurich_variant:
        return re.sub(zurich_variant_re, u"Zürich", match_zurich_variant.group())
    
    #-----------------------------------------------
    # correct abreviation in name
    else:
        name = element
        abr = {"abr_one" : [re.compile(r"a\."), "am"],
            "abr_two" : [re.compile(r"A\."), " Albis"],
                "abr_three" : [re.compile(r"b\."), "bei"]}
        for regex in abr:
            abr_re = abr[regex][0]
            if abr_re.search(element):
                return re.sub(abr_re, abr[regex][1], name)

    #-----------------------------------------------
    # return addr:city value if no cleaning necessary
    return element



mapping_street = {"stasse" : "strasse",
                  "strassse" : "strasse",
                  "str" : "strasse",
                  "str." : "strasse",
                  "strsse" : "strasse",
                  "srasse" : "strasse",
                  "rasse" : "strasse"}


def street_clean(element,mapping):
    '''
    corrects street names according to results from auditing
        
    element: XML element from OSM file
    mapping: dictionary with wrong street names/types as keys and corrected version as values (mapping_street)
    '''
    element = element.attrib["v"]
    
    # return None if street name is digit only,
    # if digits are present in name (optionally followed by word character) remove digits from name
    # else don't change name value (if no match with re.sub, street_name will store the original name)
    try:
        int(element)
        return None
    except ValueError:
        print "val"
        street_name = re.sub(r"\d+(\w+)?", "", element).strip()


    for name in mapping:
        # negative look behind to avoid that "rasse" matches "srasse", "strasse" (expected invalid street types)
        # or "terrasse" (expected valid street type, e.g in "Polyterrasse")
        # regex restriction to end of string ($) avoids "str" matching any "str"-containing strings "(e.g, strasse")
        street_re = re.compile(r"(?<!ter)(?<!s)(?<!st){}$".format(name))
        match = street_re.search(street_name)
        if match:
            return re.sub(street_re, mapping[name], street_name).strip()

    return street_name




def postcode_clean(element):
    '''
    ignore no-digit postcodes
    '''
    element = element.attrib["v"]
    if element == "q":
        return None
    return element


def housenumber_clean(element):
    '''
    identifies and corrects the two entries that contain the street name. Otherwise entries are returned if 
    not a letter at the start of the string
    '''
    element = element.attrib["v"]
    
    housenumber_re = re.compile(r"^\D")
    match = housenumber_re.match(element)
    if element == "Im Chies 14":
        return "14"
    elif element == "144 Im Hof":
        return "144"
    elif match:
        return None
    else:
        return element