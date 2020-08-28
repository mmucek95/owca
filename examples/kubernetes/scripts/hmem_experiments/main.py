from dataclasses import dataclass
from typing import List, Dict

from runner import scale_down_all_workloads
from workload_runner import run_experiment, ExperimentType

WORKLOADS = ['hmem-exp-all-dram-redis-memtier-big-wss']
WORKLOADS_COUNT = {}


@dataclass
class Scenario:
    # List of workload names used in the experiment
    workloads: List[str]
    # List of workload counts in every step of the experiment
    # e.g. [{'workload1': 1}, {'workload1': 3}] means that in first loop
    # workload1 will have one instance and three in the second
    workloads_count: List[Dict[str, int]]
    sleep_duration: int
    scenario_type: ExperimentType


scenario1 = Scenario(workloads=['hmem-exp-all-dram-redis-memtier-big-wss'],
                     workloads_count=[{'hmem-exp-all-dram-redis-memtier-big-wss': 1}],
                     sleep_duration=900, scenario_type=ExperimentType.DRAM)


def run_scenario(scenario: Scenario):
    for workload_counts in scenario.workloads_count:
        run_experiment(scenario.workloads, workload_counts,
                       scenario.sleep_duration, scenario.scenario_type)
    scale_down_all_workloads(wait_time=10)


def main():
    run_scenario(scenario1)


if __name__ == '__main__':
    main()
