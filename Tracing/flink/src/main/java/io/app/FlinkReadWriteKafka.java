package io.app;

import java.util.List;
import java.util.Map;
import java.util.ArrayList;
import java.util.Properties;

import org.apache.flink.cep.CEP;
import org.apache.flink.cep.PatternStream;
import org.apache.flink.cep.pattern.Pattern;
import org.apache.flink.cep.pattern.conditions.IterativeCondition;
import org.apache.flink.cep.PatternSelectFunction;

import org.apache.flink.api.common.restartstrategy.RestartStrategies;
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumer;
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaProducer;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.streaming.api.windowing.time.Time;

import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.api.common.functions.MapFunction;
import org.apache.flink.streaming.api.watermark.Watermark;
import org.apache.flink.streaming.api.functions.AssignerWithPeriodicWatermarks;
import org.apache.flink.api.java.functions.KeySelector;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import io.app.model.Trace;

public class FlinkReadWriteKafka {

    public static void main(String[] args) throws Exception {

        // setup streaming environment
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.getConfig().setRestartStrategy(RestartStrategies.fixedDelayRestart(4, 10000));
        env.enableCheckpointing(300000); // 300 seconds
        env.disableOperatorChaining();

        Properties properties = new Properties();
        properties.setProperty("bootstrap.servers", "kafka:9092");
        properties.setProperty("group.id", "flinkjob");

        DataStream<String> messageStream = env
            .addSource(new FlinkKafkaConsumer<>("traces", new SimpleStringSchema(), properties)).name("Read from Kafka");

        DataStream<Trace> dataStreamTrace = messageStream.map(new MapFunction<String, Trace>() {
            @Override				
            public Trace map(String value) throws Exception {                
                JSONParser parser = new JSONParser();
                JSONObject obj = (JSONObject) parser.parse(value);
                
                //JSONObject obj = new JSONObject(json);
                Trace iTrace = new Trace((String) obj.get("traceId"), (String) obj.get("spanId"), (String) obj.get("operationName"), (String) obj.get("startTime") );				
                //counter.inc();
                return iTrace;
            }
        });

        DataStream<Trace> dataStreamTraceTimestamped = dataStreamTrace.assignTimestampsAndWatermarks(new AssignerWithPeriodicWatermarks<Trace>() {

            @Override
            public long extractTimestamp(Trace element, long currentTimestamp) {
                return element.geteventtime();
            }
    
            @Override
            public Watermark getCurrentWatermark() {
                 return new Watermark(System.currentTimeMillis() - 10000); //10 sec out of order
            }
            });

    
        Pattern<Trace, ?> completed_pattern = Pattern.<Trace>begin("start").where(
            new IterativeCondition<Trace>() {
                @Override
                public boolean filter(Trace event,Context<Trace> ctx) {
                    return event.getoperationName().equals("workflow");
                }
            }
        ).followedByAny("middle").where(
            new IterativeCondition<Trace>() {
                @Override
                public boolean filter(Trace subEvent, Context<Trace> ctx) {
                    return subEvent.getoperationName().equals("startStaticalAnalysis");
                }
            }
        ).followedByAny("end").where(
                new IterativeCondition<Trace>() {
                @Override
                public boolean filter(Trace event, Context<Trace> ctx) {
                    return event.getoperationName().equals("Publish-SAMPLE_CLASSIFIED");	
                }
                }
        ).within(Time.seconds(1200));

        DataStream<Trace> partitionedInput = dataStreamTraceTimestamped.keyBy(new KeySelector<Trace, String>() {
            @Override
            public String getKey(Trace value) throws Exception {
                return value.gettraceId();
            }
        });

        PatternStream<Trace> patternStream = CEP.pattern(partitionedInput, completed_pattern);

        DataStream<Trace> correlation_stream = patternStream.select(new PatternSelectFunction<Trace, Trace>() {
                @Override
                public Trace select(Map<String, List<Trace>> matches) throws Exception {                
                    Trace start = (Trace) matches.get("start").get(0);
                    Trace middle = (Trace) matches.get("middle").get(0);
                    Trace end = (Trace) matches.get("end").get(0);
                    return new Trace( start.gettraceId(), "founde", "final", "trace");
                }
            });

        DataStream<String> dataStreamSink = correlation_stream.map(new MapFunction<Trace, String>() {
			@Override				
			public String map(Trace value) throws Exception {				
				return value.toJSON();
			}
        });
        
        dataStreamSink.addSink(new FlinkKafkaProducer<>(
                "GeneralOutput",
                new SimpleStringSchema(),
                properties)).name("Write To Kafka");

        env.execute("FlinkTracingJob");
    }
}
