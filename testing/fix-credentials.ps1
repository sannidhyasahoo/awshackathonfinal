# Fix AWS Credentials for Testing

Write-Host "=== AWS Credentials Setup ===" -ForegroundColor Green
Write-Host ""

Write-Host "Setting AWS credentials from your previous session..." -ForegroundColor Yellow

# Set the credentials you provided earlier
$Env:AWS_DEFAULT_REGION="us-east-1"
$Env:AWS_SECRET_ACCESS_KEY="dVs9x8zT/UtvYlwAcd0KdeM1tux+YQa7j6uXJkoO"
$Env:AWS_SESSION_TOKEN="IQoJb3JpZ2luX2VjEJP//////////wEaCXVzLWVhc3QtMSJGMEQCIHHAJPraJsO0hoMj0iDDCJ8M8wyKJ2ZUfYsRuIiOhPVAAiBuRyxJgj7VaJE/VDq4ELJoZIL1SDeFUuuzNCSDWpclmyqZAghcEAAaDDU5MDE4Mzg4MjkwMCIMG3yqF64jo63OqRrIKvYB7qGX/PTfKq+wcwhpEsK1kV0EKSU6NEGTOyRWPz+VfkXMdVYBNW62CJOg7ycJc5OZhCwqEo+jnEKVuYs8oCP1mVM5YkpKNRW9pMX3z9Fd8Jhm5DLzMDxpT1vko8IbzvcXwKyFcALK1mku+XywikNhtbhqjPqJuA9fmCebeobKIxb6VbUJXWGPqLD06+g1pvQ6xNHABVT/PneYLWFhq0H29E822VF0cDNVjLYU4WDVCuxWtNjFcQUVGrua1d94TVSiY0uWIioYSw72mkf6jCJipVPwtU3FaS2tQRds0mff8cPkpIsCwOL2PS2f/ofXG82iKj05zvQLML6NosgGOp4BUmp0222/qXV4l5Sx0PQ0+JJtF2iW5KWxiUnEtTZ+X/tAdJ2mvCm/0Es4cNbdKxNksNMzbjtW9hFZ6jH5moqYxpXi3U/xZ52hQQxj4/hQo7oP7tu9zNOjftxODGChtrRfgOpLZ8dc9cnXjWpQazUJZuyODTU0qPZ6QZQPXSEwryaJblvAeZH1vz4HQOUJWXp8zFFvnyCcki3Id8L3XoU="

# Set threat intelligence API keys
$Env:OTX_API_KEY="9462315b260eaa05004e66363c1604eb5b508834dce83f287862f383d6bc9797"
$Env:ABUSEIPDB_API_KEY="962c3f87b47e280becbeef0e2f91e59f981f1c2874e0d12c116638d6e9335e05af18e650bc0ac76e"

Write-Host "✅ AWS credentials configured" -ForegroundColor Green
Write-Host "✅ Threat intelligence API keys configured" -ForegroundColor Green
Write-Host ""

Write-Host "Testing credentials..." -ForegroundColor Yellow
python test-credentials.py

Write-Host ""
Write-Host "Now you can run:" -ForegroundColor Cyan
Write-Host "  python quick-test.py" -ForegroundColor White
Write-Host "  python load-test.py" -ForegroundColor White
Write-Host "  python test-agents.py" -ForegroundColor White