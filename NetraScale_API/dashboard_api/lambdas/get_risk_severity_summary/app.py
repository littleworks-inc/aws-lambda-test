import json
import os
import psycopg2
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Event received: %s", json.dumps(event))
    try:
        #org_id = event['orgId']        
        org_id = event['pathParameters'].get('orgId', None)
    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing orgId parameter','event-stack':event}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    # TODO: Perform validate of the category here
    #category = event["queryStringParameters"].get("category", None)
    #category = category.upper()


    # Retrieve the fundamentl environment variables
    db_host = os.environ['DB_HOST']
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']
    db_password = os.environ['DB_PASSWORD']
    db_port = os.environ.get('DB_PORT', 5432)

    # Establish basic variables for SQLcalls
    current_date = datetime.utcnow()
    month = current_date.month
    year = current_date.year
    author = "system"
    
    response = None

    # Store the risk score in the historical table.
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

        # Ensure the organization exists
        cursor.execute("SELECT id FROM public.\"Organization\" WHERE id = %s", (org_id,))
        if not cursor.fetchone():
            return {
                "statusCode": 400,
                "body": f"Organization with ID {org_id} does not exist."
            }

        # Check if a record already exists for this organization, month, and year
        cursor.execute(
            """
            SELECT 
                SUM(CASE WHEN score BETWEEN 0 AND 25 THEN 1 ELSE 0 END) AS Low,
                SUM(CASE WHEN score BETWEEN 26 AND 50 THEN 1 ELSE 0 END) AS Medium,
                SUM(CASE WHEN score BETWEEN 51 AND 75 THEN 1 ELSE 0 END) AS High,
                SUM(CASE WHEN score BETWEEN 76 AND 100 THEN 1 ELSE 0 END) AS Critical
            FROM 
                historical_risk_score
            WHERE 
                organization_id = %s 
                AND month = %s 
                AND year = %s;

            """,
            (org_id, month, year)
        )
        records = cursor.fetchone()

        response = None

        if records[0] is None:
            response = {
                "statusCode": 200,
                "body": json.dumps({
                    "low": 0,
                    "medium": 0,
                    "high": 0,
                    "critical": 0
                })
            }
        else:
            response = {
                "statusCode": 200,
                "body": json.dumps({
                    "low": records[0],
                    "medium": records[1],
                    "high": records[2],
                    "critical": records[3]
                })
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


    return {
        'statusCode': 200,
        'body': json.dumps(response),
        'headers': {
            'Content-Type': 'application/json'
        }
    }
 

