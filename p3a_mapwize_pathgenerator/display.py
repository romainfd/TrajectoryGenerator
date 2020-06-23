import json
import matplotlib.pyplot as plt
import numpy as np

from p3a_mapwize_pathgenerator.helper import GeolifeFormatHelper
from p3a_mapwize_pathgenerator.config import DATA_PATH


def collect_local_data():
    with open(f'{DATA_PATH}places.json', 'r') as places:
        places = json.load(places)
    with open(f'{DATA_PATH}path.json', 'r') as path:
        path = json.load(path)
    with open(f'{DATA_PATH}paths_4_floor.json', 'r') as paths4:
        paths4 = json.load(paths4)
    with open(f'{DATA_PATH}paths_4_floor_full.json', 'r') as paths4_full:
        paths4_full = json.load(paths4_full)
    print("Data loaded...")
    return places, path, paths4, paths4_full


# Collect all floors
def _collect_floors(places):
    """
    Collect all the floors

    :param places: The API answer for v1/places
    :rtype: a :obj:`dict` of :obj:`ìnt`
    :return:  The set of all the floors
    """
    floors = set()
    for place in places:
        floors.add(place["floor"])
    return floors


def display_together(places, floors_to_display=None, _plot=None, _fig=None):
    """
    Display all the floors on the same plot using different colors for each floor (the higher the redder)

    :param places: v1/places data
    :param floors_to_display: The floors to display (defaults to all the floors from places)
    :type floors_to_display: A :obj:`set` of :obj:`int`
    :param _plot: Optional plot to use
    :param _fig: Optional related figure
    :return: (fig, plot) used
    """
    fig, plot = _fig, _plot
    if _plot is None:  # pragma: no cover
        fig = plt.figure(figsize=(10, 8))
        plot = fig.add_subplot(111)
    # print all data together
    floors = _collect_floors(places) if floors_to_display is None else floors_to_display
    REFERENCE = (places[0]['longitudeMin'], places[0]['latitudeMin'])
    for place in places:
        floor = float(place['floor'])
        if floor not in floors:
            continue
        color = plt.cm.rainbow(floor / (len(floors) - 1))
        geom_type = place["geometry"]["type"]
        if geom_type == 'Polygon':
            coords = np.array([
                list(GeolifeFormatHelper.get_coords(latlon[0], latlon[1], REFERENCE))
                for latlon in place['geometry']['coordinates'][0]
            ])
            plot.plot(coords[:, 0], coords[:, 1], color=color)
        elif geom_type == 'Point':
            latlon = place['geometry']['coordinates']
            coords = GeolifeFormatHelper.get_coords(latlon[0], latlon[1], REFERENCE)
            plot.plot(coords[0], coords[1], 'o', color=color)
        else:
            print(place["geometry"]["type"], place)
    # Show image
    if _plot is None:  # pragma: no cover
        plot.set_title("Display of the places")
        plot.set_xlabel("x position (meters)")
        plot.set_ylabel("y position (meters)")
        # Same x and y axis scales
        fig.gca().set_aspect('equal', adjustable='box')
        fig.show()
    return fig, plot


def display_floors(places, floors_to_display=None):
    """
    Display all the floors on one plot for each

    :param places: v1/places data
    :param floors_to_display: The floors to display (defaults to all the floors from places)
    :type floors_to_display: A :obj:`set` of :obj:`int`
    :return: (fig, plot) used
    """
    floors = _collect_floors(places) if floors_to_display is None else floors_to_display
    # Build subplots for each floors
    fig = plt.figure(figsize=(10, 8))
    n_rows = 1 if len(floors) == 1 else 2
    n_cols = 1 if len(floors) == 1 else (len(floors) + 1) // n_rows
    floors_plots = dict()
    for i, floor in enumerate(list(floors)):
        if floor not in floors:
            continue
        plot = fig.add_subplot(n_cols, n_rows, i + 1)
        plot.axis('equal')
        plot.set_title(f"Floor {floor}")
        floors_plots[floor] = plot

    # Populate the floors
    for place in places:
        floor = place['floor']
        if floor not in floors:
            continue
        geom_type = place["geometry"]["type"]
        if geom_type == 'Polygon':
            coords = np.array(place['geometry']['coordinates'][0])
            p = floors_plots[floor].plot(coords[:, 0], coords[:, 1])
            color = p[0].get_color()
            floors_plots[floor].plot(place['marker']['longitude'], place['marker']['latitude'], 'x', color=color)
        elif geom_type == 'Point':
            coords = place['geometry']['coordinates']
            floors_plots[floor].plot(coords[0], coords[1], 'o')
        else:
            print(place["geometry"]["type"], place)
    return fig, floors_plots


def display_path(path, _floors_plots=None, _fig=None, places=None):
    """
    Display a path

    :param path: The path to display in v1/directions format
    :param _floors_plots: the dict of floor -> plot. If provided, should contain all the floors used in the path
    :param _fig: The fig linked to _floors_plots
    :param places: v1/places data. Should be provided if _floors_plots are not provided.
    """
    fig, floors_plots = _fig, _floors_plots
    if _floors_plots is None:  # pragma: no cover
        assert places is not None, "Invalid arguments: places should be provided when _floors_plots aren't"
        # we will populate a display with the required levels
        # collect the floors
        floors = set()
        for route in path['route']:
            floors.add(route['floor'])
        fig, floors_plots = display_floors(places, floors)
    # Display the path
    for route in path['route']:
        floor = route['floor']
        coords = np.array(route['path'])
        # WARNING: coords are inverted compared to places geometry
        floors_plots[floor].plot(coords[:, 1], coords[:, 0], 'ro-')
    # Show image
    if _floors_plots is None:  # pragma: no cover
        # Same x and y axis scales
        fig.gca().set_aspect('equal', adjustable='box')
        fig.show()
