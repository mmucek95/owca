import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Union, Iterable, Any
import pandas as pd
from metrics import Metric, MetricsQueries, Function, FunctionsDescription
from runner import ClusterInfoLoader


class ExperimentType(Enum):
    SingleWorkloadsRun = 'SingleWorkloadsRun'
    SteppingSingleWorkloadsRun = 'SteppingSingleWorkloadsRun'
    ThreeStageStandardRun = 'ThreeStageStandardRun'
    Hmem = 'Hmem'


@dataclass
class ExperimentMeta:
    data_path: str
    title: str
    description: str
    params: Dict[str, str]
    changelog: str
    bugs: str
    experiment_type: ExperimentType = ExperimentType.ThreeStageStandardRun
    experiment_baseline_index: int = 0
    commit_hash: str = 'unknown'

    def data_path_(self):
        return os.path.basename(self.data_path)


@dataclass
class Task:
    name: str
    workload_name: str
    node: str
    performance_metrics: Dict[str, float] = field(default_factory=lambda: {})

    def if_aep(self):
        return self.node in ClusterInfoLoader.get_instance().get_aep_nodes()

    def get_throughput(self, subvalue) -> Optional[float]:
        if Metric.TASK_THROUGHPUT in self.performance_metrics:
            return float(self.performance_metrics[Metric.TASK_THROUGHPUT][subvalue])
        else:
            return None

    def get_latency(self, subvalue) -> Optional[float]:
        if Metric.TASK_LATENCY in self.performance_metrics:
            return float(self.performance_metrics[Metric.TASK_LATENCY][subvalue])
        else:
            return None

    def has_metrics(self):
        # avg of a task behaviour
        throughput = self.get_throughput('avg')
        latency = self.get_latency('avg')
        if throughput is None or latency is None:
            return False
        else:
            return True


@dataclass
class Node:
    name: str
    performance_metrics: Dict[str, float] = field(default_factory=lambda: {})

    def to_dict(self, nodes_capacities: Dict[str, Dict]) -> Dict:
        # @TODO should be taken from queries
        node_cpu = nodes_capacities[self.name]['cpu']
        node_mem = nodes_capacities[self.name]['mem']

        if Metric.PLATFORM_CPU_REQUESTED not in self.performance_metrics:
            # means that no tasks were run on the node
            return {}

        return {
            'name': self.name,

            'cpu_requested': round(
                float(self.performance_metrics[Metric.PLATFORM_CPU_REQUESTED]['instant']), 2),
            'cpu_requested [%]': round(float(
                self.performance_metrics[Metric.PLATFORM_CPU_REQUESTED][
                    'instant']) / node_cpu * 100, 2),
            'cpu_util [experimental]': round(
                float(self.performance_metrics[Metric.PLATFORM_CPU_UTIL]['instant']), 2),

            'mem_requested': round(
                float(self.performance_metrics[Metric.PLATFORM_MEM_USAGE]['instant']), 2),
            'mem_requested [%]': round(float(
                self.performance_metrics[Metric.PLATFORM_MEM_USAGE]['instant']) / node_mem * 100,
                                       2),

            'mbw_reads [GB]': round(
                float(self.performance_metrics[Metric.PLATFORM_MBW_READS]['instant']), 2),
            'mbw_writes [GB]': round(
                float(self.performance_metrics[Metric.PLATFORM_MBW_WRITES]['instant']), 2),
            'mbw_flat [GB]': round(3.7 * float(
                self.performance_metrics[Metric.PLATFORM_MBW_WRITES]['instant']) + float(
                self.performance_metrics[Metric.PLATFORM_MBW_READS]['instant']), 2),

            'dram_hit_ratio [%]': round(
                float(self.performance_metrics[Metric.PLATFORM_DRAM_HIT_RATIO]['instant']) * 100,
                2),

            'wss_used (aprox)': round(
                float(self.performance_metrics[Metric.PLATFORM_WSS_USED]['instant']), 2),

            'mem/cpu (requested)': round(
                float(self.performance_metrics[Metric.PLATFORM_MEM_USAGE]['instant']) /
                float(self.performance_metrics[Metric.PLATFORM_CPU_REQUESTED]['instant']), 2)
        }

    @staticmethod
    def to_dataframe(nodes: List[Any], nodes_capacities: Dict[str, Dict]) -> pd.DataFrame:
        return pd.DataFrame([node.to_dict(nodes_capacities) for node in nodes])


@dataclass
class Stat:
    """Statistics"""
    avg: float
    min: float
    max: float
    stdev: float


@dataclass
class WStat:
    """Workload Statistics"""
    name: str
    latency: Stat
    throughput: Stat
    count: int

    def to_dict(self):
        return {
            "LB_min": round(self.latency.min, 2),
            "LB_avg": round(self.latency.avg, 2),
            "LB_max": round(self.latency.max, 2),
            "L_stdev": round(self.latency.stdev, 2),
            "L_stdev[%]": round(self.latency.stdev / self.latency.avg * 100, 2),
            # ---
            "TB_min": round(self.throughput.min, 2),
            "TB_avg": round(self.throughput.avg, 2),
            "TB_max": round(self.throughput.max, 2),
            "T_stdev": round(self.throughput.stdev, 2),
            "T_stdev[%]": round(self.throughput.stdev / self.throughput.avg * 100, 2),
            # ---
            "B_count": self.count,
            "app": self.name
        }

    @staticmethod
    def to_dataframe(wstats: List[Any]) -> pd.DataFrame:
        return pd.DataFrame([wstat.to_dict() for wstat in wstats])
