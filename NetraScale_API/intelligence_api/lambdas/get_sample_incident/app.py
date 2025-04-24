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

    # TODO: Perform validate of the category here
    category = event["queryStringParameters"].get("category", None)
    category = category.upper()

    response = {
        "incidents":[]
    }


    # Retrieve the fundamentl environment variables
    db_host = os.environ['DB_HOST']
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']
    db_password = os.environ['DB_PASSWORD']
    db_port = os.environ.get('DB_PORT', 5432)

    # Establish basic variables for SQLcalls
    current_date = datetime.utcnow()
    year = current_date.year
    

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

        cursor.execute(
            """
            SELECT title, description, attack_vector, impact, mitigation_strategies
	        FROM public.security_incident where category = %s and year = %s
            """,
            ( category, year)
        )
        
        rows = cursor.fetchall()

        for row in rows:
            response["incidents"].append({
                "title": row[0],
                "description": row[1],
                "attack-vector": row[2],
                "impact": row[3],
                "mitigation": row[4]
            })
        
            
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
