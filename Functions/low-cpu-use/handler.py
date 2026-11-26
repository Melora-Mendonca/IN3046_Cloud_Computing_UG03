import time
def handle(event, context):
    time.sleep(1)
    return {
        "statusCode": 200,
        "body": "Low CPU usage job completed!"
    }
