import os
import statistics
import requests
from typing import List, Tuple
from collections import defaultdict
import pandas as pd
from pprint import pprint
from urllib import parse
from dataclasses import field
from dataclasses import dataclass
from typing import Dict
from enum import Enum

from runner import AEP_NODES, NODES_CAPACITIES


class PrometheusClient:
    BASE_URL = "http://100.64.176.36:30900"

    def range_query(self, query, start, end, step=1):
        """ range query - results vector
        https://prometheus.io/docs/prometheus/latest/querying/api/#range-vectors
        """
        urlr = self.BASE_URL + '/api/v1/query_range?{}'.format(parse.urlencode(dict(
            start=start, end=end, query=query, time=start, step=step)))
        r = requests.get(urlr)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise Exception(r.content) from e
        j = r.json()
        assert j['status'] != 'error'
        assert j['data']['resultType'] == 'matrix'
        data = j['data']['result']
        return data

    @staticmethod
    def instant_query(query, time):
        """ instant query
        https://prometheus.io/docs/prometheus/latest/querying/api/#instant-vectors

        Sample usage:
        r = instant_query("avg_over_time(task_llc_occupancy_bytes
            {app='redis-memtier-big', host='node37',
             task_name='default/redis-memtier-big-0'}[3000s])",
            1583395200)
        """
        urli = PrometheusClient.BASE_URL + '/api/v1/query?{}'.format(parse.urlencode(dict(
            query=query, time=time,)))
        r = requests.get(urli)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise Exception(r.content) from e
        j = r.json()
        assert j['status'] != 'error'
        assert j['data']['resultType'] == 'vector'
        data = j['data']['result']
        return data

    @staticmethod
    def convert_result_to_dict(result):
        """ Very memory inefficient!"""
        d = defaultdict(list)
        for series in result:
            metric = series['metric']
            # instant query
            if 'value' in series:
                for label_name, label_value in metric.items():
                    d[label_name].append(label_value)
                timestamp, value = series['value']
                d['value'].append(value)
                d['timestamp'].append(pd.Timestamp(timestamp, unit='s'))
            # range query
            elif 'values' in series:
                for value in series['values']:
                    for label_name, label_value in metric.items():
                        d[label_name].append(label_value)
                    timestamp, value = value
                    d['value'].append(value)
                    d['timestamp'].append(pd.Timestamp(timestamp, unit='s'))
            else:
                raise Exception('unsupported result type! (only matrix and instant are supported!)')
        d = dict(d)
        return d


@dataclass
class Stage:
    def __init__(self, t_start: int, t_end: int):
        SAFE_DELTA = 60  # 60 seconds back
        t_end -= SAFE_DELTA
        self.tasks: List[Task] = AnalyzerQueries.query_tasks_list(t_end)
        AnalyzerQueries.query_task_performance_metrics(time=t_end, tasks=self.tasks)

        self.nodes: Dict[str, Node] = {node_name: Node(node_name)
                                       for node_name in NODES_CAPACITIES.keys()}
        AnalyzerQueries.query_platform_performance_metrics(time=t_end, nodes=self.nodes)


@dataclass
class Task:
    name: str
    workload_name: str
    node: str
    performance_metrics: Dict[str, float] = field(default_factory=lambda: {})

    def if_aep(self):
        return self.node in AEP_NODES


@dataclass
class Node:
    name: str
    performance_metrics: Dict[str, float] = field(default_factory=lambda: {})


