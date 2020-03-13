import time
import json
import uuid
import os
from datetime import date, datetime

from Tracing.core.core import CoreConnector
from prometheus_client import start_http_server, Gauge, Histogram
from neo4jrestclient.client import GraphDatabase

_INF = float("inf")
class startWorkflowConnector(CoreConnector):

    g_general_traces = Gauge('general_traces', 'general_traces', ["operation", "error"])
    h_span_duration = Histogram('span_duration', 'span_duration', ["operation"], buckets=[1, 10, 50, 100, 200, 500, 1000, 2000, 3000, 5000, 7000, 10000, _INF])
    g_span_duration = Gauge('g_span_duration', 'g_span_duration', ["operation"])
    start_time = None
    dependency_dict = {}

    def calcDependency(self, dependency):
        span_dependency_tree = set()

        for traceID in dependency.keys():
            for spanID in dependency[traceID].keys():
                endOp = dependency[traceID][spanID]['operationName']
                endService = dependency[traceID][spanID]['service']
                if len(dependency[traceID][spanID]['references']) == 1:
                    endTraceID = dependency[traceID][spanID]['references'][0]["traceId"]
                    endSpanID = dependency[traceID][spanID]['references'][0]["spanId"]
                    if dependency.get(endTraceID, {}).get(endSpanID, {}).get('operationName', None) is not None:
                        startOp = dependency[endTraceID][endSpanID]['operationName']
                        startService = dependency[endTraceID][endSpanID]['service']
                    else:
                        continue
                    span_dependency_tree.add((startService, startOp, endService, endOp))

        db = GraphDatabase(os.getenv("NEO4j", "http://neo4j:7474"))

        for dependency in span_dependency_tree:
            q = []
            q.append(f'MERGE (nodestart:Service{{name:"{dependency[0]}"}})')
            q.append(f'MERGE (nodesend:Operation{{name:"{dependency[1]}"}})')
            q.append(f'MERGE (nodestart:Service{{name:"{dependency[2]}"}})')
            if "communication" in dependency[3]:
                q.append(f'MERGE (nodesend:CommunicationLayer{{name:"{dependency[3]}"}})')
                q.append(f'MATCH (nodestart:CommunicationLayer{{name:"{dependency[3]}"}}), (nodesend:Service{{name:"{dependency[2]}"}}) MERGE (nodestart)-[:PART_OF]->(nodesend)')
            else:
                q.append(f'MERGE (nodesend:Operation{{name:"{dependency[3]}"}})')
                q.append(f'MATCH (nodestart:Operation{{name:"{dependency[3]}"}}), (nodesend:Service{{name:"{dependency[2]}"}}) MERGE (nodestart)-[:PART_OF]->(nodesend)')

            q.append(f'MATCH (nodestart:Operation{{name:"{dependency[0]}"}}), (nodesend:Operation{{name:"{dependency[1]}"}}) MERGE (nodestart)-[:DEPENDS]->(nodesend)')
            q.append(f'MATCH (nodestart:Operation{{name:"{dependency[1]}"}}), (nodesend:Service{{name:"{dependency[0]}"}}) MERGE (nodestart)-[:PART_OF]->(nodesend)')
            

            for query in q:
                results = db.query(query)
                print(results)

    def process_event(self, event, span_ctx):
        print(f"Progressing event { json.dumps(event)}")
        print(f"Using span context {span_ctx}")

        print(json.dumps(event))

        #check for tags
        error_flag = 'false'
        for tag in event['tags']:
            if tag.get('key', '') == 'error' and tag.get('vBool', False) == True:
                error_flag = 'true'

        self.g_general_traces.labels(operation=event['operationName'], error=error_flag).inc()
        self.h_span_duration.labels(operation=event['operationName']).observe(float(event['duration'][:-1].replace("-","")) * 1000)
        self.g_span_duration.labels(operation=event['operationName']).set(float(event['duration'][:-1].replace("-","")) * 1000)

        ## Dependency analysis ###################
        if self.start_time is None:
            self.start_time = time.time() * 1000

        #print(f"Progressing event { json.dumps(event)}")

        if event['traceId'] not in self.dependency_dict.keys():
            self.dependency_dict[event['traceId']] = {}

        self.dependency_dict[event['traceId']][event['spanId']] = {
            "operationName": event['operationName'],
            "references": event.get('references', []),
            "service": event['process']['serviceName']
        }
        #print(json.dumps(dependency_dict, indent=4))

        result_time = time.time() * 1000 - self.start_time
        print(result_time)
        if result_time > 30000:
            self.start_time = time.time() * 1000
            self.calcDependency(self.dependency_dict)
            self.dependency_dict = {}
        #######################

        return event

start_http_server(8089)
db = GraphDatabase(os.getenv("NEO4j", "http://neo4j:7474"))

results = db.query('CREATE CONSTRAINT ON (u:Operation) ASSERT u.name IS UNIQUE;')
results = db.query('CREATE CONSTRAINT ON (u:Service) ASSERT u.name IS UNIQUE;')
results = db.query('CREATE CONSTRAINT ON (u:CommunicationLayer) ASSERT u.name IS UNIQUE;')

iConn = startWorkflowConnector([os.getenv("KAFKA_HOST", "kafka:9092")], topics=["traces"], group_id="postprocessorlocal")
iConn.start_consuming()
time.sleep(15)
