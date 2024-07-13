import requests
import time
import json

RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_HOST = "192.168.68.105"
RPC_PORT = 22555

def call_rpc(method, params=[]):
    url = f"http://{RPC_HOST}:{RPC_PORT}"
    headers = {'content-type': 'application/json'}
    payload = json.dumps({
        "method": method,
        "params": params,
        "jsonrpc": "2.0",
        "id": 0,
    })

    response = requests.post(url, headers=headers, data=payload, auth=(RPC_USER, RPC_PASSWORD))
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"RPC call failed with status code {response.status_code}, response: {response.text}")

def get_rescan_progress():
    result = call_rpc("getwalletinfo")
    scanning_info = result['result'].get('scanning', None)
    if scanning_info:
        progress = scanning_info.get('progress', 0)
        duration = scanning_info.get('duration', 0)
        return progress, duration
    else:
        return None, None

def main():
    try:
        # Monitor the progress
        while True:
            progress, duration = get_rescan_progress()
            if progress is None:
                print("Rescan complete or not in progress.")
                break
            else:
                print(f"Rescan progress: {progress * 100:.2f}% | Estimated duration: {duration} seconds")
            
            # Wait for 10 seconds before checking again
            time.sleep(10)
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
