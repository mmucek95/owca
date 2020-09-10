#!/usr/bin/env python3.6


NUMA_BALANCING_FILE = '/proc/sys/kernel/numa_balancing'
TOPTIER_BALANCING_FILE = '/proc/sys/vm/toptier_scale_factor'


def set_numa_balancing(turned_on=True):
    numa_balancing_value = '2'
    if not turned_on:
        numa_balancing_value = '1'
    with open(NUMA_BALANCING_FILE, 'w') as numa_balancing_file:
        numa_balancing_file.write(numa_balancing_value)


def set_toptier_scale_factor(value='2000'):
    with open(TOPTIER_BALANCING_FILE, 'w') as toptier_scale_factor_file:
        toptier_scale_factor_file.write(value)
