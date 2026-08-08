# Sample PowerShell queries for safe testing
# List Bluetooth service status
Get-Service -Name bthserv | Select-Object Name, Status

# Simple output for testing
Write-Output "hello from powershell sample"

# Sleep example (used for timeout tests)
Start-Sleep -Seconds 5
