import time
def handle(event, context):
    time.sleep(3)
    return {
        "statusCode": 200,
        "body": "Moderate CPU usage job completed!"
    }