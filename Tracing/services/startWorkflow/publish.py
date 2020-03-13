import time
import json
import uuid
import hashlib
import random
import string
import os
from Tracing.core.core import CoreConnector, SimulateRuntime

class PublishConnector(CoreConnector):
    def process_event(self, event):
        return event

iConn = PublishConnector([os.getenv("KAFKA_HOST", "kafka:9092")])
iConn.init_tracer("startWorkflow", os.getenv("JAEGER_AGENT", "jaeger-agent"))

N=10
content = ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))
event = {
    "id": str(uuid.uuid4()),
    "time": time.time(),
    "tracer_context": None,
    "name": "NEW_SAMPLE_RECEIVED",
    "metadata": {
        "sha256": hashlib.sha256(content.encode('utf-8')).hexdigest()
    }
}

counter = 0
while True:
    print(f"{counter} / 100")
    counter += 1

    iConn.publish_event("NEW_SAMPLE_RECEIVED", event)

    if os.getenv("PUBLISHER_RATE_GENERATOR", "CONST") == "CONST":
        timerate = int(os.getenv("PUBLISHER_RATE", 60))
        time.sleep(timerate)
        print(f"Waited { timerate } sec")
    elif os.getenv("PUBLISHER_RATE_GENERATOR", "CONST") == "PROB":
        x = SimulateRuntime(os.getenv("PUBLISHER_RATE", 60), int(os.getenv("PUBLISHER_RATE", 60)) * 0.3)
        print(f"Waited { x } sec")