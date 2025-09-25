# Creates ed25519 SSH User CA keys in .\ca-keys\
$ErrorActionPreference = "Stop"
$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$keys = Join-Path $base "..\ca-keys"
New-Item -ItemType Directory -Force -Path $keys | Out-Null

$priv = Join-Path $keys "ssh_user_ca"
$pub  = "$priv.pub"

if (Test-Path $priv) {
  Write-Host "CA key already exists: $priv"
  exit 0
}

# Uses Windows OpenSSH (built-in). If missing, install 'OpenSSH Client' optional feature.
ssh-keygen.exe -t ed25519 -f $priv -C "SSH User CA" -N ""
Write-Host "Created:"
Write-Host "  $priv"
Write-Host "  $pub"
