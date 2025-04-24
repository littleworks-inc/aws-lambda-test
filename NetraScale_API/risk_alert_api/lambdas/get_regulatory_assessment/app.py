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

    
    # Determine if the data is for a specific focus area or general use
    focus = event["queryStringParameters"].get("focus", "RISKALERTS")

    # Handle errorneous user input for the focus value
    if focus not in ["RISKALERTS", "GENERAL"]:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid focus parameter'}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    

    category = event["queryStringParameters"].get("category", None)
    if category:
        category = category.upper()

    country = event["queryStringParameters"].get("country", None)
    if country:
        country = country.upper()

    sector = event["queryStringParameters"].get("sector", None)
    if sector:
        sector = sector.upper()

    region = event["queryStringParameters"].get("region", None)
    if region:
        region = region.upper()
        

    # Create the JSON response template
    response = {
        "regulatory-assessment": {
        "regulatory-area": category,
        "regulatory-statements": []
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

        # While we will "never" have these many regulations, this creates the generic cap for the query
        row_limit = 500

    

        if focus == "RISKALERTS":
            # set the limit for risk alert results
            row_limit = 5

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

        # Build the basic query to obtain regulations
        query = "SELECT regulation,penalty,sector,comments FROM security_regulations WHERE attack_type = %s  "
        params = [category]

        
        # Add optional filters
        if country and country != "ALL":
            query += " AND country = %s"
            params.append(country)
        if sector and sector != "ALL":
            query += " AND (sector = %s OR sector = 'ALL')"
            params.append(sector)
        if region:
            query += " AND region = %s"
            params.append(region)

        # Add the row limit to the query
        query += " LIMIT %s;"
        params.append(row_limit)

        # Execute the query
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            records = cursor.fetchall()

        # Populate the JSON response based on the query results
        for result in records:
            response["regulatory-assessment"]["regulatory-statements"].append({
                "type": result[0],
                "action": result[1],
                "sector": result[2],
                "comments": result[3]
            })
    
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

