## Trajectory Generator

This project is part of my last year Research Project at École polytechnique about trajectory reconciliation using heterogeneous sources of data.

This repo contains the files related to the random trajectory generation. To be realistic this generation is using MapWize API to generate walkable paths between several places. To reproduce the noise coing from real persons and sensors, we add a random position noise and a random speed evolution over time.

### Set up
- In a virtual environment, run `poetry install`
- Run `touch p3a_mapwize_pathgenerator/config.py` and fill it with
```
import os
ROOT = os.getcwd() + "/"
API_KEY = "YOUR_MAPWIZE_API_KEY_IF_NEEDED"
DATA_PATH = ROOT + "p3a_mapwize_pathgenerator/data/"
TRACES_PATH = DATA_PATH + "traces/"
```
- To check the project is working fine, run `poetry run pytest tests`. These tests are a bit noisy but will give examples of how the generator works.

### Usage
- The generator uses MapWize API trajectories and random noise to generate realistic trajectories. The `json` files under `p3a_mapwize_pathgenerator` contains responses from MapWize API.
- If you wish to generate such trajectories for another venue, update (set `WRITE = True` and update the `VENUE_ID`) and run `python p3a_mapwize_pathgenerator/api.py`
- To generate the randomized trajectories
    - Run `python `/playground.py`. `generate_experiment` has a few parameters (explained in its docstring) to play with
    - Trajectories will be stored under a directory under `p3a_mapwize_pathgenerator/data/traces` following the [GeoLife trace format](https://www.microsoft.com/en-us/download/details.aspx?id=52367&from=https%3A%2F%2Fresearch.microsoft.com%2Fen-us%2Fdownloads%2Fb16d359d-d164-469e-9fd4-daa38f2b2e13%2F)
    - As shown in `playground.py`, `Collector.read_file` lets you read the stored `.plt` files
    - If needed, I can also share additional code to help manipulate and display these traces
    
### Noise generation
#### Position noise
At each step, we add a random position noise uniformly generated between `[-alpha_noise, alpha_noise]` to the theorical position of the user (based on the exact path given by MapWize API)

#### Speed evolution
At each step, we will change the user speed based on a value uniformly generated between `[-alpha_speed, alpha_speed]` while making sure the final speed is always between `[min_speed, max_speed]`.

#### Implementation details
Implementation details can be found in the `follow_direction` method in `p3a_mapwize_pathgenerator/mapwize.py`
