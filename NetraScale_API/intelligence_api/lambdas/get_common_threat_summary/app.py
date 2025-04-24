import json
import os
import psycopg2
from decimal import Decimal
from netrascale_utils.postgres_manager import PostgresManager
from netrascale_utils.common_db_calls import is_valid_organization,get_organization_details
from netrascale_utils.parameter_validation import ParameterValidation

def lambda_handler(event, context):

    # Database connection parameters
    db_secret_name = os.environ['DB_SECRET_NAME']
    aws_region = os.environ['AWS_USE_REGION']
    aws_profile = os.environ.get('AWS_PROFILE')

    try:
        org_id = event['pathParameters'].get('orgId', None)

        is_valid_org = is_valid_organization(org_id,db_secret_name,aws_region,aws_profile)
        if not is_valid_org:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid organization ID'}),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }

    except KeyError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing orgId parameter','event-stack':event}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    category = "ALL"

    try:
        category = event['queryStringParameters'].get('category', None)
        if category is None:
            category = "ALL"
        else:
            is_valid_category = ParameterValidation.is_valid_attack_type(category)

            if not is_valid_category:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid attack category provided'}),
                    'headers': {
                        'Content-Type': 'application/json'
                    }
                }
    except KeyError:
        pass

    # Mapping risk_status numbers to labels
    PROBABILITY_MAPPING = {
        0: "undetermined",
        1: "low",
        2: "medium",
        3: "high",
        4: "critical"
    }

    MITIGATION_MAPPING ={
        0: "undetermined",
        1: "Risk Avoidance",
        2: "Risk Reduction",
        3: "Risk Transfer",
        4: "Risk Acceptance",
        5: "Risk Exploitation"
    }

    try:
        db_manager = PostgresManager(db_secret_name, aws_region,aws_profile)

        base_query = """SELECT id, common_threat, problem_statement, solution_statement, risk_status, probability_of_occurrence, 
            potential_impact, breach_cost FROM public.organization_common_threat_summary where organization_id=%s"""

        results = None

        if category == "ALL":
            results = db_manager.execute_query(base_query, (org_id,))
        else:
            base_query += " AND common_threat=%s"
            results = db_manager.execute_query(base_query, (org_id,category))

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to connect to database','event-stack':event}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    response = {
                "common-threats": [
                    {                    
                        "id":record[0],
                        "common_threat":record[1],
                        "problem_statement":record[2],
                        "solution_statement":record[3],
                        "risk_status":MITIGATION_MAPPING.get(record[4], "unknown")  ,
                        "probability":PROBABILITY_MAPPING.get(record[5],"unknown"),
                        "potential_impact":record[6],
                        "breach_cost":float(record[7]) if isinstance(record[7], Decimal) else record[7]	
                    }
                    for record in results
                ]
            }
        

    return {
        'statusCode': 200,
        'body': json.dumps(response),
        'headers': {
            'Content-Type': 'application/json'
        }
    }

