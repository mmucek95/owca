from time import time

from runner import scale_down_all_workloads
from workload_runner import run_experiment, experiment_to_json
from scenarios import Scenario, REDIS_SCENARIOS


def run_scenario(scenario: Scenario):
    for workload_count in scenario.workloads_count:
        experiment = run_experiment(scenario.name, scenario.workloads, workload_count,
                                    scenario.sleep_duration, scenario.scenario_type)
        experiment_to_json(experiment, 'results/{}-{}.json'.format(scenario.name, time()))
    scale_down_all_workloads(wait_time=10)


def main():
    # redis
    for scenario in REDIS_SCENARIOS:
        run_scenario(scenario)


if __name__ == '__main__':
    main()
