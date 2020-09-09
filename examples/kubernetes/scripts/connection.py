import requests
from collections import defaultdict
from urllib import parse
import logging
import pandas as pd


logger = logging.getLogger(__name__)


class PrometheusClient:
    BASE_URL = "http://100.64.176.35:30900"

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
            query=query, time=time, )))
        try:
            r = requests.get(urli)
        except requests.exceptions.ConnectionError as e:
            logging.error("Connecting error with Prometheus. Error: {}".format(e.response))
            return []
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
