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


        # Retrieve country and sector from database
        query = "SELECT industry, region FROM public.\"Organization\" where id=%s;"
        params = [org_id]

        country = None
        sector = None

        with conn.cursor() as cursor:
            cursor.execute(query, params)
            records = cursor.fetchone()

            if records:
                sector = records[0]
                country = records[1]

                country = country.upper()
                sector = sector.upper()

            cursor.execute("""
                SELECT title, author, published_at, tags, url, summary, source, 
                    related_location, related_sector, related_risk
                FROM public.news_feed 
                WHERE 
                        (related_location = 'GLOBAL' or related_location = %s)
                        AND (related_sector = 'GENERAL' or related_sector = %s)
                ORDER by related_sector,related_location 
                limit %s;                       
            """, (country, sector,result_limit))

            records = cursor.fetchall()

            response = {
                "news-feed": [
                    {                    
                        "title":record[0],
                        "author":record[1],
                        "published_at":record[2].isoformat() if isinstance(record[2], datetime) else record[2],
                        "tags":record[3],
                        "url":record[4],
                        "summary":record[5],
                        "source":record[6]	
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