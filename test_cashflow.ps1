# test_cashflow.ps1
$baseUrl = "http://localhost:8002"
$tenantId = "12345678-1234-1234-1234-123456789012"

Write-Host "🔍 Testing Cashflow Analyzer Service" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# 1. Health Check
Write-Host "`n1️⃣ Health Check:" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health"
    Write-Host "   Status: $($health.status)" -ForegroundColor Green
    Write-Host "   Service: $($health.service)" -ForegroundColor Gray
    Write-Host "   Version: $($health.version)" -ForegroundColor Gray
} catch { 
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red 
}

# 2. Cashflow Summary
Write-Host "`n2️⃣ Cashflow Summary (30 days):" -ForegroundColor Yellow
try {
    $summary = Invoke-RestMethod -Uri "$baseUrl/api/v1/cashflow/summary/$tenantId?days=30"
    Write-Host "   Total Inflow: KES $($summary.summary.total_inflow)" -ForegroundColor Green
    Write-Host "   Total Outflow: KES $($summary.summary.total_outflow)" -ForegroundColor Green
    Write-Host "   Net Cashflow: KES $($summary.summary.net_cashflow)" -ForegroundColor Green
    Write-Host "   Transactions: $($summary.summary.transaction_count)" -ForegroundColor Gray
} catch { 
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red 
}

# 3. Pattern Detection (using encoded URL)
Write-Host "`n3️⃣ Pattern Detection:" -ForegroundColor Yellow
try {
    $patternUrl = "$baseUrl/api/v1/cashflow/patterns?tenant_id=$tenantId"
    $patterns = Invoke-RestMethod -Uri $patternUrl -Method Post
    Write-Host "   Patterns found: $($patterns.Count)" -ForegroundColor Green
    if ($patterns.Count -gt 0) {
        foreach ($pattern in $patterns) {
            Write-Host "     - $($pattern.pattern_type): $($pattern.description)" -ForegroundColor Gray
        }
    }
} catch { 
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red 
}

# 4. Real-time Stats
Write-Host "`n4️⃣ Real-time Stats (24h):" -ForegroundColor Yellow
try {
    $realtime = Invoke-RestMethod -Uri "$baseUrl/api/v1/cashflow/realtime/$tenantId?hours=24"
    Write-Host "   Total Inflow: KES $($realtime.total_inflow)" -ForegroundColor Green
    Write-Host "   Total Outflow: KES $($realtime.total_outflow)" -ForegroundColor Green
    Write-Host "   Net: KES $($realtime.net)" -ForegroundColor Green
    Write-Host "   Transactions: $($realtime.transaction_count)" -ForegroundColor Gray
} catch { 
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red 
}

# 5. Analyze Endpoint (POST)
Write-Host "`n5️⃣ Analyze Cashflow (POST):" -ForegroundColor Yellow
try {
    $analyzeBody = @{
        tenant_id = $tenantId
        start_date = "2026-03-01T00:00:00Z"
        end_date = "2026-04-02T23:59:59Z"
        group_by = "week"
        include_details = $true
    } | ConvertTo-Json
    
    $analysis = Invoke-RestMethod -Uri "$baseUrl/api/v1/cashflow/analyze" `
        -Method Post `
        -Body $analyzeBody `
        -ContentType "application/json"
    
    Write-Host "   Net Cashflow: KES $($analysis.summary.net_cashflow)" -ForegroundColor Green
    Write-Host "   Period Count: $($analysis.summary.period_count)" -ForegroundColor Gray
} catch { 
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red 
}

# 6. Swagger UI
Write-Host "`n6️⃣ API Documentation:" -ForegroundColor Yellow
Write-Host "   Swagger UI: $baseUrl/api/docs" -ForegroundColor Cyan

Write-Host "`n✅ Test complete!" -ForegroundColor Green