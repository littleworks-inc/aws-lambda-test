import json

def lambda_handler(event, context):
    # Default response for API Gateway
    response = {
        "statusCode": 200,
        "body": json.dumps({
            "annualized-loss-expectancy": 30000,
            "single-loss-expectancy": 10000,
            "annualized-rate-of-occurrence": 0.5,
            "potential-impact-rating": "High",
            "cost-of-inaction": 10000,
        })
    }
    return response
