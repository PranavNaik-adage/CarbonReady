"""
Test Lambda Function Directly
Invokes the data ingestion Lambda with a test payload
"""
import boto3
import json

lambda_client = boto3.client('lambda')

print("=" * 50)
print("Testing Lambda Function Directly")
print("=" * 50)
print()

# Load test payload
print("Loading test payload...")
with open('test-valid-sensor-data.json', 'r') as f:
    payload = json.load(f)

print(f"Payload: {json.dumps(payload, indent=2)}")
print()

# Invoke Lambda directly
print("Invoking Lambda function...")
try:
    response = lambda_client.invoke(
        FunctionName='carbonready-data-ingestion',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    # Parse response
    response_payload = json.loads(response['Payload'].read())
    
    print(f"Status Code: {response['StatusCode']}")
    print(f"Response: {json.dumps(response_payload, indent=2)}")
    
    if response['StatusCode'] == 200:
        print()
        print("✓ Lambda invoked successfully!")
        
        if response_payload.get('status') == 'success':
            print("✓ Data ingestion succeeded!")
        else:
            print(f"⚠ Data ingestion status: {response_payload.get('status')}")
            print(f"  Reason: {response_payload.get('reason')}")
            if 'errors' in response_payload:
                print(f"  Errors: {response_payload.get('errors')}")
    else:
        print(f"✗ Lambda invocation failed with status {response['StatusCode']}")
        
except Exception as e:
    print(f"✗ Error invoking Lambda: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 50)
