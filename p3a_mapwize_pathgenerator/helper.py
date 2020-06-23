import numpy as np
from numpy import random
from datetime import datetime, timedelta
from geopy import distance as geopydist
from math import pi, cos, sqrt


class Helper:
    @staticmethod
    def unif(a, b):
        """
        :return: A random value uniformly in [a, b]
        :rtype: float
        """
        return a + (b - a) * random.rand()

    @staticmethod
    def borne(value, _min, _max):
        """
        :param float value: Value to truncate if necessary
        :param float _min: Lower bound
        :param float _max: Upper bound
        :return: Truncated value if outside of [_min, _max]
        """
        if value < _min:
            return _min
        elif value > _max:
            return _max
        else:
            return value

    @staticmethod
    def to_plt(pos, period, filename):
        """
        Format a list of positions to the .plt format. Here is the description from the Microsoft GeoLife project.

        "Line 1...6 are useless in this dataset, and can be ignored.
        Points are described in following lines, one for each line.
        Field 1: Latitude in decimal degrees.
        Field 2: Longitude in decimal degrees.
        Field 3: All set to 0 for this dataset.
        Field 4: Altitude in feet (-777 if not valid).
        Field 5: Date - number of days (with fractional part) that have passed since 12/30/1899.
        Field 6: Date as a string.
        Field 7: Time as a string."

        :param pos: List of positions (lat, lon) to write as .plt file
        :param float period: The sampling period in seconds
        :param str filename: Path to the file
        :return:
        """
        START_DATE = datetime(1899, 12, 30)
        DAY_IN_SECONDS = 24 * 60 * 60.
        LINE_END = "\n"
        # to all start at a different moment
        # -> have a different seed in builder.build_path() even if same lat/lon
        dt = random.randint(0, 1000000)
        with open(filename, "w+") as file:
            for i in range(1, 7):
                file.write(f"Offset line {i}{LINE_END}")
            for lat, lon in pos:
                alt = 0
                date_fraction = dt / DAY_IN_SECONDS
                d = START_DATE + timedelta(seconds=dt)
                data = [lat, lon, 0, alt, date_fraction, d.date(), d.time()]
                data_str = ",".join(list(map(str, data))) + LINE_END
                file.write(data_str)
                dt += period


class GeolifeFormatHelper:
    """
        A class to gather helper and utility functions used to build clean data from Geolife formatted data
    """
    # 1° lon / lat ~110km on the equator
    # We should underestimate the meter -> degree conversion otherwise the stats filtering
    # (using exact distance based on the degrees) will filter out some traces -> CONVERSION_SAFETY_NET
    # -> 1 / 110e3 * 0.95
    EQUATOR_METERS_TO_DEGREES = 8.6e-6

    # coords = (lat, lon) = (y, x)
    PARIS = (48.864716, 2.349014)
    MASSY = (48.7264243781, 2.2775803429)
    LONDON = (51.509865, -0.118092)
    BEIJING = (39.913818, 116.363625)
    REFERENCE = BEIJING  # most of the data was recorded in Beijing

    @staticmethod
    def get_time_s(timestamp):
        """
        Convert a geolife timestamp to a timestamp in seconds since 12/30/1899.

        :param float timestamp: The geolife data timestamp as a fraction of day (since 12/30/1899 without offset).
        :return: The equivalent in seconds
        :rtype: int
        """
        return int(round(timestamp * 24 * 3600))

    @staticmethod
    def get_coords(lat, lon, ref):
        """
        Compute the exact distance of (lat, lon) to ref (in lat, lon).
        For a faster method, see get_dist_line that uses a linear approximation of a sphere.

        :param float lat: The point latitude.
        :param float lon: The point longitude.
        :param ref: A tuple (lat, lon) used as (0, 0).
        :type ref: (float, float)
        :return: The coordinates (x, y) in meters.
        :rtype: (float, float)
        """
        y = geopydist.distance((lat, ref[1]), ref).m  # same lon => D_lat
        if lat < ref[0]:
            y = -y
        x = geopydist.distance((ref[0], lon), ref).m  # same lat => D_lon
        if lon < ref[1]:
            x = -x
        return y, x

    @staticmethod
    def to_radians(angle):
        """
        Converts degrees to radians

        :param float angle: The angle in degrees
        :return: The angle in radians
        :rtype: float
        """
        return angle / 180. * pi

    @staticmethod
    def get_dist_line(coords1, coords2):
        """
        ERROR: < 1% for points up to 300km.
        Uses the linear approximation of a sphere to compute the distance (the 2 points shouldn't be far).
        Based on Pythagoras' theorem on the equirectangular projection.
        More information on https://www.movable-type.co.uk/scripts/latlong.html

        :param coords1: Source coordinates.
        :type coords1: (float, float)
        :param coords2: Destination coordinates.
        :type coords2: (float, float)
        :return: The approximate distance between coords1 and coords2 in meters.
        :rtype: float
        """
        lat1, lon1 = coords1
        lat2, lon2 = coords2
        middle_lat = GeolifeFormatHelper.to_radians(lat1 + lat2) / 2  # We center the projection
        x = GeolifeFormatHelper.to_radians(lon2 - lon1) * cos(middle_lat)
        y = GeolifeFormatHelper.to_radians(lat2 - lat1)
        d = sqrt(x * x + y * y) * 6.3781e6
        return d

    @staticmethod
    def convert_speed_to_degrees(start, end, speed_in_ms):
        """
        :param start: The start point of the direction coordinates (lon, lat)
        :type start: numpy ndarray
        :param end: The end point of the direction coordinates (lon, lat)
        :type start: numpy ndarray
        :param float speed_in_ms: The speed in m/s to convert to internal value in lon/lat
        :return: The converted speed in lon/lat
        :rtype: float
        """
        dist_in_degrees = np.linalg.norm(end - start)
        dist_in_meters = GeolifeFormatHelper.get_dist_line(start, end)
        # Same duration in both points of view (m/s or degrees/s) -> same d / v
        return (dist_in_degrees / dist_in_meters) * speed_in_ms

    @staticmethod
    def convert_speed_from_degrees(start, end, speed_in_degrees):
        """
        :param start: The start point of the direction coordinates (lon, lat)
        :type start: numpy ndarray
        :param end: The end point of the direction coordinates (lon, lat)
        :type start: numpy ndarray
        :param float speed_in_degrees: The speed in degrees/s to convert to internal value in m/s
        :return: The converted speed in m/s
        :rtype: float
        """
        dist_in_degrees = np.linalg.norm(end - start)
        dist_in_meters = GeolifeFormatHelper.get_dist_line(start, end)
        # Same duration in both points of view (m/s or degrees/s) -> same d / v
        return (dist_in_meters / dist_in_degrees) * speed_in_degrees

