#!/usr/bin/env python3

"""
Tool to decode, group and decorate and display Travel recommendations.

> python3 recoReader.py -h

"""

import logging
import argparse
import sys
import gzip
import json
import datetime
import neobase
import os
from collections import Counter



_RECO_LAYOUT = ["version_nb", "search_id", "search_country",
                "search_date", "search_time", "origin_city", "destination_city", "request_dep_date", 
	        "request_return_date", "passengers_string", 
	        "currency", "price", "taxes", "fees", "nb_of_flights"]

_FLIGHT_LAYOUT = ["dep_airport", "dep_date", "dep_time",
                  "arr_airport", "arr_date", "arr_time",
                  "operating_airline", "marketing_airline", "flight_nb", 
	          "cabin"]


# Log init
logging.basicConfig(format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


### geography module ###
neob = None 
def get_neob():
    """ Init geography module if necessary"""
    global neob
    # geography module init
    if neob is None:
        logger.info("Init geography module neobase")
        neob = neobase.NeoBase()
    return neob


### Currency rates ###
def load_rates(rates_file):
    """
    Decodes currency rate file as provided by the BCE from https://www.ecb.europa.eu/stats/eurofxref/eurofxref.zip

    """
    
    header = None
    rates = []
    with open(rates_file, 'r') as f:
        for line in f:
            array = line.rstrip().split(',')
            if len(array)<=1: return None # skip empty line
            array = [x.lstrip() for x in array if x != ""] # removing heading white spaces
            if header == None:
                # first line is the header: Date, USD, JPY, BGN, CZK, DKK, ...
                header = array
            else:
                # next lines are date and rates: 19 November 2021, 1.1271, 128.22, 1.9558, 25.413, 7.4366, ...
                # convert date into reasonable format
                rate_date = datetime.datetime.strptime(array[0], "%d %B %Y").strftime("%Y-%m-%d")
                # convert next fields to float
                array = [rate_date] + list(map(float, array[1:]))
                # zip with header
                rates.append(dict(zip(header, array)))

    # only returns the last date for this simple version
    rates = rates[-1]
    logger.info("Currency rates loaded: %s" % rates)
    return rates


### CSV decoding ###
def decode_line(line):
    """
    Decodes a CSV line based on _RECO_LAYOUT and _FLIGHT_LAYOUT

    """
    
    try:
        # converting to text string
        if isinstance(line, bytes):
            line = line.decode()

        # splitting the CSV line
        array=line.rstrip().split('^')
        if len(array)<=1:
            logger.warning("Empty line")
            return None # skip empty line
    
        # decoding fields prior to flight details
        reco = dict(zip(_RECO_LAYOUT, array))
        read_columns_nb=len(_RECO_LAYOUT)

        # convert to integer
        reco["nb_of_flights"] = int(reco["nb_of_flights"])

        # decoding flights details
        reco["flights"]=[]
        for i in range(0, reco["nb_of_flights"]):
            flight=dict(zip(_FLIGHT_LAYOUT, array[read_columns_nb:]))
            read_columns_nb+=len(_FLIGHT_LAYOUT)
            reco["flights"].append(flight)

    except:
        logger.exception("Failed at decoding CSV line: %s" % line.rstrip())
        return None
        
    return reco
    

### Reco processing ###

_SEARCH_FIELDS = ["version_nb", "search_id", "search_country",
                  "search_date", "search_time", "origin_city", "destination_city", "request_dep_date", 
	          "request_return_date", "passengers_string", 
	          "currency"]

def group_and_decorate(recos_in, rates):
    """
    Groups recos to build a search object. Adds interesting fields.

    """
    
    # don't decorate empty search or empty recos
    if recos_in == None or len(recos_in) == 0: return None
    recos = [reco for reco in recos_in if reco != None]
    
    def to_euros(amount):
        if search["currency"] == "EUR": return amount
        else: return round(amount / rates[search["currency"]], 2)

    try:
        # some fields are common to the search, others are specific to recos
        # taking search fields from the first reco
        search = {key: value for key, value in recos[0].items() if key in _SEARCH_FIELDS}
        # keeping other fields only in reco
        search["recos"] = [{key: value for key, value in reco.items() if key not in _SEARCH_FIELDS} for reco in recos]

        # advance purchase & stay duration & OW/RT
        search_date = datetime.datetime.strptime(search["search_date"],'%Y-%m-%d')
        request_dep_date = datetime.datetime.strptime(search["request_dep_date"],'%Y-%m-%d')
        # approximative since the dep date is local to the origin city (whereas the search date is UTC)
        search["advance_purchase"] = (request_dep_date - search_date).days
        if search["request_return_date"] == "":
            search["stay_duration"] = -1
            search["trip_type"] = "OW" # One Way trip
        else:
            request_return_date = datetime.datetime.strptime(search["request_return_date"],'%Y-%m-%d')
            # approximative since the return date is local to the destination city
            search["stay_duration"] = (request_return_date - request_dep_date).days
            search["trip_type"] = "RT" # Round trip

        # decoding passengers string: "ADT=1,CH=2" means 1 Adult and 2 children
        passengers = []
        for pax_string in search['passengers_string'].rstrip().split(','):
            pax_array = pax_string.split("=")
            passengers.append({"passenger__type" : pax_array[0], "passenger_nb" : int(pax_array[1])})
        search['passengers'] = passengers
        
        # countries
        search["origin_country"] = get_neob().get(search["origin_city"], 'country_code')
        search["destination_country"] = get_neob().get(search["destination_city"], 'country_code')
        # geo: D=Domestic I=International
        search["geo"] = "D" if search["origin_country"] == search["destination_country"] else "I" 

        # OnD (means Origin and Destination. E.g. "PAR-NYC")
        search["OnD"] = f"{search['origin_city']}-{search['destination_city']}"
        search["OnD_distance"] = round(get_neob().distance(search["origin_city"], search["destination_city"]))

        # reco decoration
        for reco in search["recos"]:
            
            # currency conversion
            for amount in ["price", "taxes", "fees"]:
                reco[amount] = float(reco[amount])
                reco[amount + "_EUR"] = to_euros(reco[amount])

            # will be computed from flights
            marketing_airlines = {}
            operating_airlines = {}
            reco['flown_distance'] = 0

            # flight decoration
            for f in reco["flights"]:
                # getting cities (a city can have several airports like PAR has CDG and ORY)
                f["dep_city"] = get_neob().get(f["dep_airport"], 'city_code_list')[0]
                f["arr_city"] = get_neob().get(f["arr_airport"], 'city_code_list')[0]
                
                f["distance"] = round(get_neob().distance(f["dep_airport"], f["arr_airport"]))
                reco['flown_distance'] += f["distance"]
                marketing_airlines[f["marketing_airline"]] = marketing_airlines.get(f["marketing_airline"], 0) + f["distance"]
                if f["operating_airline"] == "": f["operating_airline"] = f["marketing_airline"]
                operating_airlines[f["operating_airline"]] = operating_airlines.get(f["operating_airline"], 0) + f["distance"]

            # the main airline is the one that covers the longuest part of the trip
            reco["main_marketing_airline"] = max(marketing_airlines, key=marketing_airlines.get)
            reco["main_operating_airline"] = max(operating_airlines, key=operating_airlines.get)


    except:
        logger.exception("Failed at grouping and decorating recos: %s" % recos_in)
        # filter out recos when we fail at decorating them
        return None
        
    return search


### Encoders ###
# Different ways to print the output. You can easily add one.

def encoder_json(reco):

    return json.dumps(reco)


def encoder_pretty_json(reco):

    return json.dumps(reco, indent=2)

# encoders list
encoders = { "json" : encoder_json,
             "pretty_json" : encoder_pretty_json,
}



### Main function ###
def process(args):

    # loading currency rates
    rates = load_rates(args.rates_file)

    logger.info("Decoding/encoding")

    cnt = Counter()
    recos = []
    current_search_id = 0
    # open input file (or stdin if there is none)
    with gzip.open(args.input_file, 'r') if args.input_file is not "-" else sys.stdin as f:
        for line in f:
            #print(line, file=sys.stderr)
            cnt['reco_read'] += 1
            reco=decode_line(line)
            if reco:
                cnt['reco_decoded'] +=1
                # new search_id means new search: we can process the collected recos
                if reco["search_id"] != current_search_id:
                    current_search_id = reco["search_id"]
                    if len(recos) > 0:
                        cnt['search_read'] += 1
                        search = group_and_decorate(recos, rates)
                        if search:
                            cnt['search_encoded'] += 1
                            yield search
                        recos=[]
                recos.append(reco)

    # Let's not forget the last search
    if len(recos) > 0:
        cnt['search_read'] += 1
        search = group_and_decorate(recos, rates)
        if search:
            cnt['search_encoded'] += 1
            yield search
    
    logger.info(f"Finished with %s" % cnt)
 

if __name__ == "__main__":

    # default rates file
    def_rates_file = os.path.join(os.path.dirname(__file__), "etc/eurofxref.csv")
    
    logger.info("Parsing arguments")
    parser = argparse.ArgumentParser(description="Travel data reader")
    parser.add_argument("input_file", help="Data file to read", nargs='?', default="-")
    parser.add_argument("-f", "--format", help="Desired output format. Default is json.", choices=encoders.keys(), default="json")
    parser.add_argument("-r", "--rates_file", help=f"Data file with currency rates. Default is {def_rates_file}", default=def_rates_file)
    args = parser.parse_args()

    encoder = encoders[args.format]

    for search in process(args):
        # encode and print
        print(encoder(search))

