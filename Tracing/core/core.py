import sys
import json
import time
import logging
import time
import random
from kafka import KafkaConsumer
from kafka import KafkaProducer
from kafka.errors import KafkaError
from opentracing.propagation import Format
from opentracing import child_of, follows_from
from jaeger_client import Config
from jaeger_client import constants as c


class CoreConnector():
    tracer = None

    def __init__(self, bootstrap_servers, topics=None, group_id=None):
        print(f"Connecting Producer to {bootstrap_servers}")
        self.producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
                                      value_serializer=lambda m: json.dumps(m).encode('ascii')
                                    )
        if topics is not None and group_id is not None:
            print(f"Connecting Consumer to {bootstrap_servers}")
            self.consumer = KafkaConsumer(*topics,
                                    group_id=group_id,
                                    #auto_offset_reset='earliest',
                                    bootstrap_servers=bootstrap_servers,
                                    value_deserializer=lambda m: json.loads(m.decode('ascii'))
                                    )
        logger = logging.getLogger('kafka')
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.ERROR)

    def publish_event(self, topic, event):
        self.producer.send(topic, event)

    def process_event(self, event, span_ctx):
        return event
    
    def start_consuming(self):
        span_ctx = None
        main_span = None

        for event in self.consumer:
            event = event.value
            if self.tracer is not None:
                event, span_ctx, main_span = self.extract_tracer(event)
            self.process_event(event, span_ctx)
            if main_span is not None:
                main_span.finish()
            
    def extract_tracer(self, event):
        print(event)
        carrier = {
            "uber-trace-id": event['tracer_context']
        }
        span_ctx = None if event['tracer_context'] is None else self.tracer.extract(Format.TEXT_MAP, carrier)
        main_span = None

        if span_ctx is None:
            main_span = self.tracer.start_span('workflow')
            span_ctx = main_span
            headers = {}
            self.tracer.inject(span_ctx, Format.TEXT_MAP, headers)
            event['tracer_context'] = headers['uber-trace-id']
            event['time'] = time.time()
        else:
            comm_span = self.tracer.start_span(f'communication-layer-{event["name"]}', child_of=span_ctx, start_time=event['time'])
            
            end =  time.time()
            comm_span.finish(end)
            print(f"Added comlayer: start: {event['time']} end: {end}")

        return event, span_ctx, main_span

    def init_tracer(self, service, jaeger_reporting_host):
        logging.getLogger('').handlers = []
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)
        config = Config(
            config={
                'sampler': {
                    'type': 'const',
                    'param': 1,
                },
                'local_agent': {
                    'reporting_host': jaeger_reporting_host,
                    'reporting_port': 5775,
                },
                'tags':{
                    c.JAEGER_IP_TAG_KEY: "127.0.0.1" # TODO: TempFix for ClockAdjustement issue of jaeger remove in the future!
                },
                'logging': True,
            },
            service_name=service
        )

        # this call also sets opentracing.tracer
        self.tracer = config.initialize_tracer()
        print("Init Tracer")
        return self.tracer
        
    def close_tracer(self):
        self.tracer.close()

def SimulateRuntime(mean, sigma=0):
    x = 0
    while x <=0:
        x = random.normalvariate(mean, sigma)
    
    time.sleep(x)
    return x