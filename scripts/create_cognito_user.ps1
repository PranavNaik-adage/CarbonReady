# Create Cognito User Script
# Usage: .\scripts\create_cognito_user.ps1 -Username "testuser" -Email "test@example.com" -Password "YourPassword123!"

param(
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$true)]
    [string]$Password,
    
    [Parameter(Mandatory=$false)]
    [string]$Group = "farmer"
)

$UserPoolId = "ap-south-1_PrdMUGun8"

Write-Host "Creating user: $Username" -ForegroundColor Green

# Create user
aws cognito-idp admin-create-user `
    --user-pool-id $UserPoolId `
    --username $Username `
    --user-attributes Name=email,Value=$Email Name=email_verified,Value=true `
    --message-action SUPPRESS

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create user" -ForegroundColor Red
    exit 1
}

Write-Host "Setting permanent password..." -ForegroundColor Yellow

# Set permanent password
aws cognito-idp admin-set-user-password `
    --user-pool-id $UserPoolId `
    --username $Username `
    --password $Password `
    --permanent

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to set password" -ForegroundColor Red
    exit 1
}

Write-Host "Adding user to group: $Group" -ForegroundColor Yellow

# Add to group
aws cognito-idp admin-add-user-to-group `
    --user-pool-id $UserPoolId `
    --username $Username `
    --group-name $Group

if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Failed to add user to group (group might not exist)" -ForegroundColor Yellow
}

Write-Host "`n✅ User created successfully!" -ForegroundColor Green
Write-Host "`nLogin credentials:" -ForegroundColor Cyan
Write-Host "  Username: $Username"
Write-Host "  Password: $Password"
Write-Host "  Email: $Email"
Write-Host "  Group: $Group"
