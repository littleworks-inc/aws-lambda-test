import json
import psycopg2
import os
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

    

    # the maximum number of results to return from the database for the invocation
    result_limit = 10

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

        

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT overall_risk_score, risk_level_indicator, summary_statement, date_of_last_assessment
	            FROM public.overall_risk_score where organization_id = %s;                    
            """, (org_id,))

            records = cursor.fetchall()
            response = {}

            print(records)

            if records == None or len(records) == 0:
                response = {
                    "overall-risk-score": [
                        {                    
                            "score":"TBD",
                            "indicator":"---",
                            "summary":"",
                            "assessment":"Under Assessment"
                        }                        
                    ]
                }
            else:
                response = {
                    "overall-risk-score": [
                        {                    
                            "score":record[0],
                            "indicator":record[1],
                            "summary":record[2],
                            "assessment":record[3].isoformat() if isinstance(record[3], datetime) else record[3]
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
