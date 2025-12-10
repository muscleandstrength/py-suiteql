#!/usr/bin/env python3

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

load_dotenv()


def get_args():
    parser = argparse.ArgumentParser(description="Run a SuiteQL query")
    parser.add_argument("--limit", type=int, help="Number of results to return")
    parser.add_argument("--offset", type=int, help="Number of results to skip")
    return parser.parse_args()


def get_credentials():
    account_id = os.getenv("NETSUITE_ACCOUNT_ID")
    consumer_key = os.getenv("NETSUITE_CONSUMER_KEY")
    consumer_secret = os.getenv("NETSUITE_CONSUMER_SECRET")
    token = os.getenv("NETSUITE_TOKEN")
    token_secret = os.getenv("NETSUITE_TOKEN_SECRET")

    # Validate all required credentials are present
    required_vars = {
        "NETSUITE_ACCOUNT_ID": account_id,
        "NETSUITE_CONSUMER_KEY": consumer_key,
        "NETSUITE_CONSUMER_SECRET": consumer_secret,
        "NETSUITE_TOKEN": token,
        "NETSUITE_TOKEN_SECRET": token_secret,
    }

    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    return (account_id, consumer_key, consumer_secret, token, token_secret)


def run_suiteql_query(query, limit=None, offset=None):
    (account_id, consumer_key, consumer_secret, token, token_secret) = get_credentials()
    url = f"https://{account_id}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"
    params = {}

    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset

    oauth = OAuth1(
        client_key=consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
        realm=account_id,
        signature_method="HMAC-SHA256",
    )

    headers = {"Content-Type": "application/json", "prefer": "transient"}

    payload = {"q": query}

    try:
        response = requests.post(
            url, params=params, auth=oauth, headers=headers, json=payload
        )
        response.raise_for_status()
        result = response.json()
        return json.dumps(result, indent=2)
    except requests.exceptions.RequestException as e:
        return f"Error making request: {str(e)}"
    except json.JSONDecodeError as e:
        return f"Error parsing JSON response: {str(e)}"


if __name__ == "__main__":
    args = get_args()
    # Read query from stdin
    query = sys.stdin.read().strip()
    print("Running query...", file=sys.stderr)
    # Run the query and print results
    result = run_suiteql_query(query, args.limit, args.offset)
    print(result)
