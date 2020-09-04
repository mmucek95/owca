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
DRAM_REDIS_MEMTIER = 'redis-memtier-big-wss-dram'
PMEM_REDIS_MEMTIER = 'redis-memtier-big-wss-pmem'
DRAM_PMEM_REDIS_MEMTIER = 'redis-memtier-big-wss-dram-pmem'
DRAM_PMEM_COLDSTART_REDIS_MEMTIER = 'redis-memtier-big-wss-coldstart-toptier'
DRAM_PMEM_TOPTIER_REDIS_MEMTIER = 'redis-memtier-big-wss-toptier'

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
    # Mixed toptier redis memier scenario
    Scenario(name='redis-memtier-toptier',
             workloads=[DRAM_PMEM_TOPTIER_REDIS_MEMTIER],
             workloads_count=[{DRAM_PMEM_TOPTIER_REDIS_MEMTIER: x} for x in range(1, 5, 2)],
             sleep_duration=SLEEP_DURATION, scenario_type=ExperimentType.TOPTIER),
    # Mixed coldstart-toptier redis memtier scenario
    Scenario(name='redis-memtier-coldstart-toptier',
             workloads=[DRAM_PMEM_COLDSTART_REDIS_MEMTIER],
             workloads_count=[{DRAM_PMEM_COLDSTART_REDIS_MEMTIER: x} for x in range(1, 5, 2)],
             sleep_duration=SLEEP_DURATION, scenario_type=ExperimentType.TOPTIER)
]

# ----------------- MEMCACHED SCENARIOS --------------------------
DRAM_MEMCACHED_MUTILATE = 'h-dram-memcached-mutilate-big'
PMEM_MEMCACHED_MUTILATE = 'h-pmem-memcached-mutilate-big'
DRAM_PMEM_MEMCACHED_MUTILATE = 'h-mix-memcached-mutilate-big'

MEMCACHED_SCENARIOS = [
    # dram scenario
    Scenario(name='memcached-mutilate-dram',
             workloads=[DRAM_MEMCACHED_MUTILATE],
             workloads_count=[{DRAM_MEMCACHED_MUTILATE: x} for x in range(1, 5, 2)],
             sleep_duration=SLEEP_DURATION, scenario_type=ExperimentType.DRAM),
    # pmem scenario
    Scenario(name='memcached-mutilate-pmem',
             workloads=[PMEM_MEMCACHED_MUTILATE],
             workloads_count=[{PMEM_MEMCACHED_MUTILATE: x} for x in range(1, 5, 2)],
             sleep_duration=SLEEP_DURATION, scenario_type=ExperimentType.PMEM),
    # Mixed scenario
    Scenario(name='memcached-mutilate-hmem-numa-balancing',
             workloads=[DRAM_PMEM_MEMCACHED_MUTILATE],
             workloads_count=[{DRAM_PMEM_MEMCACHED_MUTILATE: x} for x in range(1, 5, 2)],
             sleep_duration=SLEEP_DURATION, scenario_type=ExperimentType.HMEM_NUMA_BALANCING)
]
