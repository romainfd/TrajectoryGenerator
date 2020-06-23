from numpy import random
import os

from p3a_mapwize_pathgenerator.mapwize import Collector
from p3a_mapwize_pathgenerator.config import TRACES_PATH


if __name__ == '__main__':
    random.seed(0)
    experiment = Collector.generate_experiment(
        sampling_ratio=50.1/552,
        linear_sampling=True,
        alpha_noise=5,
        alpha_speed=2,
        min_speed=0.3,
        max_speed=2,
        extend_up_to=100
    )
    trajectories_path = TRACES_PATH + f"{experiment}/Trajectory/"
    for trace_file in os.listdir(trajectories_path):
        print(Collector.read_file(TRACES_PATH + f"{experiment}/Trajectory/" + trace_file))
