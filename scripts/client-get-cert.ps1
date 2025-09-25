# Request an SSH certificate and save it next to your key
param(
  [string]$ApiBase = "http://localhost:8080",
  [string]$Username = "$env:USERNAME",
  [string[]]$Principals = @("devops"),
  [string]$KeyPath = "$HOME\.ssh\id_ed25519",
  [string]$Ttl = "8h"
)

$pubPath = "$KeyPath.pub"
if (!(Test-Path $KeyPath)) {
  ssh-keygen.exe -t ed25519 -f $KeyPath -C "$Username" -N ""
}
$pub = Get-Content -Raw -Path $pubPath

$body = @{
  username = $Username
  principals = $Principals
  pubkey = $pub
  ttl = $Ttl
} | ConvertTo-Json

$res = Invoke-RestMethod -Method Post -Uri "$ApiBase/api/v1/sign" -ContentType "application/json" -Body $body
if ($res.error) {
  Write-Error ($res | ConvertTo-Json -Depth 5)
  exit 1
}

$certPath = "$KeyPath-cert.pub"
$res.cert | Out-File -Encoding ascii -FilePath $certPath -Force
Write-Host "Wrote cert to $certPath"
Write-Host "Try: ssh -i `"$KeyPath`" user@your-linux-host"
