$body = @{
  name       = "latency_2s"
  type       = "latency"
  stream     = "downstream"
  attributes = @{ latency = 2000; jitter = 100 }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post -Uri "http://localhost:8474/proxies/api_proxy/toxics" -ContentType "application/json" -Body $body
Write-Host "Toxic aplicado: latency_2s"