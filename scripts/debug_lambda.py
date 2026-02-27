"""
Debug Lambda Execution
Checks Lambda logs for detailed error messages
"""
import boto3
import time

logs = boto3.client('logs')

log_group = '/aws/lambda/carbonready-data-ingestion'

print("Fetching recent Lambda logs...")
print("=" * 50)

try:
    # Get the most recent log stream
    streams_response = logs.describe_log_streams(
        logGroupName=log_group,
        orderBy='LastEventTime',
        descending=True,
        limit=5
    )
    
    if not streams_response['logStreams']:
        print("No log streams found. Lambda may not have been invoked yet.")
        exit(0)
    
    # Get logs from the most recent stream
    for stream in streams_response['logStreams'][:2]:  # Check last 2 streams
        stream_name = stream['logStreamName']
        print(f"\nLog Stream: {stream_name}")
        print("-" * 50)
        
        events_response = logs.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=50,
            startFromHead=False
        )
        
        for event in events_response['events']:
            message = event['message'].strip()
            if message:
                # Highlight errors
                if 'error' in message.lower() or 'exception' in message.lower() or 'traceback' in message.lower():
                    print(f"[ERROR] {message}")
                elif 'rejected' in message.lower():
                    print(f"[REJECT] {message}")
                else:
                    print(f"[INFO] {message}")
        
except Exception as e:
    print(f"Error fetching logs: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
