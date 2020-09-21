# https://docs.geoserver.org/latest/en/docguide/installlatex.html
# sudo yum --disablerepo=docker install latexmk texlive-lastpage
# texlive-collection-fontsrecommended texlive-collection-latexrecommended
# texlive-latex-extra
# https://jeltef.github.io/PyLaTeX/current/examples/multirow.html

from pylatex import Document, Section, Subsection, Tabular, Figure

from analyzer.metrics import Metric

import matplotlib.pyplot as plt
import numpy as np

AVG = 'avg'
Q09 = 'q0.9,'


class LatexDocument:
    def __init__(self, name):
        geometry_options = {"margin": "0.7in"}
        self.doc = Document(name, geometry_options=geometry_options)
        self.sections = {}
        self.average_latency_values = {}
        self.experiment_types = []

    def add_experiment_data(self, experiment_name, experiment_type, tasks, task_counts):
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
            task_count = task_counts[task[:-2].replace('default/', '')]
            average_latency = round(float(tasks[task].performance_metrics[Metric.TASK_LATENCY][AVG]), 3)
            table.add_row(
                (tasks[task].name.replace('default/', ''), average_latency,
                 round(float(tasks[task].performance_metrics[Metric.TASK_THROUGHPUT][AVG]), 3),
                 round(float(tasks[task].performance_metrics[Metric.TASK_LATENCY][Q09]), 3),
                 round(float(tasks[task].performance_metrics[Metric.TASK_THROUGHPUT][Q09]), 3))
            )
            table.add_hline()

            task_index = task[-1]
            if task_count in self.average_latency_values:
                if task_index in self.average_latency_values[task_count]:
                    self.average_latency_values[task_count][task_index].update({experiment_type: average_latency})
                else:
                    self.average_latency_values[task_count][task_index] = {experiment_type: average_latency}
            else:
                self.average_latency_values[task_count] = {task_index: {experiment_type: average_latency}}

        workloads_results.append(table)
        self.sections[experiment_name].append(workloads_results)

    def _generate_document(self):
        for section in self.sections.values():
            self.doc.append(section)

    def generate_bar_graph(self):
        labels = self.experiment_types
        for workload_data in self.average_latency_values.values():
            x = np.arange(len(labels))
            width = 0.1
            fig, ax = plt.subplots(figsize=(15, 15))

            data_per_workload = []
            for _ in workload_data:
                data_per_workload.append([])

            for label in labels:
                i = 0
                for workload in workload_data.values():
                    data_per_workload[i].append(workload[label])
                    i += 1

            for i in range(len(data_per_workload)):
                ax.bar(x - width + i * width, data_per_workload[i],
                       width, label=i)

            ax.set_ylabel('Latency')
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.legend()

            with self.doc.create(Figure(position='htbp')) as plot:
                plot.add_plot()
                caption = '{} workload(s)'.format(str(len(data_per_workload)))
                plot.add_caption(caption)

    def generate_pdf(self):
        self._generate_document()
        self.generate_bar_graph()
        self.doc.generate_pdf(clean_tex=True)
