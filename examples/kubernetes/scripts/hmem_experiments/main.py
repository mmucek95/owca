from runner import scale_down_all_workloads
from workload_runner import run_experiment
from scenarios import Scenario, SCENARIOS

def run_scenario(scenario: Scenario):
    for workload_counts in scenario.workloads_count:
        run_experiment(scenario.workloads, workload_counts,
                       scenario.sleep_duration, scenario.scenario_type)
    scale_down_all_workloads(wait_time=10)


def main():
    for scenario in SCENARIOS:
        run_scenario(scenario)


if __name__ == '__main__':
    main()
