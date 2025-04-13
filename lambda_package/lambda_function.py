import json
import boto3
import os
import requests
from requests.auth import HTTPBasicAuth
import logging

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the Amazon Connect client
connect_client = boto3.client("connect")

# Environment variables
INSTANCE_ID = os.getenv("INSTANCE_ID")
CUSTOMER_IDENTIFIER = os.getenv("CUSTOMER_IDENTIFIER")
base_url = os.getenv("URL")  # Base URL like: https://amazon.afiniti.com/LookupAccount
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

def lambda_handler(event, context):
    try:
        # Extract contactId
        contact_id = event.get("Details", {}).get("ContactData", {}).get("ContactId")
        if not contact_id:
            return {"error": "Missing ContactId in the event."}

        logger.info(f"ContactId: {contact_id}")

        # Fetch contact attributes
        response = connect_client.get_contact_attributes(
            InstanceId=INSTANCE_ID,
            InitialContactId=contact_id
        )

        attributes = response.get("Attributes", {})
        attribute_value = attributes.get(CUSTOMER_IDENTIFIER, None)

        if not attribute_value:
            logger.error(f"Attribute '{CUSTOMER_IDENTIFIER}' not found in contact attributes.")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Missing attribute: {CUSTOMER_IDENTIFIER}"})
            }

        # Construct full URL with path parameter
        full_url = f"{base_url.rstrip('/')}/{attribute_value}"
        logger.info(f"Full URL: {full_url}")

        # Send GET request (assuming lookup should be a GET; change to POST if required)
        auth = HTTPBasicAuth(username, password)
        headers = { "Content-Type": "application/json" }

        response = requests.get(full_url, auth=auth, headers=headers, timeout=5)

        try:
            response_data = response.json()
        except ValueError:
            response_data = response.text

        if response.status_code == 200:
            logger.info("Success Response: %s", response_data)
        else:
            logger.error(f"API Error {response.status_code}: {response_data}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "lookupUrl": full_url,
                "apiStatus": "success" if response.status_code == 200 else "failed",
                "apiResponseCode": response.status_code,
                "apiResponse": response_data
            })
        }

    except Exception as e:
        logger.exception("Exception occurred in Lambda function.")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

