import requests
import json

# Test the backend API endpoints
base_url = 'http://127.0.0.1:8000'

print("Testing PrintSmart Backend API...")
print("=" * 50)

# Test health check endpoint
try:
    response = requests.get(f'{base_url}/health/')
    print(f"Health Check - Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
except Exception as e:
    print(f"Health Check failed: {e}")

# Test API root endpoint
try:
    response = requests.get(f'{base_url}/api/')
    print(f"API Root - Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
except Exception as e:
    print(f"API Root failed: {e}")

# Test admin panel availability
try:
    response = requests.get(f'{base_url}/admin/')
    print(f"Admin Panel - Status: {response.status_code}")
    print(f"Admin panel is accessible")
    print()
except Exception as e:
    print(f"Admin Panel failed: {e}")

print("Backend testing completed!")
