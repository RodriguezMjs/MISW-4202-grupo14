$body = @{
  name     = "api_proxy"
  listen   = "0.0.0.0:8666"
  upstream = "api:5000"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8474/proxies" -ContentType "application/json" -Body $body
Write-Host "OK: api_proxy creado (8666 -> api:5000)"