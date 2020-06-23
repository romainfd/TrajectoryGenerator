from numpy.linalg import norm
from numpy import array, random, genfromtxt, cos
from datetime import datetime
import os
import shutil

from p3a_mapwize_pathgenerator.helper import Helper, GeolifeFormatHelper
from p3a_mapwize_pathgenerator.display import collect_local_data
from p3a_mapwize_pathgenerator.config import TRACES_PATH


class Collector:
    @staticmethod
    def max_speed(max_speed, alpha_noise, period):
        """
        Gets max_speed based on experiment parameters. Adds 1e5 as a safety net against rounding errors failing the
        assert in :func:`check_speed <integrations.mapwise.Collector.check_speed>`
        :param max_speed:
        :param alpha_noise:
        :param period:
        :return: the max speed in the experiment (invariant is no step will have a bigger speed)
        :rtype: float
        """
        return max_speed + (alpha_noise / period) + 1e-5

    @staticmethod
    def follow_direction(start, end, initial_noise, initial_speed,
                         alpha_noise=0.25, alpha_speed=0.1, min_speed=0.3, max_speed=2,
                         delta_dt=0, period=1):
        """
        Generates the list of positions between 2 points: start and end.
        Also returns the useful information to keep following directions.

        :param start: The start point of the direction coordinates (lon, lat)
        :type start: numpy ndarray
        :param end: The end point of the direction coordinates (lon, lat)
        :type start: numpy ndarray
        :param initial_noise: (lon, lat) initial noise
        :param float initial_speed: m/s initial speed
        :param float max_speed: The maximum allowed speed in m/s
        :param float min_speed: The minimum allowed speed in m/s
        :param float alpha_speed: The speed noise range for each step in m/s
        :param float alpha_noise: The position noise range for each step in m (used for both lon and lat)
        :type start: numpy ndarray
        :param float delta_dt: the remaining movement time to do based on speed, period and past movement in second
        :param float period: The sampling period in seconds
        :return: The list of positions, the 2D noise, the current speed, the remaining time
        :rtype: :obj:`tuple` of (numpy 2d-array of :obj:`float`, np array of :obj:`float`, :obj:`float`, :obj:`float`)
        """
        # The meter -> degree conversion is constant on the latitude axis but the longitude axis got squeezed as we
        # go closer to the poles. The decrease is ~ linear based on the dist projected on the equator - center line.
        # This distance is the cos of the latitude.
        # TODO: this distance reduction should only affect the longitude distances. Update the code to separate lon/lat
        # distances and speeds to only use this factor on the longitude related ones.
        # Now, because we want to underestimate the meter -> degree conversion otherwise the stats filtering
        # (using exact distance based on the degrees) will filter out some traces, we don't / cos(start[1])
        alpha_noise_in_degrees = alpha_noise * GeolifeFormatHelper.EQUATOR_METERS_TO_DEGREES
        alpha_speed_in_degrees = alpha_speed * GeolifeFormatHelper.EQUATOR_METERS_TO_DEGREES

        min_speed_in_degrees = GeolifeFormatHelper.convert_speed_to_degrees(start, end, min_speed)
        max_speed_in_degrees = GeolifeFormatHelper.convert_speed_to_degrees(start, end, max_speed)

        # all movements are in lat/lon because trace files are written like this
        direction = end - start
        total_degrees_dist = norm(direction)  # distance to do on this path in degrees

        # initialisation
        noise = initial_noise.astype(float)
        speed_in_degrees = Helper.borne(
            GeolifeFormatHelper.convert_speed_to_degrees(start, end, float(initial_speed)),
            min_speed_in_degrees,
            max_speed_in_degrees
        )
        lambda_dir = (speed_in_degrees * delta_dt) / total_degrees_dist
        pos = []

        while lambda_dir <= 1:
            next_pos = start + lambda_dir * direction + noise
            Collector.check_speed(pos, start + noise, next_pos, period,
                                  Collector.max_speed(max_speed, alpha_noise, period))
            pos.append(next_pos)
            # Case 1: there is still some move on this direction to do compute all the deltas
            d_lat = Helper.unif(-1, 1)  # When using unif(-1, 1), we usually see a dispersion to up to 3 times the noise
            # To remain below the speed limit, we need to subtract d_lat ** 2
            # Besides, 1 lon meter is worth more degrees as we go towards the poles
            d_lon = Helper.unif(-1 + d_lat ** 2, 1 - d_lat ** 2) / cos(start[1])
            d_speed = Helper.unif(-1, 1)

            # iterate noise and speed_in_degrees
            noise += alpha_noise_in_degrees * array([d_lat, d_lon])
            speed_in_degrees = Helper.borne(
                speed_in_degrees + alpha_speed_in_degrees * d_speed,
                min_speed_in_degrees,
                max_speed_in_degrees
            )
            lambda_dir += (speed_in_degrees * period) / total_degrees_dist

        # Case 2: we have done all the movement based on 'start' to 'end' -> finished
        # 1. Just move based on what was left to 1 -> directly to the end
        # pos.append(end + noise)  # NO -> only a point every second !
        remaining_lambda = lambda_dir - 1
        remaining_dt = remaining_lambda * total_degrees_dist / speed_in_degrees

        # 2. Pass the remaining movement to the next call
        # return with the positions and the useful information to continue following directions
        return array(pos), noise, GeolifeFormatHelper.convert_speed_from_degrees(start, end,
                                                                                 speed_in_degrees), remaining_dt

    @staticmethod
    def check_speed(pos, start, next_pos, period, max_speed):
        """
        Asserts the speed is consistent with the expactations (the max_speed filter which is going to be used in stats)
        """
        if len(pos) == 0:
            # Not true but a proxy to avoid having to send the previous pos to follow_direction
            previous = start
        else:
            previous = pos[-1]
        # line approx to be faster because 2 consecutive points should be close
        speed = GeolifeFormatHelper.get_dist_line(previous, next_pos) / period
        assert speed < max_speed, f"Step speed {speed} exceeded expected max_speed {max_speed}"

    @staticmethod
    def follow_path(path, noise=array([0, 0]), speed=1.3, delta_dt=0,
                    alpha_noise=0.25, alpha_speed=0.1, min_speed=0.3, max_speed=2, period=1):
        """
        Iterates on the directions of a path.

        :param noise: Initial noise
        :param float speed: Initial speed
        :param float delta_dt: Remaining delta time
        :param path: List of coords (lat, lon) of the path
        :type path: :obj:`list` of :obj:`list` of :obj:`float`
        :param float max_speed: The maximum allowed speed in m/s
        :param float min_speed: The minimum allowed speed in m/s
        :param float alpha_speed: The speed noise range for each step in m/s
        :param float alpha_noise: The position noise range for each step in m (used for both lon and lat)
        :param float period: The sampling period in seconds
        :return: The complete list of positions (lat, lon) from path[0] to path[-1]
        :rtype: :obj:`list` of :obj:`list` of :obj:`float`
        """
        pos = []
        for i in range(len(path) - 1):
            start, end = array(path[i]), array(path[i + 1])
            new_pos, noise, speed, delta_dt = Collector.follow_direction(
                start,
                end,
                noise,
                speed,
                alpha_noise=alpha_noise,
                alpha_speed=alpha_speed,
                min_speed=min_speed,
                max_speed=max_speed,
                delta_dt=delta_dt,
                period=period
            )
            pos.extend(new_pos)
        return pos, noise, speed, delta_dt

    @staticmethod
    def get_stats_file(experiment):
        return f"{experiment}_stats.txt"

    @staticmethod
    def generate_experiment(sampling_ratio=0.05, linear_sampling=False, alpha_noise=0.25, alpha_speed=0.1,
                            min_speed=0.3, max_speed=2, extend_up_to=-1):
        """
        ATTENTION: the maximum real speed is (max_speed * period + alpha_noise) / period

        :param boolean linear_sampling: Should sampling_ratio be used to have a linear sampling (more accurate)
            or be used to compute a discrete sampling step (for back compatibility)
        :param int extend_up_to: The number of steps up to which we should combine paths (-1 to do nothing).
            The only guarantee is path lengths will be lower (but can be strictly lower).
        :param float sampling_ratio: Percentage (between 0 and 1) of traces to use
        :param float max_speed: The maximum allowed speed in m/s
        :param float min_speed: The minimum allowed speed in m/s
        :param float alpha_speed: The speed noise range for each step in m/s
        :param float alpha_noise: The position noise range for each step in m (used for both lon and lat)
        """
        args = locals()
        # Create experiment folder
        experiment = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        os.mkdir(TRACES_PATH + experiment)
        os.mkdir(TRACES_PATH + experiment + "/Trajectory")

        # Generate paths
        _, _, paths4, paths4_full = collect_local_data()
        if linear_sampling:
            selected_paths4 = random.choice(paths4, int(sampling_ratio * len(paths4)), replace=False)
        else:
            sampling = int(len(paths4) / (sampling_ratio * len(paths4)))
            selected_paths4 = paths4[::sampling]
        period = 1  # 1 second

        if extend_up_to == -1:
            # simply loop through sampled paths
            for path in selected_paths4:
                # Convert to trace
                pos, _, _, _ = Collector.follow_path(
                    path['route'][0]['path'],
                    alpha_noise=alpha_noise,
                    alpha_speed=alpha_speed,
                    min_speed=min_speed,
                    max_speed=max_speed,
                    period=period
                )
                # Write as file
                source = path['from']['placeId']
                dest = path['to']['placeId']
                Helper.to_plt(pos, period, TRACES_PATH + f"{experiment}/Trajectory/{source}-{dest}.plt")
        else:
            # Loop through construction until we have the expected number of users
            # During construction, loop through paths until we exceed the expected duration
            user_cpt = 0
            # We get a number of expected places to start from (with replacement)
            place_ids = random.choice(list(paths4_full.keys()), len(selected_paths4), replace=True)
            while user_cpt < len(place_ids):
                pos = []
                current_place_id = place_ids[user_cpt]
                # Initiate movement tracking variables
                noise = array([0, 0])
                speed = 1.3
                delta_dt = 0
                while len(pos) < extend_up_to:
                    # Pick a destination at random
                    next_place_id = random.choice(list(paths4_full[current_place_id].keys()))
                    # Convert to trace
                    new_pos, noise, speed, delta_dt = Collector.follow_path(
                        paths4_full[current_place_id][next_place_id]['route'][0]['path'],
                        noise=noise,
                        speed=speed,
                        delta_dt=delta_dt,
                        alpha_noise=alpha_noise,
                        alpha_speed=alpha_speed,
                        min_speed=min_speed,
                        max_speed=max_speed,
                        period=period
                    )
                    if len(pos) > 0 and len(pos) + len(new_pos) > extend_up_to:
                        # if not empty and we exceed the duration -> stop
                        break
                    # else
                    pos.extend(new_pos)  # [:1] would cumulate the pos noises, thanks to them it's fine without it
                    # (but might be below min_speed)
                    current_place_id = next_place_id
                # Write as file
                Helper.to_plt(pos, period, TRACES_PATH + f"{experiment}/Trajectory/{user_cpt}.plt")
                user_cpt += 1

        # save experiment generation data -> Not copied to this project, ask me if needed
        # (no save_to_labbook because it isn't in the primary table anyway so it won't be found by joins)
        # LabBook.publish_generate_experiment(
        #     Collector.get_stats_file(experiment),  # to be able to join with the args table
        #     args
        # )

        return experiment

    @staticmethod
    def clean_experiment(experiment):
        print("Cleaning experiment data", end="\r")
        shutil.rmtree(TRACES_PATH + experiment)
        print("Cleaning experiment data: traces folder removed")

    @staticmethod
    def read_file(filename):
        """
        Reads the data from the given filename and parses all the information.

        :param string filename: The absolute path to the file to collect
        :return: A table with all the data as rows and the given names as column names
        :rtype: numpy ndarray
        """
        return genfromtxt(
            filename,
            delimiter=',',
            dtype="f8,f8,i8,i8,f8,U10,U8",
            names=['lat', 'lon', '0', 'alt', 'timestamp', 'date', 'time'],
            skip_header=6
        )
