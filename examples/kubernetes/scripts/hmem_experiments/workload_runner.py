from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from runner import default_shell_run
from hmem_experiments.kernel_parameters import set_numa_balancing, set_toptier_scale_factor

from time import sleep


class MemoryType(Enum):
    DRAM = 'dram'
    PMEM = 'pmem'
    HMEM = 'hmem'


@dataclass
class Experiment:
    workloads: List[str]
    number_of_workloads: Dict[str, int]
    start_timestamp: int = None
    stop_timestamp: int = None


@dataclass
class ExperimentConfiguration:
    memory_type: MemoryType
    numa_balancing: bool
    toptier_scale_factor: int = 2000


class ExperimentType(Enum, ExperimentConfiguration):
    DRAM = ExperimentConfiguration(
        MemoryType.DRAM, numa_balancing=True)
    PMEM = ExperimentConfiguration(
        MemoryType.PMEM, numa_balancing=True)
    HMEM_NUMA_BALANCING = ExperimentConfiguration(
        MemoryType.HMEM, numa_balancing=True)
    HMEM_NO_NUMA_BALANCING = ExperimentConfiguration(
        MemoryType.HMEM, numa_balancing=False)
    COLD_START = HMEM_NUMA_BALANCING
    TOPTIER = ExperimentConfiguration(
        MemoryType.HMEM, numa_balancing=True, toptier_scale_factor=10000)
    TOPTIER_WITH_COLDSTART = TOPTIER


def _scale_workload(workload_name, number_of_workloads=1):
    cmd_scale = "kubectl scale sts {} --replicas={}".format(
        workload_name, number_of_workloads)
    default_shell_run(cmd_scale)


def _set_configuration(configuration: ExperimentConfiguration):
    set_numa_balancing(configuration.numa_balancing)
    set_toptier_scale_factor(configuration.toptier_scale_factor)


def _run_workload(workload_names: List, number_of_workloads: Dict,
                  sleep_duration: int):
    for workload_name in workload_names:
        _scale_workload(workload_name, number_of_workloads[workload_name])
    sleep(sleep_duration)
    for workload_name in workload_names:
        _scale_workload(workload_name, 0)


def run_experiment(workload_names: List[str], number_of_workloads: Dict[str, int],
                   sleep_duration: int, experiment_type: ExperimentType):
    _set_configuration(experiment_type)
    _run_workload(workload_names, number_of_workloads, sleep_duration)
