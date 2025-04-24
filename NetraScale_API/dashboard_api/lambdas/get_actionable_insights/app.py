import json

def lambda_handler(event, context):
    # Default response for API Gateway
    response = {
        "statusCode": 200,
        "body": json.dumps({
            "insights": [
                {
                    "Threat": "AI-Powered Phishing and Social Engineering Attacks",
                    "Severity Level": "High",
                    "Problem Domain": "Phishing",
                    "Mitigation Tactic": "Implement AI-based email filtering and conduct regular employee training on phishing awareness."
                },
                {
                    "Threat": "Ransomware Campaigns Targeting Financial Data",
                    "Severity Level": "Critical",
                    "Problem Domain": "Ransomware",
                    "Mitigation Tactic": "Regularly back up data and ensure backups are stored offline."
                },
                {
                    "Threat": "Insider Threats and Third-Party Vulnerabilities",
                    "Severity Level": "High",
                    "Problem Domain": "Insider Threats",
                    "Mitigation Tactic": "Conduct thorough background checks and continuously monitor user activities."
                },
                {
                    "Threat": "Cloud Security Breaches",
                    "Severity Level": "High",
                    "Problem Domain": "Cloud Security",
                    "Mitigation Tactic": "Implement multi-factor authentication and conduct regular security audits."
                },
                {
                    "Threat": "Advanced Persistent Threats (APTs)",
                    "Severity Level": "High",
                    "Problem Domain": "APTs",
                    "Mitigation Tactic": "Deploy advanced threat detection systems and regularly update security protocols."
                }
            ]
        })
    }
    return response
