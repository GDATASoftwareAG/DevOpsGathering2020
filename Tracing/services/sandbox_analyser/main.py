import time
import json
import uuid
import os
from numpy.random import choice
from Tracing.core.core import CoreConnector
from Tracing.core.core import SimulateRuntime
from opentracing import child_of, follows_from

class SandboxAnalyserConnector(CoreConnector):
    def process_event(self, event, span_ctx):
        print(f"Progressing event { json.dumps(event)}")
        print(f"Using span context {span_ctx}")

        with self.tracer.start_span('startSandboxAnalysis', child_of=span_ctx) as span:
            span.log_kv({"event": event})
            with self.tracer.start_span('S3_GET', child_of=span) as child_span:
                with self.tracer.start_span('S3_RETRIVAL', child_of=child_span) as child_child_span:
                    if os.getenv("SIMULATE_S3_BEHAVIOUR", "CONST") == "CONST":
                        SimulateRuntime(1, 0)
                    elif os.getenv("SIMULATE_S3_BEHAVIOUR", "CONST") == "PROBABILISTIC":
                        SimulateRuntime(5, 3)
                    elif os.getenv("SIMULATE_S3_BEHAVIOUR", "CONST") == "ERROR":                        
                        x = SimulateRuntime(3, 2)
                        if x >= 4:
                            child_child_span.set_tag('error', True)
                            return event

                with self.tracer.start_span('SAVE_FILE', child_of=child_span) as child_child_span:
                    SimulateRuntime(2, 0.8)

            with self.tracer.start_span('VM_DEPLOYMENT', child_of=span) as child_span:
                with self.tracer.start_span('CONTACT_HYPERVISOR', child_of=child_span) as child_child_span:
                    SimulateRuntime(1, 0.5)
                with self.tracer.start_span('PROVISION', child_of=child_span) as child_child_span:
                    SimulateRuntime(2, 0.5)
                with self.tracer.start_span('START_VM', child_of=child_span) as child_child_span:
                    SimulateRuntime(0.1, 0.5)

            with self.tracer.start_span('EXECUTE_SAMPLE', child_of=span) as child_span:
                SimulateRuntime(10)

            with self.tracer.start_span('DECT_RULES', child_of=span) as child_span:
                SimulateRuntime(3, 1)

            event["id"] = str(uuid.uuid4())
            event["name"] = "SANDBOX_RUN_COMPLETE"  

            DECT_RULE = choice(["RULE_A", "RULE_B", "RULE_C", "RULE_D", "RULE_E"], 1, p=[0.5, 0.3, 0.1, 0.05, 0.05])[0]
            event["metadata"]["DECT_RULE"] = DECT_RULE
            
            with self.tracer.start_span(f'Publish-{event["name"]}', child_of=span) as child_span:
                event["time"] = time.time()
                self.publish_event("SANDBOX_RUN_COMPLETE", event)

        return event

iConn = SandboxAnalyserConnector([os.getenv("KAFKA_HOST", "kafka:9092")], topics=["SAMPLE_RECEIVED"], group_id="sandboxanalyser")
iConn.init_tracer("SandboxAnalyser", os.getenv("JAEGER_AGENT", "jaeger-agent"))
iConn.start_consuming()
time.sleep(15)
iConn.close_tracer()
time.sleep(15)