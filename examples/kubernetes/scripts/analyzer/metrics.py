# Copyright (c) 2020 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from enum import Enum


class Metric(Enum):
    TASK_THROUGHPUT = 'task_throughput'
    TASK_LATENCY = 'task_latency'

    # platform
    TASK_UP = 'task_up'
    WCA_UP = 'wca_up'
    # POD_SCHEDULED = 'platform_tasks_scheduled'
    PLATFORM_MEM_USAGE = 'platform_mem_usage'
    PLATFORM_CPU_REQUESTED = 'platform_cpu_requested'
    PLATFORM_CPU_UTIL = 'platform_cpu_util'
    PLATFORM_MBW_READS = 'platform_mbw_reads'
    PLATFORM_MBW_WRITES = 'platform_mbw_writes'
    # PLATFORM_DRAM_HIT_RATIO = 'platform_dram_hit_ratio'
    PLATFORM_WSS_USED = 'platform_wss_used'
    # hmem
    TASK_MEM_NUMA_PAGES = 'task_mem_numa_pages'

    ### raw:
    # grupa 1
    PLATFORM_CAS_COUNT_READS = 'platform_cas_count_reads'
    PLATFORM_CAS_COUNT_WRITES = 'platform_cas_count_writes'
    PLATFORM_PMM_BANDWIDTH_READS = 'platform_pmm_bandwidth_reads'
    PLATFORM_PMM_BANDWIDTH_WRITES = 'platform_pmm_bandwidth_writes'
    # grupa 2
    PLATFORM_UPI_RXL_FLITS = 'platform_upi_rxl_flits'
    PLATFORM_UPI_TXL_FLITS = 'platform_upi_txl_flits'
    # grupa 3
    PLATFORM_RPQ_OCCUPANCY = 'platform_rpq_occupancy'
    PLATFORM_RPQ_INSERTS = 'platform_rpq_inserts'
    PLATFORM_IMC_CLOCKTICKS = 'platform_imc_clockticks'

    ### derived_metrics
    PLATFORM_PMM_READS_BYTES_PER_SECOND = 'platform_pmm_reads_bytes_per_second'
    PLATFORM_PMM_WRITES_BYTES_PER_SECOND = 'platform_pmm_writes_bytes_per_second'
    PLATFORM_PMM_TOTAL_BYTES_PER_SECOND = 'platform_pmm_total_bytes_per_second'
    PLATFORM_DRAM_READS_BYTES_PER_SECOND = 'platform_dram_reads_bytes_per_second'
    PLATFORM_DRAM_WRITES_BYTES_PER_SECOND = 'platform_dram_writes_bytes_per_second'
    PLATFORM_DRAM_TOTAL_BYTES_PER_SECOND = 'platform_dram_total_bytes_per_second'
    PLATFORM_DRAM_HIT_RATIO = 'platform_dram_hit_ratio'
    PLATFORM_UPI_BANDWIDTH_BYTES_PER_SECOND = 'platform_upi_bandwidth_bytes_per_second'
    PLATFORM_RPQ_READ_LATENCY_SECONDS = 'platform_rpq_read_latency_seconds'

    #### surowe:
    # 1 grupa
    # - platform_cas_count_reads
    # - platform_cas_count_writes
    # - platform_pmm_bandwidth_reads
    # - platform_pmm_bandwidth_writes
    # 2 grupa
    # - platform_upi_rxl_flits
    # - platform_upi_txl_flits
    # 3 grupa
    # - platform_rpq_occupancy
    # - platform_rpq_inserts
    # - platform_imc_clockticks
    #### pochodne (chyba nie trzeba ich enablowac, albo juz sa enablowane)z 1 pierszej grupy:
    # - platform_pmm_reads_bytes_per_second
    # - platform_pmm_writes_bytes_per_second
    # - platform_pmm_total_bytes_per_second
    # - platform_dram_reads_bytes_per_second
    # - platform_dram_writes_bytes_per_second
    # - platform_dram_total_bytes_per_second
    # - platform_dram_hit_ratio
    # wyswietlic sume po socketa (ale nie per pmu/mc)z 2giej grupy:
    # - platform_upi_bandwidth_bytes_per_second
    # wyswietlic sume po socketa (ale nie per pmu/mc)z 3 grupy:
    # - platform_rpq_read_latency_seconds


platform_metrics = [
    Metric.PLATFORM_PMM_READS_BYTES_PER_SECOND,
    Metric.PLATFORM_PMM_WRITES_BYTES_PER_SECOND,
    Metric.PLATFORM_PMM_TOTAL_BYTES_PER_SECOND,
    Metric.PLATFORM_DRAM_READS_BYTES_PER_SECOND,
    Metric.PLATFORM_DRAM_WRITES_BYTES_PER_SECOND,
    Metric.PLATFORM_DRAM_TOTAL_BYTES_PER_SECOND,
    Metric.PLATFORM_DRAM_HIT_RATIO,
    Metric.PLATFORM_UPI_BANDWIDTH_BYTES_PER_SECOND,
    Metric.PLATFORM_RPQ_READ_LATENCY_SECONDS,
]


