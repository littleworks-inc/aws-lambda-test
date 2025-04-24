import os
import psycopg2
from datetime import datetime, timedelta
import calendar
import json

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
    
    period = event["queryStringParameters"].get("period", None) # 1,3, or 0 (all)
        
    grouping = event["queryStringParameters"].get("grouping", None)

    if grouping is not None:
        grouping = grouping.upper()

    # Database connection parameters
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

        # Base SQL query
        sql_query = None

        # TODO: Clean up this processing and move business logic to a function

        if grouping == "YES":
            sql_query = """
            SELECT month, year, score,category
                FROM public."historical_risk_score"
            WHERE organization_id = %s and month = %s and year = %s
		    order by year,month,category 
            """

            current_date = datetime.utcnow()
            month = current_date.month
            year = current_date.year

            print(month)

            cursor.execute(sql_query , (org_id,month,year))

        else:
            sql_query = """
                SELECT month, year, score,category
                FROM public."historical_risk_score"
                WHERE organization_id = %s and category = %s
            """

            # Add date range condition based on period
            if period == 1:
                start_date = datetime.utcnow() - timedelta(days=365)  # 1 year
                sql_query += " AND created_on >= %s " 
                cursor.execute(sql_query, (org_id,category, start_date))
            elif period == 3:
                start_date = datetime.utcnow() - timedelta(days=3 * 365)  # 3 years
                sql_query += " AND created_on >= %s " 
                cursor.execute(sql_query, (org_id,category, start_date))
            else:
                # No date filter if period is 0
                cursor.execute(sql_query , (org_id,category))

        # Fetch results
        records = cursor.fetchall()

        # Convert results to JSON format
        response = {
            "historical-risk-scores": [
                {
                    "month": calendar.month_abbr[record[0]],  # Convert numeric month to abbreviated name (e.g., 12 -> Dec)
                    "year": record[1],
                    "score": record[2],
                    "category": record[3]
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
            "body": f"Database error: {e}"
        }
    finally:
        if conn:
            cursor.close()
            conn.close()
