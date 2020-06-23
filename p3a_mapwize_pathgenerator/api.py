import requests
import json
from p3a_mapwize_pathgenerator.config import API_KEY
from tqdm import tqdm

VENUE_ID = "56b20714c3fa800b00d8f0b5"
WRITE = False

r = requests.get(
    f'https://api.mapwize.io/v1/places?api_key={API_KEY}&venueId={VENUE_ID}&isPublished=true'
)

if r.status_code == 200:
    places = r.json()
    if WRITE:
        with open('data/places.json', 'w+') as outfile:
            json.dump(places, outfile)
        print("Places saved")

    # A sample path
    query = {
      "from": {
        "placeId": places[0]["_id"]
      },
      "to": [{
        "placeId": places[-1]["_id"]
      }]
    }
    r2 = requests.post('https://api.mapwize.io/v1/directions?api_key='+API_KEY, json=query)
    if r2.status_code == 200:
        path = r2.json()
        if WRITE:
            with open('data/path.json', 'w+') as outfile:
                json.dump(path, outfile)
            print("Path saved")

        # Take only 4-floor for paths
        places = list(filter(lambda place: place['floor'] == 4, places))
        # Download all the paths between 4-floor buildings
        places_pairs = []
        for place1 in places:
            for place2 in places:
                if place1["_id"] != place2['_id']:
                    places_pairs.append((place1["_id"], place2['_id']))
        paths_4_floor = []
        paths_4_floor_full = {}
        for place1_id, place2_id in tqdm(places_pairs):
            query = {
                "from": {
                    "placeId": place1_id
                },
                "to": [{
                    "placeId": place2_id
                }]
            }
            r3 = requests.post('https://api.mapwize.io/v1/directions?api_key=' + API_KEY, json=query)
            if r3.status_code == 200:
                path = r3.json()
                paths_4_floor.append(path)
                if place1_id not in paths_4_floor_full:
                    paths_4_floor_full[place1_id] = {place2_id: None}
                paths_4_floor_full[place1_id][place2_id] = path
            else:
                raise Exception(
                    f"Path between {place1_id} to {place2_id} failed to be download. " +
                    r3.status_code + r3.content
                )
        if WRITE:
            with open('data/paths_4_floor.json', 'w+') as outfile:
                json.dump(paths_4_floor, outfile)
            print("Paths for 4th floor saved")
        if WRITE:
            with open('data/paths_4_floor_full.json', 'w+') as outfile:
                json.dump(paths_4_floor_full, outfile)
            print("Paths with source-target for 4th floor saved")
    else:
        raise Exception("Path not downloaded. " + r2.status_code + r2.content)
else:
    raise Exception("Places not downloaded. " + r.status_code + r.content)

with open('data/places.json') as json_file:
    places_loaded = json.load(json_file)
    assert places_loaded == places
    print(f"{len(places_loaded)} places loaded")
with open('data/path.json') as json_file:
    path_loaded = json.load(json_file)
    assert path_loaded == path
    print(f"{path_loaded['traveltime']:.2f} seconds long path")
with open('data/paths_4_floor.json') as json_file:
    paths_loaded = json.load(json_file)
    assert paths_loaded == paths_4_floor
    print(f"{len(paths_loaded)} paths on 4th floor loaded")
with open('data/paths_4_floor_full.json') as json_file:
    paths_full_loaded = json.load(json_file)
    assert paths_full_loaded == paths_4_floor_full
    print(f"{len(paths_full_loaded)} sources on 4th floor loaded")
