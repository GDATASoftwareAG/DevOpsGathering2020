
package io.app.model;

import java.util.Random;
import java.sql.Timestamp;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;

public class Trace {
	
    private String traceId;
    private String spanId;
    private String operationName;
    private String startTime;

	public Trace (String traceId, String spanId, String operationName, String startTime) {
		this.traceId = traceId; //rand.nextInt((99999999 - 1) + 1) + 1;
		this.spanId = spanId;
		this.operationName = operationName;
		this.startTime = startTime;		
	}
	
	public String toJSON() {
		
		return "{" + 
		"\"traceId\": " + this.traceId + 
		",\"spanId\": \"" + this.spanId + 
		"\",\"operationName\": \"" + this.operationName + 
		"\",\"startTime\": \"" + this.startTime + 
		"\"}";
	}
	
	public String gettraceId() {
        return this.traceId;
    }
	
	public String getspanId() {
        return this.spanId;
    }

    public String getoperationName() {
        return this.operationName;
    }

    public String getstartTime() {
        return this.startTime;
    }

    public Long geteventtime() {
        try {
            // "startTime":"2020-03-03T21:55:10.162007Z"
            DateFormat formatter = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'");
            Date date = formatter.parse(this.startTime);
            Timestamp timeStampDate = new Timestamp(date.getTime());

            return timeStampDate.getTime();
        } catch (ParseException e) {
            System.out.println("Exception :" + e);
            return null;
          }
    }

    public void settraceId(String traceId) {
        this.traceId = traceId;
    }

    public void setspanId(String spanId) {
        this.spanId = spanId;
    }

    public void setoperationName(String operationName) {
        this.operationName = operationName;
    }

    public void setstartTime(String startTime) {
        this.startTime = startTime;
    }	
	
	@Override
    public boolean equals(Object obj) {
        if (obj instanceof Trace) {
            Trace iTrace = (Trace) obj;
            return iTrace.canEquals(this) && spanId == iTrace.spanId;
        } else {
            return false;
        }
    }

    public boolean canEquals(Object obj) {
        return obj instanceof Trace;
    }
}
