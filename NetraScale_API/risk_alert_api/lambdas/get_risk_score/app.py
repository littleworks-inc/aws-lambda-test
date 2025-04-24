import json
import os
import psycopg2
from datetime import datetime

def lambda_handler(event, context):
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
    category = event["queryStringParameters"].get("category", None)
    category = category.upper()


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
    
    risk_score = None

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
            SELECT id,score FROM historical_risk_score
            WHERE organization_id = %s AND month = %s AND year = %s AND category = %s
            """,
            (org_id, month, year,category)
        )
        existing_record = cursor.fetchone()

        if existing_record:
           risk_score = existing_record[1]
        
            
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


    # Return the risk score to the client
    response = {
        "risk-score": risk_score
    }
    
    return {
        'statusCode': 200,
        'body': json.dumps(response),
        'headers': {
            'Content-Type': 'application/json'
        }
    }
