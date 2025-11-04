# Get Fresh AWS Credentials

Write-Host "=== AWS Session Token Expired ===" -ForegroundColor Red
Write-Host ""
Write-Host "Your AWS session token has expired. You need to get fresh credentials." -ForegroundColor Yellow
Write-Host ""

Write-Host "Options to get fresh credentials:" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. AWS CLI (if configured):" -ForegroundColor Green
Write-Host "   aws sts get-caller-identity" -ForegroundColor White
Write-Host ""

Write-Host "2. AWS Console (get temporary credentials):" -ForegroundColor Green
Write-Host "   - Go to AWS Console" -ForegroundColor White
Write-Host "   - Click your username (top right)" -ForegroundColor White
Write-Host "   - Select 'Command line or programmatic access'" -ForegroundColor White
Write-Host "   - Copy the credentials from Option 2" -ForegroundColor White
Write-Host ""

Write-Host "3. Set new credentials manually:" -ForegroundColor Green
Write-Host '   $Env:AWS_ACCESS_KEY_ID="your_new_access_key"' -ForegroundColor White
Write-Host '   $Env:AWS_SECRET_ACCESS_KEY="your_new_secret_key"' -ForegroundColor White
Write-Host '   $Env:AWS_SESSION_TOKEN="your_new_session_token"' -ForegroundColor White
Write-Host '   $Env:AWS_DEFAULT_REGION="us-east-1"' -ForegroundColor White
Write-Host ""

Write-Host "4. Alternative - Test without deployment:" -ForegroundColor Green
Write-Host "   Since the system isn't deployed yet, you can:" -ForegroundColor White
Write-Host "   - Run simulation tests (no AWS resources needed)" -ForegroundColor White
Write-Host "   - Deploy the system first, then test" -ForegroundColor White
Write-Host ""

Write-Host "After getting fresh credentials, run:" -ForegroundColor Cyan
Write-Host "   python test-credentials.py" -ForegroundColor White
Write-Host "   python quick-test.py" -ForegroundColor White