from fastapi import FastAPI, HTTPException
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from pydantic import BaseModel
import uvicorn


app = FastAPI()

# Configuration (Matches Docker Compose)
INFLUX_URL = "http://localhost:8086"
TOKEN = "my-super-secret-token"
ORG = "my-sdk-org"
BUCKET = "metrics_bucket"

client = InfluxDBClient(url=INFLUX_URL, token=TOKEN, org=ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Match your Android MetricEntity exactly


class Metric(BaseModel):
    metricId: str
    value: float
    timestamp: int  # System.currentTimeMillis() from SDK
    screenName: str
    type: str


@app.post("/v1/metrics/batch")
async def receive_batch(metrics: Request):
    try:
        points = []
        for m in metrics:
            # We convert the Android long timestamp to Nanoseconds for Influx
            point = Point("performance_data") \
                .tag("sdk_metric_id", m.metricId) \
                .tag("screen_name", m.screenName) \
                .tag("event_type", m.type) \
                .field("value", m.value) \
                .time(m.timestamp, WritePrecision.MS)
            points.append(point)

        # Direct write to DB (No queue for now)
        write_api.write(bucket=BUCKET, org=ORG, record=points)

        return {"status": "ok", "received": len(metrics)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
