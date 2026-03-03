#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Trigger AI Processing Lambda to generate carbon calculations
.DESCRIPTION
    Manually invokes the AI processing Lambda function to calculate
    carbon position and CRI from sensor data
#>

param(
    [string]$FarmId = "farm-001"
)

Write-Host "Triggering AI Processing Lambda..." -ForegroundColor Cyan
Write-Host "Farm ID: $FarmId" -ForegroundColor Gray

# Create payload
$payload = @{
    farmId = $FarmId
} | ConvertTo-Json -Compress

Write-Host "`nPayload: $payload" -ForegroundColor Gray

# Invoke Lambda
Write-Host "`nInvoking Lambda function..." -ForegroundColor Yellow

# Write payload to file
$payload | Out-File -FilePath payload.json -Encoding utf8 -NoNewline

$response = aws lambda invoke `
    --function-name carbonready-ai-processing `
    --payload file://payload.json `
    response.json

# Clean up payload file
Remove-Item payload.json -ErrorAction SilentlyContinue

if ($LASTEXITCODE -eq 0) {
    Write-Host "Lambda invoked successfully!" -ForegroundColor Green
    
    # Read and display response
    if (Test-Path response.json) {
        Write-Host "`nResponse:" -ForegroundColor Cyan
        $responseContent = Get-Content response.json -Raw | ConvertFrom-Json
        $responseContent | ConvertTo-Json -Depth 10
        
        # Check for errors in response
        if ($responseContent.errorMessage) {
            Write-Host "`nLambda execution failed:" -ForegroundColor Red
            Write-Host $responseContent.errorMessage -ForegroundColor Red
            if ($responseContent.errorType) {
                Write-Host "Error Type: $($responseContent.errorType)" -ForegroundColor Red
            }
        } else {
            Write-Host "`nCarbon calculations generated successfully!" -ForegroundColor Green
            Write-Host "`nYou can now view the data in the dashboard." -ForegroundColor Cyan
        }
        
        # Clean up
        Remove-Item response.json -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "Failed to invoke Lambda" -ForegroundColor Red
    Write-Host "Error: $response" -ForegroundColor Red
}

Write-Host "`nTip: Run this script periodically to update carbon calculations" -ForegroundColor Yellow
Write-Host "   Or set up a CloudWatch Events rule to run it automatically" -ForegroundColor Yellow
