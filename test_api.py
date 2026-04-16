import requests

def test_operations_endpoint():
    try:
        print("Testing /api/operations endpoint...")
        response = requests.get('http://127.0.0.1:5000/api/operations')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data)} operations")
            for i, op in enumerate(data[:5], 1):  # Show first 5 operations
                print(f"{i}. ID: {op.get('operation_id')}, Name: {op.get('operation_name')}")
            if len(data) > 5:
                print(f"... and {len(data) - 5} more operations")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_operations_endpoint()
