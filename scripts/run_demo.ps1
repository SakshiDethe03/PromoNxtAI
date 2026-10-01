# PromoNxtAI 1-Command Demo Launcher & Interactive Guide
$ErrorActionPreference = "Stop"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  PromoNxtAI - Live Demo Environment Launcher" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# Set environment variables for live image generation demo
$env:USE_SAMPLE_DATA = "true"
$env:IMAGE_MOCK = "false"
$env:N8N_MOCK = "true"

Write-Host "`n[1/3] Starting PromoNxtAI Backend Server..." -ForegroundColor Yellow
$BackendProcess = Start-Process python -ArgumentList "-m uvicorn app.main:app --port 8000" -PassThru -NoNewWindow

Write-Host "[2/3] Waiting for server health check on http://127.0.0.1:8000/health..." -ForegroundColor Yellow
$serverReady = $false
for ($i = 1; $i -le 15; $i++) {
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -ErrorAction SilentlyContinue
        if ($res.status -eq "ok") {
            $serverReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $serverReady) {
    Write-Host "ERROR: Server failed to start on port 8000!" -ForegroundColor Red
    exit 1
}

Write-Host "`n[3/3] SERVER READY! Live Demo Interactive Commands" -ForegroundColor Green
Write-Host "Copy and paste the following commands step-by-step during your live presentation:`n" -ForegroundColor White

Write-Host "----------------------------------------------------" -ForegroundColor Gray
Write-Host "STEP 1: Create Campaign (Autonomous AI Agent Pipeline)" -ForegroundColor Cyan
Write-Host "----------------------------------------------------" -ForegroundColor Gray
Write-Host 'Invoke-RestMethod -Uri "http://127.0.0.1:8000/campaigns" -Method Post -ContentType "application/json" -Body ''{"business_id": "biz_101", "goal": "clear excess stock", "language": "en"}''' -ForegroundColor Yellow

Write-Host "`n----------------------------------------------------" -ForegroundColor Gray
Write-Host "STEP 2: Approve Campaign (Shopkeeper HITL Approval)" -ForegroundColor Cyan
Write-Host "----------------------------------------------------" -ForegroundColor Gray
Write-Host '# Replace <CAMPAIGN_ID> with the campaign_id returned above:' -ForegroundColor Gray
Write-Host 'Invoke-RestMethod -Uri "http://127.0.0.1:8000/campaigns/<CAMPAIGN_ID>/approve" -Method Post -ContentType "application/json" -Body ''{"action": "approve"}''' -ForegroundColor Yellow

Write-Host "`n----------------------------------------------------" -ForegroundColor Gray
Write-Host "STEP 3: Publish Campaign (Trigger n8n Webhook)" -ForegroundColor Cyan
Write-Host "----------------------------------------------------" -ForegroundColor Gray
Write-Host 'Invoke-RestMethod -Uri "http://127.0.0.1:8000/campaigns/<CAMPAIGN_ID>/publish" -Method Post' -ForegroundColor Yellow

Write-Host "`n----------------------------------------------------" -ForegroundColor Gray
Write-Host "STEP 4: Simulate n8n Instagram Callback" -ForegroundColor Cyan
Write-Host "----------------------------------------------------" -ForegroundColor Gray
Write-Host 'Invoke-RestMethod -Uri "http://127.0.0.1:8000/n8n/callback" -Method Post -Headers @{"X-Webhook-Secret"="your_n8n_shared_secret_here"} -ContentType "application/json" -Body ''{"campaign_id": "<CAMPAIGN_ID>", "status": "published", "instagram_post_id": "ig_live_101", "permalink": "https://instagram.com/p/live_demo"}''' -ForegroundColor Yellow

Write-Host "`n----------------------------------------------------" -ForegroundColor Gray
Write-Host "STEP 5: Get Full Audit Activity Log" -ForegroundColor Cyan
Write-Host "----------------------------------------------------" -ForegroundColor Gray
Write-Host 'Invoke-RestMethod -Uri "http://127.0.0.1:8000/campaigns/<CAMPAIGN_ID>/activity" -Method Get' -ForegroundColor Yellow
Write-Host "`n====================================================" -ForegroundColor Cyan