class StagesAnalyzer:
    def __init__(self, events, workloads):
        self.events_data = (events, workloads)

        # @Move to loader
        T_DELTA = os.environ.get('T_DELTA', 0)

        self.stages = []
        for i in (0, 2, 4):
            self.stages.append(Stage(t_start=events[i][0].timestamp()+T_DELTA,
                                     t_end=events[i+1][0].timestamp() + T_DELTA))

    def get_all_tasks_count_in_stage(self, stage: int):
        return sum(int(node.performance_metrics[Metric.POD_SCHEDULED]['instant'])
                   for node in self.stages[stage].nodes.values()
                   if Metric.POD_SCHEDULED in node.performance_metrics)

    @staticmethod
    def delete_report_files(report_root_dir):
        if os.path.isdir(report_root_dir):
            for file_ in os.listdir(report_root_dir):
                os.remove(os.path.join(report_root_dir, file_))

    def aep_report(self, report_root_dir: str, experiment_index: int):
        # Compare results from AEP to DRAM:
        # 1) list all workloads which are run on AEP (Task.workload.name) in stage 3 (or 2)
        #   a) for all this workloads read performance on DRAM in stage 1
        # 2) for assertion and consistency we could also check how compare results in all stages
        # 3) compare results which we got AEP vs DRAM separately for stage 2 and 3
        #   a) for each workload:

        # baseline results in stage0 on DRAM
        for i in range(len(self.stages)):
            assert self.get_all_tasks_count_in_stage(0) > 20

        # task throughput
        @dataclass
        class PSummary:
            """Performance summary"""
            throughput: float
            latency: float

        def get_throughput_q01(task: Task) -> float:
            return float(task.performance_metrics[Metric.TASK_THROUGHPUT]['q0.1,'])

        def get_latency_q09(task: Task) -> float:
            return float(task.performance_metrics[Metric.TASK_LATENCY]['q0.9,'])

        # Use worst values of: throughput q0.1 and latency q0.9, as baseline
        workloads_baseline = {}
        for task in self.stages[0].tasks.values():
            workload = task.workload_name
            throughput_q01 = get_throughput_q01(task)
            latency_q09 = get_latency_q09(task)
            if workload not in workloads_baseline:
                workloads_baseline[workload] = PSummary(throughput_q01, latency_q09)
            else:
                if throughput_q01 < workloads_baseline[workload].throughput:
                    workloads_baseline[workload].throughput = throughput_q01
                if latency_q09 > workloads_baseline[workload].latency:
                    workloads_baseline[workload].latency = latency_q09

        def get_throughput(task: Task, subvalue) -> float:
            return float(task.performance_metrics[Metric.TASK_THROUGHPUT][subvalue])

        def get_latency(task: Task, subvalue) -> float:
            return float(task.performance_metrics[Metric.TASK_LATENCY][subvalue])

        workloads_baseline_avg = {}
        all_workloads = set(task.workload_name for task in self.stages[0].tasks.values())
        for workload in all_workloads:
            tasks = [
                task for task in self.stages[0].tasks.values() if task.workload_name == workload]
            throughput = statistics.mean([get_throughput(task, 'avg') for task in tasks])
            latency = statistics.mean([get_latency(task, 'avg') for task in tasks])
            workloads_baseline_avg[workload] = PSummary(throughput, latency)

        # Compare to baseline results which we got on AEP
        @dataclass
        class TaskSummary:
            def __init__(self, task, throughput_optimistic_result, latency_optimistic_result,
                         throughput_average_result, latency_average_result, limits):
                self.task: Task = task
                self.latency_optimistic_result: float = latency_optimistic_result
                self.throughput_optimistic_result: float = throughput_optimistic_result
                self.latency_average_result: float = latency_average_result
                self.throughput_average_result: float = throughput_average_result
                self.pass_optimistic_limits = self.throughput_optimistic_result > \
                    limits.throughput and \
                    self.latency_optimistic_result < limits.latency
                self.pass_average_limits = self.throughput_average_result > \
                    limits.throughput and self.latency_average_result < limits.latency

            def to_dict(self):
                return {
                    'latency_optimistic_result': self.latency_optimistic_result,
                    'throughput_optimistic_result': self.throughput_optimistic_result,
                    'latency_average_result': self.latency_average_result,
                    'throughput_average_result': self.throughput_average_result,
                    'taskname': self.task.name, 'workload': self.task.workload_name,
                    'pass_optimistic_limits': self.pass_optimistic_limits,
                    'pass_average_limits': self.pass_average_limits}

        # @TODO should set as parameter
        limits = PSummary(throughput=0.8, latency=1.5)

        # copied from below, replica of code, just changed index
        aep_tasks_summaries_kubernetes_only = []
        for task in [task for task in self.stages[1].tasks.values() if task.node in AEP_NODES]:
            workload = task.workload_name
            throughput_q01 = get_throughput_q01(task)
            latency_q09 = get_latency_q09(task)
            throughput_avg = get_throughput(task, 'avg')
            latency_avg = get_latency(task, 'avg')

            task_summary = TaskSummary(task,
                                       throughput_q01 / workloads_baseline[workload].throughput,
                                       latency_q09 / workloads_baseline[workload].latency,
                                       throughput_avg / workloads_baseline_avg[workload].throughput,
                                       latency_avg / workloads_baseline_avg[workload].latency,
                                       limits)
            aep_tasks_summaries_kubernetes_only.append(task_summary)

        aep_tasks_summaries = []
        for task in [task for task in self.stages[2].tasks.values() if task.node in AEP_NODES]:
            workload = task.workload_name
            throughput_q01 = get_throughput_q01(task)
            latency_q09 = get_latency_q09(task)
            throughput_avg = get_throughput(task, 'avg')
            latency_avg = get_latency(task, 'avg')

            task_summary = TaskSummary(task,
                                       throughput_q01 / workloads_baseline[workload].throughput,
                                       latency_q09 / workloads_baseline[workload].latency,
                                       throughput_avg / workloads_baseline_avg[workload].throughput,
                                       latency_avg / workloads_baseline_avg[workload].latency,
                                       limits)
            aep_tasks_summaries.append(task_summary)

        def node_to_dict(node: Node):
            assert len(AEP_NODES) == 1, 'Not adjusted to multiple nodes'
            return {'name': node.name,
                    'cpu_requested': round(float(
                        node.performance_metrics[Metric.PLATFORM_CPU_REQUESTED]['instant']), 2),
                    'cpu_requested [%]': round(float(
                        node.performance_metrics[Metric.PLATFORM_CPU_REQUESTED]['instant']) /
                                               AEP_NODES[0]['cpu'] * 100, 2),
                    'cpu_util': round(float(
                        node.performance_metrics[Metric.PLATFORM_CPU_UTIL]['instant']), 2),
                    'mem_requested': round(float(
                        node.performance_metrics[Metric.PLATFORM_MEM_USAGE]['instant']), 2),
                    'mem_requested [%]': round(float(
                        node.performance_metrics[Metric.PLATFORM_MEM_USAGE]['instant']) /
                                               AEP_NODES[0]['mem'] * 100, 2),
                    'mbw_total': round(float(
                        node.performance_metrics[Metric.PLATFORM_MBW_TOTAL]['instant']), 2),
                    'dram_hit_ratio [%]': round(float(
                        node.performance_metrics[Metric.PLATFORM_DRAM_HIT_RATIO]['instant']) *
                                                100, 2),
                    'wss_used (aprox)': round(float(
                        node.performance_metrics[Metric.PLATFORM_WSS_USED]['instant']), 2),
                    'wss_used (aprox) [%]': round(float(
                        node.performance_metrics[Metric.PLATFORM_WSS_USED]['instant']) /
                                                  193 * 100, 2),
                    }
        node_df_kubernetes_only = pd.DataFrame([node_to_dict(self.stages[1].nodes['node101'])])
        aep_tasks__kubernetes_only_df = pd.DataFrame(
            [task_summary.to_dict() for task_summary in aep_tasks_summaries_kubernetes_only])

        node_df = pd.DataFrame([node_to_dict(self.stages[2].nodes['node101'])])
        aep_tasks_df = pd.DataFrame(
            [task_summary.to_dict() for task_summary in aep_tasks_summaries])

        with open(os.path.join(report_root_dir, 'results_df.txt'), 'a+') as fref:
            fref.write('*' * 90 + '\n')
            fref.write("Experiment index: {}\n\n".format(experiment_index))
            for i in range(5):
                fref.write("Time event {}: {}.\n".format(
                           i, self.events_data[0][i][0].strftime("%d-%b-%Y (%H:%M:%S)")))
            fref.write("\nWorkloads scheduled:\n{}\n".format(pprint.pformat(
                self.events_data[1], indent=0, width=120, compact=True)))
            utilization_file = os.path.join(os.path.dirname(report_root_dir),
                                            'chosen_workloads_utilization.{}.txt'.format(
                                                experiment_index))
            utilization = open(utilization_file).readlines()[0].rstrip()
            fref.write("Utilization of resources: {}\n".format(utilization))

            fref.write("\n***KUBERNETET BASELINE***\n")
            fref.write(str(node_df_kubernetes_only.to_string()))
            fref.write('\n\n')
            fref.write(str(aep_tasks__kubernetes_only_df.to_string()))
            fref.write('\n\n')
            fref.write('Passed {}/{} avg limit >>{}<<\n'.format(
                           len([task for task in aep_tasks_summaries_kubernetes_only if
                                task.pass_average_limits]),
                           len(aep_tasks_summaries_kubernetes_only),
                           limits))
            fref.write('Passed {}/{} optimistic limit >>{}<<\n'.format(
                            len([task for task in aep_tasks_summaries_kubernetes_only if
                                 task.pass_optimistic_limits]),
                            len(aep_tasks_summaries_kubernetes_only), limits))

            fref.write("\n***WCA-SCHEDULER***\n")
            fref.write(str(node_df.to_string()))
            fref.write('\n\n')
            fref.write(str(aep_tasks_df.to_string()))
            fref.write('\n\n')
            fref.write('Passed {}/{} avg limit >>{}<<\n'.format(
                            len([task for task in aep_tasks_summaries if task.pass_average_limits]),
                            len(aep_tasks_summaries),
                            limits))
            fref.write('Passed {}/{} optimistic limit >>{}<<\n'.format(len(
                [task for task in aep_tasks_summaries if task.pass_optimistic_limits]),
                len(aep_tasks_summaries), limits))

            fref.write('*' * 90 + '\n')
            fref.write('\n\n\n')


