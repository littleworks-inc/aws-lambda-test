import json
import os
import re
import boto3
import psycopg2
import base64
import logging
from datetime import datetime


# Lambda Handler Function
def lambda_handler(event, context):
    try:
        http_method = event["httpMethod"]

        if http_method == "PATCH":
            return update_flag(event)

        elif http_method == "POST":
            return upload_file(event)

        else:
            logging.debug(f"Unsupported HTTP Method: {http_method}")
            return {"statusCode": 400, "body": json.dumps("Unsupported HTTP Method")}

    except Exception as e:
        logging.warning(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
    
def update_flag(event):
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

    # Validate the data from the body
    body = json.loads(event["body"])

    try:
        # these are validated in other areas of the code, so we can assume they are present
        evidence_id = body["evidence_id"]
        third_party = body["third_party"]   

        # (0) verbal, (1) collected, (2) request for verification, (3) verified 
        evidence_state = body["evidence_state"]
        if evidence_state not in [0, 1, 2, 3]:
            return {"statusCode": 400, "body": json.dumps("Invalid evidence state")}
        
        # (0) pending, (1) approved, (2) rejected, (3) verified, (4) archived, (5) completed
        status = body["status"] 
        if status not in [0, 1, 2, 3, 4, 5]:
            return {"statusCode": 400, "body": json.dumps("Invalid status")}

        # true or false
        from_third_party = body["from_third_party"]
        if from_third_party not in [True, False]:
            return {"statusCode": 400, "body": json.dumps("Invalid third party indicator")}
        
    except KeyError:

        logging.debug(f"Missing required parameters: {event}")

        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing required parameters','event-stack':event}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    except ValueError:
        logging.debug(f"Invalid value for required parameters: {event}")

        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid value for required parameters','event-stack':event}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    

    current_date = datetime.utcnow()
    year = current_date.year

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Make sure the organization exists, although details are not needed
        cursor.execute("SELECT id FROM public.\"Organization\" WHERE id=%s", [org_id])

        if cursor.rowcount == 0:
            return {"statusCode": 404, "body": json.dumps("Organization not found")}
        
        # Make sure the evidence requirement exists (evidence_id)
        cursor.execute("SELECT id,evidence_category FROM public.\"evidence_requirements\" WHERE id=%s", [evidence_id])

        evidence_category = None

        if cursor.rowcount == 0:
            return {"statusCode": 404, "body": json.dumps("The associated evidence requirement does not exist")}
        else:
            evidence_category = cursor.fetchone()[1]

        # TODO: Get the person who is logged into the system via authentication header
        #user = event["requestContext"]["authorizer"]["claims"]
        #username = user.get("cognito:username")  # Get the username
        #user_sub = user.get("sub")  # Unique Cognito user ID
        #email = user.get("email")  # If included in the token

        username ='test_user'

        # Does evidence already exist for this category, if so, this is an update, otherwise, it is a new entry
        cursor.execute("SELECT id FROM public.\"evidence_collection\" WHERE organization_id=%s AND evidence_id=%s and year=%s", [org_id, evidence_id,year])

        if cursor.rowcount == 0:
            # create a new entry
            cursor.execute(
                "INSERT INTO public.\"evidence_collection\" (organization_id, evidence_category, evidence_id, provided_by, evidence_state, status, from_third_party, third_party, year) " 
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [org_id, evidence_category, evidence_id, username, evidence_state, status, from_third_party, third_party, year]
                )
        else:
            # update the existing entry
            cursor.execute("update public.\"evidence_collection\" set evidence_state=%s, status=%s, from_third_party=%s, third_party=%s, updated_at=%s where organization_id=%s and evidence_id=%s and year=%s", 
                           [evidence_state, status, from_third_party, third_party, current_date, org_id, evidence_id, year])

        conn.commit()
        return {"statusCode": 200, "body": json.dumps("Evidence updated successfully")}

    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Database error: {str(e)}")}

    finally:
        cursor.close()
        conn.close()


def upload_file(event):
    # First thing we do is perform the fundamental updates for the evidence
    json_results = update_flag(event)

    valid_extensions = {".pdf", ".docx"}

    # If the evidence update was not successful, return the error
    if json_results["statusCode"] != 200:
        return json_results
    
    body = json.loads(event["body"])

    # Since these are validated by update_flag call, we can assume they are present
    org_id = event['pathParameters'].get('orgId', None)
    evidence_id = body["evidence_id"]    

    db_key = body.get("db_key", None)  # Optional field

    # Get the S3 bucket name from the environment
    S3_BUCKET = os.getenv("S3_BUCKET", None)
    if not S3_BUCKET:
        return {"statusCode": 500, "body": json.dumps("S3_BUCKET environment variable not set")}

    # ensure this is a valid file name
    file_name = body.get("file_name")
    if not file_name:
        return {"statusCode": 400, "body": json.dumps("Missing file_name")}
    
    if not is_valid_filename("report.pdf", valid_extensions):
        return {"statusCode": 400, "body": json.dumps("Invalid file_name")}

    file_content_base64 = body.get("file_content")  # Expect base64 encoded content

    file_content = base64.b64decode(file_content_base64)
    s3_key = f"uploads/{org_id}/{file_name}"

    s3_client = boto3.client("s3")

    # S3 content for storage in the database
    version_id = None
    etag = None

    # Handle the uploading of  the file to S3
    try:
        if isinstance(file_content, str):
            file_content = file_content.encode("utf-8")  # Convert to bytes
            
        response = s3_client.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=file_content)
        
        # Get the version and eTag (Hash) and add to meta information
        version_id = response.get("VersionId", None)
        etag = response.get("ETag", None)

    except Exception as e:
        logging.error("Error uploading file to S3: {}".format(e))         
        return {"statusCode": 500, "body": json.dumps(f"Error uploading file to S3")}


    # setup the DB variables
    conn = None
    cursor = None

    # Store the metadata in the database
    try:        
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the evidence collection ID for the created/updated evidence
        evidence_collected_id = None
        current_date = datetime.utcnow()
        year = current_date.year

        cursor.execute("SELECT id FROM public.\"evidence_collection\" WHERE organization_id=%s AND evidence_id=%s and year=%s", [org_id, evidence_id,year])
        if cursor.rowcount > 0:
            evidence_collected_id = cursor.fetchone()[0]
        else:
            return {"statusCode": 404, "body": json.dumps("Evidence collection not found")}

        # TODO: Add the hash and version

        # Store metadata in database
        cursor.execute(
            "INSERT INTO file_uploads (organization_id,eTag,s3_version_id,evidence_collected_id, db_key, file_name, s3_path) VALUES (%s, %s, %s, %s,%s,%s,%s)",
            (org_id,etag,version_id,evidence_collected_id, db_key, file_name, s3_key),
        )
        conn.commit()

        return {"statusCode": 200, "body": json.dumps({"message": "File uploaded", "s3_path": s3_key})}
    except psycopg2.Error as e:
        logging.error("Database error: {}".format(e))
        return {"statusCode": 500, "body": json.dumps(f"Database error: {str(e)}")}                
    finally:
        cursor.close()
        conn.close()
        

def get_db_connection():

    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_PORT = os.getenv("DB_PORT")

    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

# TODO: Move to common library
def is_valid_filename(filename, allowed_extensions=None):
    """
    is_valid_filename checks if a filename is valid based on the following criteria:
    - The filename is not empty or None
    - The filename does not contain any of the following characters: < > : " / \\ | ? *
    - The filename has an allowed extension if provided

    :param filename: The filename to validate
    :param allowed_extensions: A list of allowed file extensions (e.g., ['.jpg', '.png'])
    :return: True if the filename is valid, False otherwise
    
    Example:
        >>> is_valid_filename("report.pdf", {".pdf", ".docx"})
        True

    """
    if not filename or filename.strip() == "":
        return False  # Empty or None filename is invalid
    
    # Check for forbidden characters
    if re.search(r'[<>:"/\\|?*\x00-\x1F]', filename):
        return False
    
    # Validate file extension if provided
    if allowed_extensions:
        _, ext = os.path.splitext(filename)
        if ext.lower() not in allowed_extensions:
            return False
    
    return True  # Passed all checks
