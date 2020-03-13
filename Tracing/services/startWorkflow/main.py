import os
import time
import random
import json
import uuid
from Tracing.core.core import CoreConnector
from opentracing import child_of, follows_from

class startWorkflowConnector(CoreConnector):
    def process_event(self, event, span_ctx):
        print(f"Progressing event { json.dumps(event)}")
        print(f"Using span context {span_ctx}")
        print(type(span_ctx))

        with self.tracer.start_span('startWorkflowSampleProgressing', child_of=span_ctx) as span:
            span.log_kv({"event": event})
            time.sleep(1)
            event['id'] = str(uuid.uuid4())
            event['correlation_id'] = str(uuid.uuid4())            
            event["name"] = "SAMPLE_RECEIVED"  

            with self.tracer.start_span(f'Publish-{event["name"]}', child_of=span) as child_span:
                event["time"] = time.time()
                if os.getenv("SIMULATE_COMMLAYER_DELAY", "NO") == "CONST":
                    time.sleep(2)
                elif os.getenv("SIMULATE_COMMLAYER_DELAY", "NO") == "PROBABILISTIC":
                    time.sleep(time.sleep(random.normalvariate(5, 0.5)))
                
                self.publish_event("SAMPLE_RECEIVED", event)

        return event

iConn = startWorkflowConnector([os.getenv("KAFKA_HOST", "kafka:9092")], topics=["NEW_SAMPLE_RECEIVED"], group_id="startWorkflow")
iConn.init_tracer("startWorkflow", os.getenv("JAEGER_AGENT", "jaeger-agent"))
iConn.start_consuming()
time.sleep(15)
iConn.close_tracer()
time.sleep(15)