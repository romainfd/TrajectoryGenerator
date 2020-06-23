# RUN WITH DEBUGGER
# to inspect API answers

import matplotlib.pyplot as plt
import json

with open('data/places.json', 'r') as places:
    places = json.load(places)
    # places = list(filter(lambda place: place['geometry']['type'] == 'Point', places))
    # places = list(map(lambda place: place['name'], places))
with open('data/path.json', 'r') as path:
    path = json.load(path)
with open('data/paths_4_floor.json') as json_file:
    paths4 = json.load(json_file)

# distances
data = [path4['distance'] for path4 in paths4]

# waypoints -> tous 0
# data = [len(path4['waypoints']) for path4 in paths4]

# vitesse moyenne -> 1.3m/s
# data = [(1. * path4['distance']) / path4['traveltime'] for path4 in paths4]

# duree
# data = [path4['traveltime'] for path4 in paths4]

# nombre de routes -> tous 1 (car même étage)
# data = [len(path4['route']) for path4 in paths4]

# nombre de subdirections -> tous 1 aussi
# data = [len(path4['subdirections']) for path4 in paths4]

plt.hist(data)
plt.show()

print("Data loaded...")
