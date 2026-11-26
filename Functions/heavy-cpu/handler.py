import math
def handle(event, context):
    total = 0
    for i in range(1, 3000000):
       total += math.sqrt(i)
    return {
        "statusCode": 200,
        "body": "Heavy CPU usage job completed!"
    }
