import unittest
from numpy import array, random, mean
import matplotlib.pyplot as plt

from p3a_mapwize_pathgenerator.helper import Helper, GeolifeFormatHelper
from p3a_mapwize_pathgenerator.display import collect_local_data, display_floors, display_path, display_together
from p3a_mapwize_pathgenerator.config import TRACES_PATH
from p3a_mapwize_pathgenerator.mapwize import Collector


class TestIntegration(unittest.TestCase):
    def test_display(self):
        """ DISPLAY EXAMPLES """
        # Collects local data
        _places, _path, _paths4, _ = collect_local_data()

        # Display all floors together
        display_together(_places)

        # Display all floors separately
        _fig, _ = display_floors(_places, {0, 1, 2, 3, 4, 5})
        _fig.show()

        # Display some floors
        pathFloors = set()
        for _route in _path['route']:
            pathFloors.add(_route['floor'])
        pathFloors.update({3, 4, 5})
        _fig, _floors_plots = display_floors(_places, pathFloors)

        # Display path on floors display
        display_path(_path, _floors_plots, _fig)
        _fig.show()

        # Display a single path
        display_path(_path, places=_places)

        # display all the paths
        _fig2, _floors_plots2 = display_floors(_places, {4})
        for _path4 in _paths4:
            display_path(_path4, _floors_plots2, _fig2)
        _fig2.show()

    def test_generation(self):
        """
        Basic MapWize API integration tests (display floor and path) and experimental path generation and display
        Not asserting anything, just running the logic
        """
        places, path, paths4, _ = collect_local_data()

        fig, floors_plots = display_floors(places, {4})
        display_path(path, floors_plots, fig)
        fig.show()

        random.seed(0)
        pos, _, _, delta_dt = Collector.follow_direction(
            [0, 0],
            array([60, 80]) * GeolifeFormatHelper.EQUATOR_METERS_TO_DEGREES,
            array([0, 0]),
            1.3,
            0
        )
        print(pos)
        print(delta_dt)
        plt.plot(pos[:, 0], pos[:, 1], 'rx-')
        plt.axis('equal')

        pos2, _, _, delta_dt = Collector.follow_direction(
            [0, 0],
            array([60, 80]) * GeolifeFormatHelper.EQUATOR_METERS_TO_DEGREES,
            array([0, 0]),
            1.3,
            0
        )
        print(pos2)
        print(delta_dt)
        plt.plot(pos2[:, 0], pos2[:, 1], 'bx-')
        plt.show()

        # Compute the average difference in positions
        diffs = []
        for i in range(min(len(pos), len(pos2))):
            diffs.append(GeolifeFormatHelper.get_dist_line(pos[i], pos2[i]))
        diffs = array(diffs)
        print(diffs)
        print(mean(diffs))

        print("\n\n FINAL TEST \n")
        print(path['route'][0]['path'])
        pos3 = array(Collector.follow_path(path['route'][0]['path'])[0])
        print(len(pos3))
        groundtruth = array(path['route'][0]['path'])
        plt.plot(groundtruth[:, 0], groundtruth[:, 1], 'bo-')
        plt.plot(pos3[:, 0], pos3[:, 1], 'rx-')
        plt.axis("equal")
        plt.show()

        Helper.to_plt(pos3, 1, TRACES_PATH + "file.plt")
