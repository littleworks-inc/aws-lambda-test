import json
import os
import psycopg2
import logging

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Log the entire event for debugging
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Get org_id from path parameters
        # org_id = event['pathParameters'].get('orgId', None)
        # logger.info(f"Organization ID: {org_id}")
        
        # Log request headers
        if 'headers' in event:
            logger.info(f"Request headers: {json.dumps(event['headers'])}")
        
        # Parse request body
        body = json.loads(event['body'])
        logger.info(f"Request body: {json.dumps(body)}")
        
        action_ids = body.get('ids', [])
        new_status = body.get('status')
        
        logger.info(f"Action IDs to update: {action_ids}")
        logger.info(f"New status to set: {new_status}")
        
        # Validate required parameters
        if not action_ids or not new_status:
            error_msg = "Missing required parameters: ids and status are required"
            logger.error(error_msg)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': error_msg}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',  # Add CORS headers
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                }
            }
        
        # Validate status value
        valid_statuses = ['not_started', 'in_progress', 'completed', 'paused']
        if new_status not in valid_statuses:
            error_msg = f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            logger.error(error_msg)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': error_msg}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                }
            }
            
        # Database connection
        db_host = os.environ['DB_HOST']
        db_name = os.environ['DB_NAME']
        db_user = os.environ['DB_USER']
        db_password = os.environ['DB_PASSWORD']
        db_port = os.environ.get('DB_PORT', 5432)
        
        logger.info(f"Connecting to database: {db_host}/{db_name}")
        
        conn = None
        cursor = None
        
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
            
            # Update multiple action statuses
            updated_actions = []
            for action_id in action_ids:
                logger.info(f"Updating action ID: {action_id} to status: {new_status}")
                
                cursor.execute("""
                    UPDATE general_threat_mitigation_activities
                    SET tactic_state = %s
                    WHERE id = %s
                    RETURNING id, problem_domain, mitigation_action, priority, category, tactic_state
                """, (new_status, action_id))
                
                updated_record = cursor.fetchone()
                if updated_record:
                    action_data = {
                        'id': updated_record[0],
                        'type': updated_record[1],
                        'action': updated_record[2],
                        'priority': updated_record[3],
                        'category': updated_record[4],
                        'state': updated_record[5]
                    }
                    updated_actions.append(action_data)
                    logger.info(f"Successfully updated action: {json.dumps(action_data)}")
                else:
                    logger.warning(f"Action ID {action_id} not found in database")
            
            conn.commit()
            logger.info(f"Database transaction committed. Updated {len(updated_actions)} actions.")
            
            # Format the response
            response = {
                'success': True,
                'updatedCount': len(updated_actions),
                'actions': updated_actions
            }
            
            logger.info(f"Sending response: {json.dumps(response)}")
            
            return {
                'statusCode': 200,
                'body': json.dumps(response),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                }
            }
            
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            return {
                'statusCode': 500,
                'body': json.dumps({'error': error_msg}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                }
            }
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            logger.info("Database connection closed")
                
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        logger.error(error_msg)
        logger.exception("Detailed exception information:")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            }
        }