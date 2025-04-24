
import json
import os
import psycopg2
from datetime import datetime

def lambda_handler(event, context):
    try:  
        org_id = event['pathParameters'].get('orgId', None)
    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing orgId parameter','event-stack':event}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    
    category = event["queryStringParameters"].get("category", None)
    category = category.upper()

    # the year associated to the risk factors
    current_year = datetime.now().year

    # the maximum number of results to return from the database for the invocation
    result_limit = 5

    cursor = None

    # Retrieve the fundamentl environment variables
    db_host = os.environ['DB_HOST']
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']
    db_password = os.environ['DB_PASSWORD']
    db_port = os.environ.get('DB_PORT', 5432)

    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )

        cursor = conn.cursor()

        cursor.execute("""
            SELECT category, problem_domain, risk_factor, severity 
	        FROM public.risk_factors_per_threat
	        where year = %s and category = %s and deprecated = false
	        order by severity desc limit %s;
        """, (current_year,category, result_limit))
        
        records = cursor.fetchall()

        response = {            
            "risk-factor-breakdown": [
                {
                    "severity": record[3],
                    "type": record[1],
                    "description": record[2],
                }
                for record in records
            ]
        }

        return {
            "statusCode": 200,
            "body": response,
            'headers': {
                'Content-Type': 'application/json'
            }
        }


    except psycopg2.Error as e:
        return {
            "statusCode": 500,
            "body": f"Database error: {str(e)}"
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


