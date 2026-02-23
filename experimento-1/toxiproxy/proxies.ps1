$headers = @{
  "Content-Type" = "application/json"
  "User-Agent"   = "curl/8.0"   # <- clave
}

$body = @{
  name     = "api_proxy"
  listen   = "0.0.0.0:8666"
  upstream = "api:5000"
} | ConvertTo-Json

try {
  Invoke-RestMethod -Method Post -Uri "http://localhost:8474/proxies" -Headers $headers -Body $body | Out-Null
  Write-Host "OK: api_proxy creado (8666 -> api:5000)"
} catch {
  Write-Host "ERROR creando proxy en toxiproxy: $($_.Exception.Message)"
  exit 1
}