class Metric(Enum):
    TASK_THROUGHPUT = 'task_throughput'
    TASK_LATENCY = 'task_latency'

    # platform
    TASK_UP = 'task_up'
    POD_SCHEDULED = 'platform_tasks_scheduled'
    PLATFORM_MEM_USAGE = 'platform_mem_usage'
    PLATFORM_CPU_REQUESTED = 'platform_cpu_requested'
    PLATFORM_CPU_UTIL = 'platform_cpu_util'
    PLATFORM_MBW_TOTAL = 'platform_mbw_total'
    PLATFORM_DRAM_HIT_RATIO = 'platform_dram_hit_ratio'
    PLATFORM_WSS_USED = 'platform_wss_used'


MetricsQueries = {
    Metric.TASK_THROUGHPUT: 'apm_sli',
    Metric.TASK_LATENCY: 'apm_sli2',

    # platform
    Metric.TASK_UP: 'task_up',
    Metric.POD_SCHEDULED: 'wca_tasks',
    Metric.PLATFORM_MEM_USAGE: 'sum(task_requested_mem_bytes) by (nodename) / 1e9',
    Metric.PLATFORM_CPU_REQUESTED: 'sum(task_requested_cpus) by (nodename)',
    Metric.PLATFORM_CPU_UTIL: "sum(1-rate(node_cpu_seconds_total{mode='idle'}[10s])) "
                              "by(nodename) / sum(platform_topology_cpus) by (nodename)",
    Metric.PLATFORM_MBW_TOTAL: 'sum(platform_dram_reads_bytes_per_second + '
                               'platform_pmm_reads_bytes_per_second) by (nodename) / 1e9',
    Metric.PLATFORM_DRAM_HIT_RATIO: 'avg(platform_dram_hit_ratio) by (nodename)',
    Metric.PLATFORM_WSS_USED: 'sum(avg_over_time(task_wss_referenced_bytes[15s])) '
                              'by (nodename) / 1e9',
}


