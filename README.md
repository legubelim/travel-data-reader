# Travel data reader

Travel data are collected each time an end-user issues a search on a travel web site. A search is basically made of an origin, destination, departure, return date and numbers and types of the passengers. For each search a set of travel recommendations is returned. Each travel recommendation provides a solution to make the trip. It is made of a list of flights together with a price.
Our raw data are travel recommendations returned to real user searches.

This Python script aims at
* decoding CSV travel recommendations
* grouping them: all recommendations returned by the same search have the same Search ID
* decorating them with additional fields, especially regarding geography (countries, distance) and currency (conversion to Euros)
* encode them in json

Installation
-------

The scipts runs with Python3. Required module are available in requirement.txt (to be used with pip install).
A Bash script is available to create a virtualenv and install the dependencies

```bash
./create_env.sh
source .env/bin/activate
```

Tests
-------

To run all tests, run this command:
```bash
source .env/bin/activate
pytest
```

Usage
-----

The scripts loads the rates file, reads and decodes the input file (or standard input) line by line. Each time a new Search ID is met the last set of decoded lines is converted into a Search object and decorated with additional fields, especially regarding geography (countries, distance) and currency (conversion to Euros). Each Search is then encoded and printed on the standard output in json.

```bash
usage: recoReader.py [-h] [-f {json,pretty_json}] [-r RATES_FILE] [input_file]

Travel data reader

positional arguments:
  input_file            Data file to read (gziped csv file)

optional arguments:
  -h, --help            show this help message and exit
  -f {json,pretty_json}, --format {json,pretty_json}
                        Desired output format. Default is json.
  -r RATES_FILE, --rates_file RATES_FILE
                        Data file with currency rates. Default is etc/eurofxref.csv
```

Example:
```bash
source .env/bin/activate
./recoReader.py test/search_example.csv.gz
```

CSV Raw Data
-----

The input file should be in CSV format with '^' as separator. Each line is a travel recommendation. Here are the fields:
* **version_nb:** version number. Always 1.0 for now
* **search_id**: common and unique to all travel recommendations returned by the same search query. E.g. Q13-28139-1637149716-312856
* **search_country**: country of the end user that issued the search. 2-letter code. E.g. US
* **search_date**: date of the search (UTC). E.g. 2021-11-17
* **search_time**: time of the search (UTC). E.g. 12:56:33
* **origin_city**: search request origin city. 3-letter code. E.g. PAR
* **destination_city**: search request destination city. 3-letter code. E.g. LIS
* **request_dep_date**: search request departure date. E.g. 2022-05-12
* **request_return_date**: search request return date, for round trips (blank for a One Way trip). E.g. 2022-05-19
* **passengers_string**: travellers for the trip. E.g. ADT=1,CH=2 (1 adult and 2 children)
* **currency**: Search request currency. 3-letter code. E.g. USD
* **price**: total price of the recommendation (in previous currency). E.g. 432.14
* **taxes**: taxes, included in the price (in previous currency). E.g. 56.12
* **fees**: Travel agent margin, included in the price. Often 0.0 as the travel agent has other means to make money
* **nb_of_flights**: number of flights for the trip (include both outbound and inbound in case of round trip). E.g. 4

The next fields are repeated for each flight:
* **dep_airport**: departure airport. E.g. CDG
* **dep_date**: departure date (local to departure airport). E.g. 2022-05-12
* **dep_time**: departure time (local to departure airport). E.g. 08:32
* **arr_airport**: arrival airport. E.g. AMS (airport and city codes can be identical)
* **arr_date**: arrival date (local to arrival airport). E.g. 2022-05-12
* **arr_time**: arrival time (local to arrival airport). E.g. 09:10
* **operating_airline**: airline that operates the flight. 2-letter code. E.g. AF
* **marketing_airline**: airline that markets the flight (airlines can sell flights of other airlines if they have agreements). 2-letter code. E.g. AF
* **flight_nb**: flight number that identifies the flight for the marketing airline. E.g. 123 (for the flight AF123)
* **cabin**: M for Eco cabin, B for Business, F for First...

Note: down to currency (included), the fields are the same for all recommendations belonging to the same Search (I.e. with same search_id)

There is a sample with recommendations from 2 searches in test/search_example.csv


Decoration
-------
The decoration adds fields.

At **search** level:
* **advance_purchase**: number of days between search date and departure date. I.e. how long in advance the search was done. E.g. 176
* **stay_duration**: number of days spent at destination. E.g. 7 (-1 for One Way trips)
* **trip_type**: OW for One Way, RT for Round Trip
* **passengers**: arrays of passenger type and passenger number. E.g. [{"passenger_type":"ADT","passenger_nb":1},{"passenger_type":"CH","passenger_nb":2}]
* **origin_country**: country of the orign city. 2-letter code. E.g. FR
* **destination_country**: country of the destination city. 2-letter code. E.g. PT
* **geo**: whether origin and destination are in the same country. D=Domestic I=International
* **OnD**: pair origin/destination cities. E.g. PAR-LIS
* **OnD_distance**: distance between origin and destination cities in km. E.g. 1447

At **recommendation** level:
* **price_EUR**: total price of the recommendation in Euros. E.g. 386.07
* **taxes_EUR**: taxes, included in the price in Euros. E.g. 50.14
* **fees_EUR**: Travel agent margin, included in the price. E.g. 0.0
* **flown_distance**: sum of the distances between departure and arrival airports of all flights in km. E.g. 3714
* **main_marketing_airline**: marketing airline that covers the longuest part of the trip. E.g. AF
* **main_operating_airline**: operating airline that covers the longuest part of the trip. E.g. AF

At **flight** level:
* **dep_city**: departure city. 3-letter code. E.g. PAR
* **arr_city**: arrival city. 3-letter code. E.g. AMS
* **distance**: distance between departure and destination airports in km. E.g. 398

The json generated based on test/search_example.csv is to be found in search_example1.json and search_example2.json

