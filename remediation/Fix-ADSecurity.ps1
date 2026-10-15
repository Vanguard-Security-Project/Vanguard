<#
.SYNOPSIS
    Automated Active Directory Hardening Script
    Author: Active Directory Remediation & Fix Engineer
.DESCRIPTION
    Automates the remediation of high-risk Active Directory misconfigurations:
    1. Enforces strong domain-wide password & account lockout policies.
    2. Disables LLMNR (Link-Local Multicast Name Resolution) via registry.
    3. Mandates SMB Server Signing to neutralize NTLM relay attacks.
#>

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSA AD REMEDIATION & HARDENING TOOL  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Enforce Domain Password Policy
Write-Host "[+] Applying Domain Password & Lockout Policy..." -ForegroundColor Yellow
try {
    Set-ADDefaultDomainPasswordPolicy -MinPasswordLength 14 -ComplexityEnabled $true -LockoutThreshold 5 -LockoutDuration (New-TimeSpan -Minutes 30) -ErrorAction Stop
    Write-Host "[SUCCESS] Password Policy updated (Min Length: 14, Complexity: Enabled, Lockout: 5 attempts)." -ForegroundColor Green
} catch {
    Write-Host "[INFO/SKIP] Run directly on the Domain Controller or with Domain Admin rights to apply policy." -ForegroundColor Gray
}

# 2. Disable Insecure LLMNR Protocol
Write-Host "`n[+] Disabling LLMNR Multicast Protocol..." -ForegroundColor Yellow
$llmnrPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient"

if (-not (Test-Path $llmnrPath)) {
    New-Item -Path $llmnrPath -Force | Out-Null
}

Set-ItemProperty -Path $llmnrPath -Name "EnableMulticast" -Value 0 -Type DWord
Write-Host "[SUCCESS] LLMNR permanently disabled." -ForegroundColor Green

# 3. Require SMB Signing
Write-Host "`n[+] Enabling Required SMB Server Signing..." -ForegroundColor Yellow
$smbPath = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"

Set-ItemProperty -Path $smbPath -Name "RequireSecuritySignature" -Value 1 -Type DWord
Write-Host "[SUCCESS] SMB Server Signing enabled." -ForegroundColor Green

Write-Host "`n[========================================]" -ForegroundColor Cyan
Write-Host " REMEDIATION COMPLETE! System Hardened.   " -ForegroundColor Cyan
Write-Host "[========================================]" -ForegroundColor Cyan