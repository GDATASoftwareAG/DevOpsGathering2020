# OpenTracing Prototype

> Prototype according to presentation DevOpsGathering 2020 - "Tracing - a journey to the tactical insight"
> author: Florian Kuckelkorn
> email: Florian.Kuckelkorn ( at ) gdata.de

## Deployment

Deployment for single-node docker swarm (docker needs to be installed)

```sh
ansible-playbook -i inventory/swarm play.yml
```

4 different stacks are getting deployed on the target system
ptl -> SwarmPit for Docker Swarm management
tracing -> general tracing dependencies
worker -> sample worker
flink -> apache flink cluster for cep pattern detection on  trace stream

## Flink

If you want to test the flink job just sent the target jar file from the flink subdirectory to the flink jobmanager

## Grafana

If you want to visualize some metrics, you can build your own dashboard or use the prepared dashboard in Tracing/grafana.
You need to setup a prometheus datasource first (check docker-compose.tracing.yml for closer deployment)

## Service Behaviour

If you want to simulate certain service behavior, change the service environment variable according to the python scripts