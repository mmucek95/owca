from dataclasses import dataclass
from typing import List, Dict

from workload_runner import ExperimentType


@dataclass
class Scenario:
    name: str
    # List of workload names used in the experiment
    workloads: List[str]
    # List of workload counts in every step of the experiment
    # e.g. [{'workload1': 1}, {'workload1': 3}] means that in first loop
    # workload1 will have one instance and three in the second
    workloads_count: List[Dict[str, int]]
    sleep_duration: int
    scenario_type: ExperimentType


# ----------------- REDIS SCENARIOS --------------------------
DRAM_REDIS_MEMTIER = 'hmem-exp-all-dram-redis-memtier-big-wss'
PMEM_REDIS_MEMTIER = 'hmem-exp-all-pmem-redis-memtier-big-wss'
DRAM_PMEM_REDIS_MEMTIER = 'hmem-exp-mix-redis-memtier-big-wss'
DRAM_PMEM_COLDSTART_REDIS_MEMTIER = 'hmem-exp-coldstart-memtier-big-wss'

SLEEP_DURATION = 900
REDIS_SCENARIOS = [
    # Dram redis memtier scenario
    Scenario(name='redis-memtier-dram',
             workloads=[DRAM_REDIS_MEMTIER],
             workloads_count=[{DRAM_REDIS_MEMTIER: x} for x in range(1, 5, 2)],
             sleep_duration=SLEEP_DURATION, scenario_type=ExperimentType.DRAM),
    # PMEM redis memtier scenario
    Scenario(name='redis-memtier-pmem',
             workloads=[PMEM_REDIS_MEMTIER],
             workloads_count=[{PMEM_REDIS_MEMTIER: x} for x in range(1, 5, 2)],
             sleep_duration=SLEEP_DURATION, scenario_type=ExperimentType.PMEM),
    # Mixed redis memtier scenario with numa balancing
    Scenario(name='redis-memtier-hmem-numa-balancing',
             workloads=[DRAM_PMEM_REDIS_MEMTIER],
             workloads_count=[{DRAM_PMEM_REDIS_MEMTIER: x} for x in range(1, 5, 2)],
             sleep_duration=SLEEP_DURATION, scenario_type=ExperimentType.HMEM_NUMA_BALANCING),
    # Mixed redis memtier scenario without numa balancing
    Scenario(name='redis-memtier-hmem-no-numa-balancing',
             workloads=[DRAM_PMEM_REDIS_MEMTIER],
             workloads_count=[{DRAM_PMEM_REDIS_MEMTIER: x} for x in range(1, 5, 2)],
             sleep_duration=SLEEP_DURATION, scenario_type=ExperimentType.HMEM_NO_NUMA_BALANCING),
    # Mixed coldstart redis memtier scenario
    Scenario(name='redis-memtier-coldstart',
             workloads=[DRAM_PMEM_COLDSTART_REDIS_MEMTIER],
             workloads_count=[{DRAM_PMEM_COLDSTART_REDIS_MEMTIER: x} for x in range(1, 5, 2)],
             sleep_duration=SLEEP_DURATION, scenario_type=ExperimentType.COLD_START)
]