class Function(Enum):
    AVG = 'avg_over_time'
    QUANTILE = 'quantile_over_time'


FunctionsDescription = {
    Function.AVG: 'avg',
    Function.QUANTILE: 'q',
}


def build_function_call_id(function: Function, arg: str):
    return "{}{}".format(FunctionsDescription[function], str(arg))


class AnalyzerQueries:
    """Class used for namespace"""

    @staticmethod
    def query_tasks_list(time) -> Dict[str, Task]:
        query_result = PrometheusClient.instant_query(MetricsQueries[Metric.TASK_UP], time)
        tasks = {}
        for metric in query_result:
            metric = metric['metric']
            task_name = metric['task_name']
            tasks[task_name] = Task(metric['task_name'], metric['app'],
                                    metric['nodename'])
        return tasks

    @staticmethod
    def query_platform_performance_metrics(time: int, nodes: Dict[str, Node]):
        metrics = (Metric.PLATFORM_MEM_USAGE, Metric.PLATFORM_CPU_REQUESTED,
                   Metric.PLATFORM_CPU_UTIL, Metric.PLATFORM_MBW_TOTAL,
                   Metric.POD_SCHEDULED, Metric.PLATFORM_DRAM_HIT_RATIO, Metric.PLATFORM_WSS_USED)

        for metric in metrics:
            query_results = PrometheusClient.instant_query(MetricsQueries[metric], time)
            for result in query_results:
                nodes[result['metric']['nodename']].performance_metrics[metric] = \
                    {'instant': result['value'][1]}

    @staticmethod
    def query_performance_metrics(time: int, functions_args: List[Tuple[Function, str]],
                                  metrics: List[Metric], window_length: int) -> Dict[Metric, Dict]:
        """performance metrics which needs aggregation over time"""
        query_results: Dict[Metric, Dict] = {}
        for metric in metrics:
            for function, arguments in functions_args:
                query_template = "{function}({arguments}{prom_metric}[{window_length}s])"
                query = query_template.format(function=function.value,
                                              arguments=arguments,
                                              window_length=window_length,
                                              prom_metric=MetricsQueries[metric])
                query_result = PrometheusClient.instant_query(query, time)
                aggregation_name = build_function_call_id(function, arguments)
                if metric in query_results:
                    query_results[metric][aggregation_name] = query_result
                else:
                    query_results[metric] = {aggregation_name: query_result}
        return query_results

    @staticmethod
    def query_task_performance_metrics(time: int, tasks: Dict[str, Task]):
        window_length = 120  # [s]
        metrics = (Metric.TASK_THROUGHPUT, Metric.TASK_LATENCY)

        function_args = ((Function.AVG, ''), (Function.QUANTILE, '0.1,'),
                         (Function.QUANTILE, '0.9,'),)

        query_results = AnalyzerQueries.query_performance_metrics(time, function_args,
                                                                  metrics, window_length)
        for metric, query_result in query_results.items():
            for aggregation_name, result in query_result.items():
                for per_app_result in result:
                    task_name = per_app_result['metric']['task_name']
                    value = per_app_result['value'][1]
                    if metric in tasks[task_name].performance_metrics:
                        tasks[task_name].performance_metrics[metric][aggregation_name] = value
                    else:
                        tasks[task_name].performance_metrics[metric] = {aggregation_name: value}


