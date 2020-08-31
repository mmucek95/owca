from dataclasses import dataclass
from typing import List, Dict

from workload_runner import ExperimentType


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


DRAM_REDIS_MEMTIER = 'hmem-exp-all-dram-redis-memtier-big-wss'
SCENARIOS = [Scenario(workloads=[DRAM_REDIS_MEMTIER],
                     workloads_count=[{DRAM_REDIS_MEMTIER: 1},
                                      {DRAM_REDIS_MEMTIER: 3},
                                      {DRAM_REDIS_MEMTIER: 5}],
                     sleep_duration=900, scenario_type=ExperimentType.DRAM)]