MetricsQueries = {
    Metric.TASK_THROUGHPUT: 'apm_sli2',
    Metric.TASK_LATENCY: 'apm_sli',

    # platform
    Metric.TASK_UP: 'task_up',
    Metric.WCA_UP: 'wca_up',
    # Metric.POD_SCHEDULED: 'wca_tasks',
    Metric.PLATFORM_MEM_USAGE: 'sum(task_requested_mem_bytes) by (nodename) / 1e9',
    Metric.PLATFORM_CPU_REQUESTED: 'sum(task_requested_cpus) by (nodename)',
    # @TODO check if correct (with htop as comparison)
    Metric.PLATFORM_CPU_UTIL: "sum(1-rate(node_cpu_seconds_total{mode='idle'}[10s])) "
                              "by(nodename) / sum(platform_topology_cpus) by (nodename)",
    Metric.PLATFORM_MBW_READS: 'sum(platform_dram_reads_bytes_per_second + '
                               'platform_pmm_reads_bytes_per_second) by (nodename) / 1e9',
    Metric.PLATFORM_MBW_WRITES: 'sum(platform_dram_writes_bytes_per_second + '
                                'platform_pmm_writes_bytes_per_second) by (nodename) / 1e9',
    Metric.PLATFORM_DRAM_HIT_RATIO: 'avg(platform_dram_hit_ratio) by (nodename)',
    Metric.PLATFORM_WSS_USED: 'sum(avg_over_time(task_wss_referenced_bytes[15s])) '
                              'by (nodename) / 1e9',
    # hmem
    Metric.TASK_MEM_NUMA_PAGES: 'task_mem_numa_pages{host="nodename"} * 4096',

    ### raw:
    # grupa 1
    Metric.PLATFORM_CAS_COUNT_READS: 'platform_cas_count_reads',
    Metric.PLATFORM_CAS_COUNT_WRITES: 'platform_cas_count_writes',
    Metric.PLATFORM_PMM_BANDWIDTH_READS: 'platform_pmm_bandwidth_reads',
    Metric.PLATFORM_PMM_BANDWIDTH_WRITES: 'platform_pmm_bandwidth_writes',
    # grupa 2
    Metric.PLATFORM_UPI_RXL_FLITS: 'platform_upi_rxl_flits',
    Metric.PLATFORM_UPI_TXL_FLITS: 'platform_upi_txl_flits',
    # grupa 3
    Metric.PLATFORM_RPQ_OCCUPANCY: 'platform_rpq_occupancy',
    Metric.PLATFORM_RPQ_INSERTS: 'platform_rpq_inserts',
    Metric.PLATFORM_IMC_CLOCKTICKS: 'platform_imc_clockticks',

    ### derived_metrics
    Metric.PLATFORM_PMM_READS_BYTES_PER_SECOND:
        'sum(platform_pmm_reads_bytes_per_second{}) by (__name__, nodename, socket)',
    Metric.PLATFORM_PMM_WRITES_BYTES_PER_SECOND:
        'sum(platform_pmm_writes_bytes_per_second{}) by (__name__, nodename, socket)',
    Metric.PLATFORM_PMM_TOTAL_BYTES_PER_SECOND:
        'sum(platform_pmm_total_bytes_per_second{}) by (__name__, nodename, socket)',
    Metric.PLATFORM_DRAM_READS_BYTES_PER_SECOND:
        'sum(platform_dram_reads_bytes_per_second{}) by (__name__, nodename, socket)',
    Metric.PLATFORM_DRAM_WRITES_BYTES_PER_SECOND:
        'sum(platform_dram_writes_bytes_per_second{}) by (__name__, nodename, socket)',
    Metric.PLATFORM_DRAM_TOTAL_BYTES_PER_SECOND:
        'sum(platform_dram_total_bytes_per_second{}) by (__name__, nodename, socket)',
    Metric.PLATFORM_DRAM_HIT_RATIO:
        'sum(platform_dram_hit_ratio{}) by (__name__, nodename, socket)',
    Metric.PLATFORM_UPI_BANDWIDTH_BYTES_PER_SECOND:
        'sum(platform_upi_bandwidth_bytes_per_second{}) by (__name__, nodename, socket)',
    Metric.PLATFORM_RPQ_READ_LATENCY_SECONDS:
        'sum(platform_rpq_read_latency_seconds{}) by (__name__, nodename, socket)',


}


class Function(Enum):
    AVG = 'avg_over_time'
    QUANTILE = 'quantile_over_time'
    STDEV = 'stddev_over_time'


FunctionsDescription = {
    Function.AVG: 'avg',
    Function.QUANTILE: 'q',
    Function.STDEV: 'stdev',
}
