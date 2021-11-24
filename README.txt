### Price benchmark data sample ###

The Air Prices data set consists in prices of air travels collected in the first months of 2020.
During those month we collected every day the cheapest price for a set of origin city, destination city, departure date, return date and airline.

## Fields ##

The fields of the data set are the following:

*search_date: day the price was collected. E.g. 2020-01-20
*origin_city: origin city of the trip (3-letter IATA city code). E.g. PAR (i.e. Paris)
*destination_city: destination city of the trip (3-letter IATA city code). E.g. NYC (i.e. New York)
*departure_date: day of the outbound of the trip. E.g. 2020-02-12
*return_date: day of the inbound of the trip. E.g. 2020-02-19. All the trip of the data set are round trips
*airline: airline company proposing the air ticket (2-letter IATA code). E.g. AF (Air France). All airlines of this data set have been modified so as you don't recognize the real airline.
*price: price of air ticket at search date in Euros. The price of a given trip is likely to change over time (it often gets higher when we get closer to the departure date). E.g. 543.21 (Euros)

The following fields are additional features that can deduced from the first fields:

*ond: Origin-Destination. Just the pair origin city / destination city. E.g. PAR-NYC
*origin_country: country of the origin city (2-letter code). E.g. FR
*destination_country: country of the destination city (2-letter code). E.g. US
*ond_distance: distance in km between the origin city and destination city. E.g. 5837 (km)
*departure_week_day: day of the week of the departure date (0=Monday, 6=Sunday). E.g. 2 (Wednesday)
*advance_purchase: number of days between the search date and the departure date. It shows how close to the departure we are. E.g. 22 (days)
*stay_duration: number of days between the departure date and the return date. E.g. 7 (days)



