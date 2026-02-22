$toxics = Invoke-RestMethod -Uri "http://localhost:8474/proxies/api_proxy/toxics"
$toxics.PSObject.Properties.Name | ForEach-Object {
  Invoke-RestMethod -Method Delete -Uri "http://localhost:8474/proxies/api_proxy/toxics/$_"
}
Write-Host "Toxics eliminados"