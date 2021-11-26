#!/usr/bin/env python3

"""
Simple unit test

> pytest

"""

import os

from recoReader import (
    process
)

csv_filename = os.path.join(os.path.dirname(__file__), "test/travel_data_example.csv.gz")
rates_file = os.path.join(os.path.dirname(__file__), "etc/eurofxref.csv")
rate_RUB = 82.8124


def test_process():

    # fake args
    class args:
        pass
    args.encoder = "json"
    args.input_file = csv_filename
    args.rates_file = rates_file

    # run process with fake args
    searches = list(process(args))    
    assert len(searches) == 2

    # look at first search
    search = searches[0]
    assert search["advance_purchase"] == 30
    assert search["stay_duration"] == 2
    assert search["trip_type"] == "RT"
    assert search["origin_country"] == "FR"
    assert search["destination_country"] == "PT"
    assert search["geo"] == "I"
    assert search["OnD"] == "PAR-LIS"
    assert search["OnD_distance"] == 1447
    assert search["passengers"] == [{'passenger_type': 'ADT', 'passenger_nb': 2}]
    assert len(search["recos"]) == 60

    # look at first reco
    reco = search["recos"][0]
    assert len(reco["flights"]) == reco["nb_of_flights"]
   
    assert reco["price_EUR"] == round(reco["price"] / rate_RUB, 2)
    assert reco["taxes_EUR"] == round(reco["taxes"] / rate_RUB, 2)
    assert reco["fees_EUR"] == round(reco["fees"] / rate_RUB, 2)
    assert reco["flown_distance"] == 3714
    assert reco["main_marketing_airline"] == "KL"
    assert reco["main_operating_airline"] == "KL"
    assert reco["main_cabin"] == "M"

    # look at first flight
    flight = reco["flights"][0]
    assert flight["dep_city"] == "PAR"
    assert flight["arr_city"] == "AMS"
    assert flight["distance"] == 398
    
    
    
