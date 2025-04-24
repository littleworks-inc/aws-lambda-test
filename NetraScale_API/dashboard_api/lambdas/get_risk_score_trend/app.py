import json
import psycopg2
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Event received: %s", json.dumps(event))

    # 1. Get orgId from pathParameters
    try:
        org_id = event['pathParameters'].get('orgId', None)
        if org_id is None:
            raise KeyError()
    except KeyError:
        return {
            'statusCode': 400,
            'body': {'error': 'Missing orgId parameter', 'event-stack': event},
            'headers': {'Content-Type': 'application/json'}
        }
    
    # 2. DB credentials from environment
    db_host = os.environ['DB_HOST']
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']
    db_password = os.environ['DB_PASSWORD']
    db_port = os.environ.get('DB_PORT', 5432)

    cursor = None
    conn = None

    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )

        # 3. SQL query
        sql = """
            SELECT
                overall_risk_score,
                EXTRACT(MONTH FROM date_of_last_assessment) AS month,
                EXTRACT(YEAR FROM date_of_last_assessment) AS year
            FROM public.overall_risk_score
            WHERE organization_id = %s
            ORDER BY year, month;
        """
        # 4. Execute
        with conn.cursor() as cursor:
            cursor.execute(sql, (org_id,))
            records = cursor.fetchall()

        # 5. Map month # to short names
        months_abbr = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }

        # 6. Format as needed
        trend = []
        for record in records:
            score, month, year = record
            month_abbr = months_abbr.get(int(month), str(int(month)))
            trend.append({
                "month": month_abbr,
                "year": int(year),
                "score": int(score) if score is not None else None
            })

        # 7. The response as requested
        response = {
            "statusCode": 200,
            "body": json.dumps({"trend": trend}),
            "headers": {'Content-Type': 'application/json'}
        }
        return response

    except psycopg2.Error as e:
        logger.exception("Database error")
        return {
            "statusCode": 500,
            "body": {"error": f"Database error: {str(e)}"},
            "headers": {'Content-Type': 'application/json'}
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()