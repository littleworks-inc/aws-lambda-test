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

    # Database connection parameters
    db_host = os.environ['DB_HOST']
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']
    db_password = os.environ['DB_PASSWORD']
    db_port = os.environ.get('DB_PORT', 3306)


    attack_data = {
        "attack_types": [
            {
                "type": "AI-Based Attacks",
                "description": "Attacks leveraging artificial intelligence to enhance their effectiveness.",
                "severity": "Critical",
                "adversaries": [
                    {
                        "id":"6067b9a5-1e57-4a76-9b71-8cab84d18a6a",
                        "title": "Deep Fake Voice Fraud",
                        "definition": "AI-generated voice impersonation of executives requesting urgent wire transfers."
                    },
                    {
                        "id":"6067b9a5-1e57-4a76-9b71-8cab84d18a6a",
                        "title": "AI-Powered Malware",
                        "definition": "Malware that uses AI to evade detection and adapt to security measures."
                    }
                ]
            },
            {
                "type": "Social Engineering",
                "description": "Manipulative tactics to trick individuals into divulging confidential information.",
                "severity": "High",
                "adversaries": [
                    {
                        "id":"6067b9a5-1e57-4a76-9b71-8cab84d18a6a",
                        "title": "Advanced Spear Phishing",
                        "definition": "Highly targeted phishing attacks using personalized information to deceive victims."
                    },
                    {
                        "id":"6067b9a5-1e57-4a76-9b71-8cab84d18a6a",
                        "title": "Pretexting",
                        "definition": "Creating a fabricated scenario to obtain sensitive information from a target."
                    },
                    {
                        "id":"6067b9a5-1e57-4a76-9b71-8cab84d18a6a",
                        "title": "Baiting",
                        "definition": "Luring victims with enticing offers to steal their personal information."
                    }
                ]
            },
            {
                "type": "Ransomware",
                "description": "Malware that encrypts data and demands payment for its release.",
                "severity": "Critical",
                "adversaries": [
                    {
                        "id":"6067b9a5-1e57-4a76-9b71-8cab84d18a6a",
                        "title": "CryptoLocker",
                        "definition": "Ransomware that encrypts files and demands payment in cryptocurrency for decryption."
                    },
                    {
                        "id":"6067b9a5-1e57-4a76-9b71-8cab84d18a6a",
                        "title": "WannaCry",
                        "definition": "A global ransomware attack that exploited a vulnerability in Windows systems."
                    }
                ]
            }
        ]
    }
    
    return {
        'statusCode': 200,
        'body': json.dumps(attack_data)
    }