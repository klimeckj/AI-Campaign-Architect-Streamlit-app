"""Bloomreach API integration service."""
import base64
import requests


def push_to_bloomreach(config, data_payload):
    """Push campaign data to Bloomreach Content/Catalog API."""
    if not config or "bloomreach" not in config:
        return False, "Chybí konfigurace pro Bloomreach."
    
    br_conf = config["bloomreach"]
    
    # Load configuration variables
    base_url = br_conf.get("api_base_url", "").strip().rstrip('/')
    project_token = br_conf.get("project_token", "").strip()
    catalog_id = br_conf.get("catalog_id", "").strip()
    key_id = br_conf.get("auth_key_id", "").strip()
    key_secret = br_conf.get("auth_key_secret", "").strip()
    
    if not all([base_url, project_token, catalog_id, key_id, key_secret]):
        return False, "Neúplná konfigurace Bloomreach."

    # Get item_id for URL
    item_id = str(data_payload.get("item_id", "")).strip()
    
    if not item_id:
        return False, "Chybí item_id."

    url = f"{base_url}/data/v2/projects/{project_token}/catalogs/{catalog_id}/items/{item_id}"
    
    # Prepare Basic Auth header
    auth_str = f"{key_id}:{key_secret}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("ascii")
    
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/json; charset=utf-8"
    }

    # Prepare payload (item_id already in URL, not in properties)
    properties = {
        "segment_id": data_payload.get("segment_id"),
        "email_subject": data_payload.get("email_subject"),
        "email_body": data_payload.get("email_body"),
        "sms_text": data_payload.get("sms_text"),
        "push_text": data_payload.get("push_text")
    }
    
    # Remove None values (optional fields)
    properties = {k: v for k, v in properties.items() if v is not None}

    payload = {"properties": properties}

    # Send PUT request
    try:
        response = requests.put(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201, 204]:
            return True, f"Success ({response.status_code})"
        else:
            return False, f"API Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, f"Connection Error: {str(e)}"
