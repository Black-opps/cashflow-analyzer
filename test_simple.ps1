# test_simple.ps1
$baseUrl = "http://localhost:8002"
$tenantId = "12345678-1234-1234-1234-123456789012"

Write-Host "Testing Cashflow Analyzer Service" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

Write-Host "`n1. Health Check:" -ForegroundColor Yellow
try {
    $result = Invoke-RestMethod -Uri "$baseUrl/health" -ErrorAction Stop
    Write-Host "   Status: $($result.status)" -ForegroundColor Green
    Write-Host "   Service: $($result.service)" -ForegroundColor Gray
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
}

Write-Host "`n2. Cashflow Summary:" -ForegroundColor Yellow
try {
    $url = "$baseUrl/api/v1/cashflow/summary/$tenantId`?days=30"
    $result = Invoke-RestMethod -Uri $url -ErrorAction Stop
    Write-Host "   Total Inflow: KES $($result.summary.total_inflow)" -ForegroundColor Green
    Write-Host "   Total Outflow: KES $($result.summary.total_outflow)" -ForegroundColor Green
    Write-Host "   Net Cashflow: KES $($result.summary.net_cashflow)" -ForegroundColor Green
} catch {
    Write-Host "   ERROR: $_" -ForegroundColor Red
}

Write-Host "`n3. Swagger Docs:" -ForegroundColor Yellow
Write-Host "   Open in browser: $baseUrl/api/docs" -ForegroundColor Cyan

Write-Host "`nDone!" -ForegroundColor Green