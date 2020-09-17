# https://docs.geoserver.org/latest/en/docguide/installlatex.html
# sudo yum --disablerepo=docker install latexmk texlive-lastpage texlive-collection-fontsrecommended texlive-collection-latexrecommended  texlive-latex-extra
# https://jeltef.github.io/PyLaTeX/current/examples/multirow.html
from typing import Dict, List

from pylatex import Document, Section, Subsection, Tabular, MultiColumn, MultiRow

from analyzer.metrics import Metric


class LatexDocument:
    def __init__(self, name):
        self.doc = Document(name)

    def add_experiment_data(self, experiment_name, tasks):
        section = Section(experiment_name)
        workloads_results = Subsection('Tasks')

        # create table with results
        table = Tabular('|c|c|c|c|c|')
        table.add_hline()
        table.add_row(('name', 'avg latency', 'avg throughput', 'q0.9 latency', 'q0.9 throughput'))
        table.add_hline()

        for task in tasks:
            table.add_row(
                (tasks[task].name.replace('default/', ''),
                 round(float(tasks[task].performance_metrics[Metric.TASK_LATENCY]['avg']), 3),
                 round(float(tasks[task].performance_metrics[Metric.TASK_THROUGHPUT]['avg']), 3),
                 round(float(tasks[task].performance_metrics[Metric.TASK_LATENCY]['q0.9,']), 3),
                 round(float(tasks[task].performance_metrics[Metric.TASK_THROUGHPUT]['q0.9,']), 3))
            )
            table.add_hline()

        workloads_results.append(table)
        section.append(workloads_results)
        self.doc.append(section)

    def generate_pdf(self):
        self.doc.generate_pdf(clean_tex=True)
