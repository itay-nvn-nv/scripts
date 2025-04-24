import json
import requests
import os

TOKEN = os.environ.get("RUNAI_TOKEN")
RUNAI_CTRL_PLANE_URL = os.environ.get("RUNAI_CTRL_PLANE_URL")
TARGET_CLUSTER_ID = os.environ.get("RUNAI_CLUSTER_ID")
BASE_URL = f"{RUNAI_CTRL_PLANE_URL}/api/v1/asset/compute"
OUTPUT_DIR = "compute_resource_specs"

def get_token():
    return TOKEN

def api_request(method, url, headers=None, json=None):
    headers = headers or {}
    headers['authorization'] = f'Bearer {get_token()}'
    try:
        response = requests.request(method, url, headers=headers, json=json)
        response.raise_for_status()
        if response.status_code != 204:
            return response.json(), response.status_code
        else:
            return response, response.status_code
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None, None
    except json.JSONDecodeError:
        print("Error: Invalid JSON response from API")
        return None, None


def fetch_compute_assets():
    url = f'{BASE_URL}?usageInfo=true'
    data, _ = api_request('GET', url)
    return data


def fetch_compute_details(compute_id):
    url = f'{BASE_URL}/{compute_id}'
    data, _ = api_request('GET', url)
    return data


def delete_compute_asset(compute_id):
    url = f'{BASE_URL}/{compute_id}'
    _, status_code = api_request('DELETE', url)
    return status_code

def create_compute_asset(data):
    data, _ = api_request('POST', BASE_URL, json=data)
    return data


def create_fixed_spec(compute_details):
    if not compute_details:
        print("No compute details provided, cannot create fixed spec.")
        return None

    fixed_spec = compute_details.copy()

    meta_fields_to_delete = [
        "id",
        "kind",
        "tenantId",
        "createdBy",
        "createdAt",
        "updatedBy",
        "updatedAt",
        "deletedAt",
        "updateCount"
    ]
    if "meta" in fixed_spec:
        for field in meta_fields_to_delete:
            fixed_spec["meta"].pop(field, None)

    if "spec" in fixed_spec:
        fixed_spec["spec"]["cpuMemoryRequest"] = "1M"

    return fixed_spec


def process_json_data(json_data):
    matching_ids = []

    if not isinstance(json_data, dict) or 'entries' not in json_data:
        print("Unexpected data structure - missing 'entries' key")
        return matching_ids

    for entry in json_data['entries']:
        if (isinstance(entry, dict) and
            entry.get('meta', {}).get('clusterId') == TARGET_CLUSTER_ID and
            entry.get('spec', {}).get('cpuMemoryRequest') in ['0M', '0G']):
            matching_ids.append(entry.get('meta', {}).get('id'))

    return matching_ids


def save_json(data, filename):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Saved JSON data to {filename}")
    except Exception as e:
        print(f"Error saving JSON to file: {e}")

def main():
    data = fetch_compute_assets()
    if data is None:
        return

    matching_ids = process_json_data(data)

    print(f"\nFound {len(matching_ids)} matching compute assets")
    print("\nProcessing each compute asset...")

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


    for compute_id in matching_ids:
        print(f"\n{'=' * 50}")
        print(f"Processing compute asset: {compute_id}")
        print(f"{'=' * 50}")

        details = fetch_compute_details(compute_id)
        if not details:
            print(f"Failed to fetch details for {compute_id}")
            continue

        original_filename = os.path.join(OUTPUT_DIR, f"{compute_id}_spec_original.json")
        save_json(details, original_filename)

        print("Original Details:")
        print(f"Name: {details.get('meta', {}).get('name', 'N/A')}")
        print(f"Status: {details.get('status', {}).get('phase', 'N/A')}")
        print(f"Created: {details.get('meta', {}).get('creationTimestamp', 'N/A')}")
        print(f"CPU Request: {details.get('spec', {}).get('cpuMemoryRequest', 'N/A')}")
        print(f"GPU Count: {details.get('spec', {}).get('gpuCount', 'N/A')}")
        print(f"Memory Request: {details.get('spec', {}).get('memoryRequest', 'N/A')}")

        fixed_spec = create_fixed_spec(details)

        if not fixed_spec:
            print(f"Failed to create fixed spec for {compute_id}")
            continue

        fixed_filename = os.path.join(OUTPUT_DIR, f"{compute_id}_spec_fixed.json")
        save_json(fixed_spec, fixed_filename)

        print(f"Deleting compute asset {compute_id}...")
        delete_status_code = delete_compute_asset(compute_id)

        print(f"Successfully deleted compute asset {compute_id}")
        print(delete_status_code)

        print(f"Creating new compute asset with fixed spec...")
        create_response = create_compute_asset(fixed_spec)

        if create_response:
            print(f"Successfully created new compute asset for {compute_id}")
            print(f"New compute asset details: {create_response}")
        else:
            print(f"Failed to create new compute asset for {compute_id}")
            print(f"Fixed spec: {fixed_spec}")


if __name__ == "__main__":
    main()