def load_events_file(filename):
    # Each python structure in separate file.
    with open(filename) as fref:
        il = 0
        workloads_ = []
        events_ = []
        for line in fref:
            if il % 2 == 0:
                workloads = eval(line)
                if type(workloads) == dict:
                    workloads_.append(workloads)
                else:
                    break
            if il % 2 == 1:
                events = eval(line)
                if type(events) == list:
                    events_.append(events)
                else:
                    break
            il += 1
    assert len(workloads_) == len(events_), 'Wrong content of event file'
    return [(workloads, events) for workloads, events in zip(workloads_, events_)]


def analyze_3stage_experiment(events_file, report_root_dir):
    # Loads data from event file created in runner stage.
    for i, (workloads, events) in enumerate(load_events_file(events_file)):
        stages_analyzer = StagesAnalyzer(events, workloads)
        if i == 0:
            stages_analyzer.delete_report_files(report_root_dir)
        stages_analyzer.aep_report(report_root_dir, experiment_index=i)


if __name__ == "__main__":
    # @Archive:
    # experiment_dir = '2020-03-10_14.17'
    # experiment_dir = 'creatonealg_2020-03-14'
    # experiment_dir = 'creatonealg_2020-03-15'
    # experiment_dir= 'creatonealg_2020_03-17__target_score_set__ugly_fixes'
    # experiment_dir = 'creatonealg_2020-03-17__target_score_set__ugly_fixes__night'

    experiment_dir = '2020-03-18__hp_enabled'
    analyze_3stage_experiment('results/{}/events.txt'.format(experiment_dir),
                              'results/{}/runner_analyzer'.format(experiment_dir))
