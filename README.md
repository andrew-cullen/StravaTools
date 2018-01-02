# StravaTools

Selection of tools to interface with the website "Strava" - which acts as a social network for athletes, and allows for the storing of ride/run/swim data. 

WahooElemntTurnByTurn - fixes a missing feature for Wahoo Elemnt (and Elemnt Bolt) bike computer users for Strava. These two GPS cycle computers can provide turn-by-turn navigation instrcutions, however this feature cannot be used for gps routes created in Strava. This program takes the gps route data, and matches it to cue sheet data provided by Strava, which is stored in encoded polyline format. The code then creates an equivalent turn by turn file. 

ClubScrape - uses the strava api to access recent rides by all the riders in a club, collects the GPS track data from all of those rides, and then uses that data to create a heatmap that is superimposed over a map procured from OSM (Open Street Maps). This allows for analysing the geographic spread, distribution, and behavior of riders from a club on Strava. 
