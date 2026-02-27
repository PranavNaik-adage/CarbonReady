"""
Check AWS Costs
Shows your current month's spending
"""
import boto3
from datetime import datetime, timedelta

ce = boto3.client('ce', region_name='us-east-1')  # Cost Explorer is only in us-east-1

# Get current month costs
start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
end = datetime.now().strftime('%Y-%m-%d')

print("=" * 50)
print("AWS Cost Report")
print("=" * 50)
print(f"Period: {start} to {end}")
print()

try:
    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start,
            'End': end
        },
        Granularity='MONTHLY',
        Metrics=['BlendedCost', 'UnblendedCost'],
        GroupBy=[
            {'Type': 'SERVICE', 'Key': 'SERVICE'}
        ]
    )
    
    total_cost = 0
    print("Costs by Service:")
    print("-" * 50)
    
    for result in response['ResultsByTime']:
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['BlendedCost']['Amount'])
            if cost > 0.01:  # Only show services with cost > $0.01
                print(f"  {service:30s} ${cost:8.2f}")
                total_cost += cost
    
    print("-" * 50)
    print(f"  {'TOTAL':30s} ${total_cost:8.2f}")
    print()
    print(f"Remaining credits: ${100 - total_cost:.2f}")
    
    if total_cost > 10:
        print("\n⚠ WARNING: You've spent more than $10!")
    elif total_cost > 5:
        print("\n⚠ Note: You've spent more than $5")
    else:
        print("\n✓ Costs are minimal")
        
except Exception as e:
    print(f"Error fetching costs: {e}")
    print("\nNote: Cost Explorer may take 24 hours to show data")
    print("Check AWS Console → Billing Dashboard for real-time costs")

print("=" * 50)
