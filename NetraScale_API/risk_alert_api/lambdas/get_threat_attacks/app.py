import json
import psycopg2
import os

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

    if not category:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing category parameter','event-stack':event}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }


    category = category.upper()
    

    # the maximum number of results to return from the database for the invocation
    result_limit = event["queryStringParameters"].get("limit", 5)

    cursor = None
    conn = None
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


        # Fetch min(year) and max(year) for the category to build period
        cursor.execute("""
            SELECT MIN(year), MAX(year)
            FROM common_attack_data
            WHERE category = %s
        """, (category,))
        min_year, max_year = cursor.fetchone()
        if not min_year or not max_year:
            # No records found for this category
            return {
                "statusCode": 200,
                "body": json.dumps({"period": None, "threat-attacks": []}),
                'headers': {'Content-Type': 'application/json'}
            }
        period = f"{min_year} - {max_year}"


        cursor.execute("""
            SELECT year,target,industry,number_employees,market_cap,
                       location,ransom_cost,ransom_paid,source_article_url,
                       revenue,employees_range_min,employees_range_max
            FROM common_attack_data                       
            WHERE
                category = %s 
            ORDER BY 
                market_cap DESC NULLS LAST,
                revenue DESC NULLS LAST,
                year DESC
            LIMIT %s;
        """, (category, result_limit))

        records = cursor.fetchall()


        response = {
            "period":period,
            "threat-attacks": [
                {
                    "index":idx+1,
                    "year":record[0],
                    "target":record[1],
                    "industry":record[2],
                    "location":record[5],
                    "revenue":record[9],
                    "marketCap":record[4],
                    "link":record[8]	
                }
                for idx, record in enumerate(records)
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


    
 