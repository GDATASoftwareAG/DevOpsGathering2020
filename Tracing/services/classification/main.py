import time
import json
import uuid
import os
from Tracing.core.core import CoreConnector
from opentracing import child_of, follows_from

class ClassificatorConnector(CoreConnector):
    event_state = {}

    def process_event(self, event, span_ctx):
        print(f"Progressing event { json.dumps(event)}")
        print(f"Using span context {span_ctx}")

        with self.tracer.start_span(f"startClassification-{event['name']}", child_of=span_ctx) as span:
            span.log_kv({"event": event})
            time.sleep(0.1)

            if event['correlation_id'] not in self.event_state.keys():
                self.event_state[event['correlation_id']] = {}    
            self.event_state[event['correlation_id']][event['name']] = event

            if "SANDBOX_RUN_COMPLETE" in self.event_state[event['correlation_id']].keys() and "STATICAL_ANALYSIS_COMPLETE"  in self.event_state[event['correlation_id']].keys():

                event["id"] = str(uuid.uuid4())
                event["time"] = time.time()
                event["name"] = "SAMPLE_CLASSIFIED"  

                event["metadata"] = { **self.event_state[event['correlation_id']]['SANDBOX_RUN_COMPLETE']['metadata'], **self.event_state[event['correlation_id']]['STATICAL_ANALYSIS_COMPLETE']['metadata'] }

                with self.tracer.start_span(f'Publish-{event["name"]}', child_of=span) as child_span:
                    self.publish_event("SAMPLE_CLASSIFIED", event)
                    del self.event_state[event['correlation_id']]

        return event

iConn = ClassificatorConnector([os.getenv("KAFKA_HOST", "kafka:9092")], topics=["SANDBOX_RUN_COMPLETE", "STATICAL_ANALYSIS_COMPLETE"], group_id="classificator")
iConn.init_tracer("Classificator", os.getenv("JAEGER_AGENT", "jaeger-agent"))
iConn.start_consuming()
time.sleep(15)
iConn.close_tracer()
time.sleep(15)