import json
import os
import psycopg2

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
    
    # TODO: Implement scope to limit the number of results to return within specific parameters
    scope = event["queryStringParameters"].get("scope", None)
    
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
            WITH ranked_threats AS (
                SELECT 
                    problem_domain, 
                    mitigation_action, 
                    priority, 
                    category,
                    tactic_state,
                    ROW_NUMBER() OVER (PARTITION BY category ORDER BY priority DESC) AS rank
                FROM 
                    general_threat_mitigation_activities
            )
            SELECT 
                problem_domain, 
                mitigation_action, 
                priority, 
                category,
                tactic_state
            FROM 
                ranked_threats
            WHERE 
                category = %s 
            ORDER BY 
                rank, category
            LIMIT %s;
        """, (category, result_limit))
        
        

        records = cursor.fetchall()

        response = {
            "mitigation-strategy": "---",
            "mitigation-actions": [
                {
                    "type": record[0],
                    "action": record[1],
                    "priority": record[2],
                    "state": record[4]
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

