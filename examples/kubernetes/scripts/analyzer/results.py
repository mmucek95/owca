# https://docs.geoserver.org/latest/en/docguide/installlatex.html
# sudo yum --disablerepo=docker install latexmk texlive-lastpage
# texlive-collection-fontsrecommended texlive-collection-latexrecommended
# texlive-latex-extra
# https://jeltef.github.io/PyLaTeX/current/examples/multirow.html

from pylatex import Document, Section, Subsection, Tabular, Figure

from metrics import Metric

import matplotlib.pyplot as plt
import numpy as np

AVG = 'avg'
Q09 = 'q0.9,'

NAME = 'name'
UNIT = 'unit'

# METRIC NAMES
AVG_LATENCY = 'avg_latency'
AVG_THROUGHPUT = 'avg_throughput'
Q09_LATENCY = 'q09_latency'
Q09_THROUGHPUT = 'q09_throughput'

METRIC_METADATA = {AVG_LATENCY: {NAME: 'Average latency', UNIT: 'ms'},
                   AVG_THROUGHPUT: {NAME: 'Average throughput', UNIT: 'ops'},
                   Q09_LATENCY: {NAME: 'quantile 0.9 latency', UNIT: 'ms'},
                   Q09_THROUGHPUT: {NAME: 'quantile 0.9 throughput', UNIT: 'ops'}}


class ExperimentResults:
    def __init__(self, name):
        geometry_options = {"margin": "0.7in"}
        self.doc = Document(name, geometry_options=geometry_options)
        self.sections = {}
        self.metric_values = {AVG_LATENCY: {}, AVG_THROUGHPUT: {},
                              Q09_LATENCY: {}, Q09_THROUGHPUT: {}}
        self.experiment_types = []

    @staticmethod
    def _get_task_index(task_name):
        index = ''
        for i in range(len(task_name) - 1, 0, -1):
            if task_name[i] == '-':
                break
            else:
                index = task_name[i] + index
        return index

    def _strip_task_name(self, task_name):
        index = self._get_task_index(task_name)
        stripped_task_name = task_name.replace('default/', '')
        stripped_task_name = stripped_task_name.replace('-{}'.format(index), '')
        return stripped_task_name

    def discover_experiment_data(self, experiment_name, experiment_type, tasks, task_counts):
        if experiment_name not in self.sections.keys():
            self.sections[experiment_name] = Section(experiment_name)
        if experiment_type not in self.experiment_types:
            self.experiment_types.append(experiment_type)

        workloads_results = Subsection('')
        # create table with results
        table = Tabular('|c|c|c|c|c|')
        table.add_hline()
        table.add_row(('name', 'avg latency', 'avg throughput', 'q0.9 latency', 'q0.9 throughput'))
        table.add_hline()

        for task in tasks:
            task_count = task_counts[self._strip_task_name(task)]
            average_latency = round(float(
                tasks[task].performance_metrics[Metric.TASK_LATENCY][AVG]), 3)
            average_throughput = round(float(
                tasks[task].performance_metrics[Metric.TASK_THROUGHPUT][AVG]), 3)
            q09_latency = round(float(
                tasks[task].performance_metrics[Metric.TASK_LATENCY][Q09]), 3)
            q09_throughput = round(float(
                tasks[task].performance_metrics[Metric.TASK_THROUGHPUT][Q09]), 3)
            table.add_row(
                (tasks[task].name.replace('default/', ''), average_latency,
                 average_throughput, q09_latency, q09_throughput)
            )
            table.add_hline()

            task_metrics = {AVG_LATENCY: average_latency,
                            AVG_THROUGHPUT: average_throughput,
                            Q09_LATENCY: q09_latency,
                            Q09_THROUGHPUT: q09_throughput}

            task_index = self._get_task_index(task)
            for metric_name, metric_value in task_metrics.items():
                if task_count in self.metric_values[metric_name]:
                    if task_index in self.metric_values[metric_name][task_count]:
                        self.metric_values[metric_name][task_count][task_index].update(
                            {experiment_type: metric_value})
                    else:
                        self.metric_values[metric_name][task_count][task_index] = \
                            {experiment_type: metric_value}
                else:
                    self.metric_values[metric_name][task_count] = \
                        {task_index: {experiment_type: metric_value}}

        workloads_results.append(table)
        self.sections[experiment_name].append(workloads_results)

    def _generate_document(self):
        for section in self.sections.values():
            self.doc.append(section)

    def generate_bar_graph(self, metric_name, metric_values):
        labels = self.experiment_types
        for workload_data in metric_values.values():
            x = np.arange(len(labels))
            width = 0.1
            fig, ax = plt.subplots(figsize=(15, 15))

            data_per_workload = []
            for _ in workload_data:
                data_per_workload.append([])

            for label in labels:
                i = 0
                for workload in workload_data.values():
                    if label in workload:
                        data_per_workload[i].append(workload[label])
                    else:
                        data_per_workload[i].append(0)
                    i += 1

            for i in range(len(data_per_workload)):
                ax.bar(x - width + i * width, data_per_workload[i],
                       width, label=i)

            ax.set_ylabel('{} ({})'.format(METRIC_METADATA[metric_name][NAME],
                                           METRIC_METADATA[metric_name][UNIT]))
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.legend()

            with self.doc.create(Figure(position='htbp')) as plot:
                plot.add_plot()
                caption = '{} workload(s)'.format(str(len(data_per_workload)))
                plot.add_caption(caption)

    def generate_pdf(self):
        self._generate_document()
        for metric_name, metric_values in self.metric_values.items():
            self.generate_bar_graph(metric_name, metric_values)
        self.doc.generate_pdf(clean_tex=True)
