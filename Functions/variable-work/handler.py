import time
import json
def handle(event, context):
    try:
       payload = json.loads(event.body or "{}") # reads either the incoming request or records as empty dictionary
       seconds = float(payload.get("seconds", 1)) # reads and converts the "seconds" key, or defaults to 1
    except (ValueError, TypeError):
        seconds = 1 # If there is an error, or the "seconds" key contains no value, default to 1
    seconds = max(0.0, min(seconds, 10)) # Add a min and max safety cap so no one can request long durations by accident
    time.sleep(seconds)
    return {
        "statusCode": 200,
       "body": f"Variable CPU usage job completed - slept for {seconds} seconds"

    }
