import json
import os
import psycopg2
from decimal import Decimal

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

    # Database connection parameters
    db_host = os.environ['DB_HOST']
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']
    db_password = os.environ['DB_PASSWORD']
    db_port = os.environ.get('DB_PORT', 3306)

    conn = None  # Initialize conn before the try block

    # Connect to PostgreSQL database
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )

        # Retrieve country and sector from database
        query = "SELECT industry, region FROM public.\"Organization\" where id=%s;"
        params = [org_id]

        with conn.cursor() as cursor:
            cursor.execute(query, params)
            records = cursor.fetchone()

            if records:
                sector = records[0]
                country = records[1]

                country = country.upper()
                sector = sector.upper()

        # if we have no country or sector, than return a blank response
        if country == None or sector == None:
            response = {
                "statusCode": 200,
                "body": json.dumps({
                "regulation-count": 0,
                "compliance-percent": 0,
                "in-progress": [],
                })
            }
    
            return response

        # Build the basic query to obtain regulations
        query = """
            SELECT DISTINCT ON (sr.regulation)
                sr.regulation,
                ors.is_favorite,
                ors.implementation_state,
                ors.percent_complete
            FROM 
                public.security_regulations sr
            LEFT JOIN 
                organization_regulation_state ors
            ON 
                sr.id = ors.regulation_id AND ors.organization_id = %s
            WHERE 
                sr.country = '%s' AND sr.sector = '%s';

        """ % (org_id, country, sector)
            
        # Create the JSON response template
        response = {
            "regulatory-statistics": {
            "regulation-count": 0,
            "compliance-percent": 0,
            "in-progress": []
            }
        }


        # Execute the query
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            records = cursor.fetchall()

        # count the number of regulations
        regulation_count = len(records)
        response["regulatory-statistics"]["regulation-count"] = regulation_count

        # count the number at 100% complete
        complete_count = 0

        # Populate the JSON response based on the query results
        for result in records:
            response["regulatory-statistics"]["in-progress"].append({
                "name": result[0],
                "compliance": float(result[3]) if isinstance(result[3], Decimal) else result[3],
            })

            if result[3] == 100:
                complete_count += 1
        
        complete_percent = complete_count

        if complete_count >0:
            response["regulatory-statistics"]["compliance-percent"] = (complete_percent / regulation_count)*100
    
    except psycopg2.Error as e:
        return {
            "statusCode": 500,
            "body": f"Database error: {e}"
        }
    finally:    
        if conn:
            cursor.close()
            conn.close()        
        
        return {
            'statusCode': 200,
            'body': json.dumps(response),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
