import time
import json
import uuid
import os
import string
import hashlib
import random
from numpy.random import choice
from Tracing.core.core import CoreConnector
from Tracing.core.core import SimulateRuntime
from opentracing import child_of, follows_from

class StaticalAnalyserConnector(CoreConnector):
    def process_event(self, event, span_ctx):
        print(f"Progressing event { json.dumps(event)}")
        print(f"Using span context {span_ctx}")

        with self.tracer.start_span('startStaticalAnalysis', child_of=span_ctx) as span:
            span.log_kv({"event": event})
            SimulateRuntime(5, 4)
            event["id"] = str(uuid.uuid4())
            event["name"] = "STATICAL_ANALYSIS_COMPLETE"  

            content = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            random_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            hashlist = ["cfc71c242a485dd2ef1cbf2f9c9d720a64e72b73a3dff2da719f548a495ae143",
                        "860c73012ba6059cd3a85bfa4186f2bccf343d4d30a84a82ae10c897c1c4276e", 
                        "3e7a24ab6d6dad852eba9269dea1254032167d95a4381d3ed8a04372c4bd5655", 
                        "cff989ab9f739f1b0f963c862153c5a150e2255a875c791df2ac7ee88b866757",
                        random_hash]
            IMPORT_HASH = choice(hashlist, 1, p=[0.5, 0.3, 0.1, 0.05, 0.05])[0]

            event["metadata"]["ImportHash"] = IMPORT_HASH

            with self.tracer.start_span(f'Publish-{event["name"]}', child_of=span) as child_span:
                event["time"] = time.time()
                self.publish_event("STATICAL_ANALYSIS_COMPLETE", event)

        return event

iConn = StaticalAnalyserConnector([os.getenv("KAFKA_HOST", "kafka:9092")], topics=["SAMPLE_RECEIVED"], group_id="staticalanalyser")
iConn.init_tracer("StaticalAnalyser", os.getenv("JAEGER_AGENT", "jaeger-agent"))
iConn.start_consuming()
time.sleep(15)
iConn.close_tracer()
time.sleep(15)