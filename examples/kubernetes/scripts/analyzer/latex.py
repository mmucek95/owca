# https://docs.geoserver.org/latest/en/docguide/installlatex.html
# sudo yum --disablerepo=docker install latexmk texlive-lastpage texlive-collection-fontsrecommended texlive-collection-latexrecommended  texlive-latex-extra
# https://jeltef.github.io/PyLaTeX/current/examples/multirow.html
from typing import Dict, List

from pylatex import Document, Section, Subsection, Tabular, MultiColumn, MultiRow

from analyzer.model import Task
from analyzer.metrics import Metric


def create_latex_files(tasks: List[Task], experiment_type):
    doc = Document("multirow")
    section = Section(experiment_type)

    test5 = Subsection('Tasks')

    table5 = Tabular('|c|c|c|c|c|')
    table5.add_hline()
    # table5.add_row(('X', MultiColumn(5, align='|c|', data=MultiRow(2, data='multi-col-row'))))
    table5.add_row(('name', 'avg latency', 'avg throughput', 'q0.9 latency', 'q0.9 throughput'))
    table5.add_hline()
    for task in tasks:
        # table5.add_row((MultiColumn(5, align='|c|', data=''), 'X'))
        table5.add_row(
            (tasks[task].name,
             round(float(tasks[task].performance_metrics[Metric.TASK_LATENCY]['avg']), 3),
             round(float(tasks[task].performance_metrics[Metric.TASK_THROUGHPUT]['avg']), 3),
             round(float(tasks[task].performance_metrics[Metric.TASK_LATENCY]['q0.9,']), 3),
             round(float(tasks[task].performance_metrics[Metric.TASK_THROUGHPUT]['q0.9,']), 3))
        )
        table5.add_hline()

    test5.append(table5)
    section.append(test5)
    doc.append(section)
    doc.generate_pdf(clean_tex=True)
