import json
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor  # For returning results as dictionaries

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Get the origin from the request headers
    origin = event.get('headers', {}).get('Origin', event.get('headers', {}).get('origin', ''))
    
    # Define allowed origins
    allowed_origins = [
        'http://localhost:3000',
        'https://staging.riskact.com',
        'https://www.riskact.com'
    ]
    
    # Check if the request origin is allowed
    cors_origin = origin if origin in allowed_origins else allowed_origins[0]

    logger.info("================== EVENT START ==================")
    logger.info(json.dumps(event, indent=2))
    logger.info("================== EVENT END ==================")
    
    # Get query parameters
    query_params = event.get('queryStringParameters', {}) or {}
    sector = query_params.get('sector')
    region = query_params.get('region')

    # Initialize regulations list
    regulations = []

    # Only proceed with query if parameters are valid
    if not (sector == 'no_value' and region == 'no_value'):
        try:
            # Database connection parameters
            conn = psycopg2.connect(
                host=os.environ['DB_HOST'],
                database=os.environ['DB_NAME'],
                user=os.environ['DB_USER'],
                password=os.environ['DB_PASSWORD'],
                port=os.environ.get('DB_PORT', 5432),
                cursor_factory=RealDictCursor  # Return results as dictionaries
            )

            # Build the query dynamically
            query = """
                SELECT *
                FROM "RansomwareRegulationsWorldwidePenalty"
                WHERE 1=1
            """
            params = []

            # Add region filter if provided and valid
            if region and region != 'no_value' and region != 'All Country/Region':
                query += """ AND location ILIKE %s"""
                params.append(f'%{region}%')

            # Add sector filter if provided and valid
            if sector and sector != 'no_value' and sector != 'All Sector':
                query += """ AND sector ILIKE %s"""
                params.append(f'%{sector}%')

            logger.info(f"Executing query: {query}")
            logger.info(f"With parameters: {params}")

            # Execute query
            with conn.cursor() as cur:
                cur.execute(query, params)
                regulations = cur.fetchall()
                
                # Convert results to list of dictionaries
                regulations = [dict(row) for row in regulations]

        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            regulations = []

        finally:
            if conn:
                conn.close()

    # Create response body
    body = {
        "regulation-information": {
            "regulations": regulations,
            "parameters": {
                "sector": sector,
                "region": region
            }
        }
    }

    response = {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': cors_origin,
            'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key,Authorization',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Credentials': 'true'
        },
        'body': json.dumps(body, default=str)  # default=str handles datetime objects
    }

    logger.info("================== RESPONSE START ==================")
    logger.info(json.dumps(response, indent=2, default=str))
    logger.info("================== RESPONSE END ==================")

    return response