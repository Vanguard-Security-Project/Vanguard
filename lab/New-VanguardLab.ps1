<#
.SYNOPSIS  Build the Vanguard test AD.
.DESCRIPTION
    Creates the users, groups, and intentional misconfigurations that give 
.NOTES  Rename $MemberServer to whatever your member server is actually called. Everything else works as is.
#>
[CmdletBinding()]
param(
    [string]$OuName = "VanguardLab",
    [string]$MemberServer = "LAB-SRV01",
    [string]$DefaultPassword = "ChangeMe!2024"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Import-Module ActiveDirectory

$domainDn = (Get-ADDomain).DistinguishedName
$ouDn = "OU=$OuName,$domainDn"

if (-not (Get-ADOrganizationalUnit -Filter "Name -eq '$OuName'" -ErrorAction SilentlyContinue)) {
    New-ADOrganizationalUnit -Name $OuName -Path $domainDn -ProtectedFromAccidentalDeletion $false
}

$pw = ConvertTo-SecureString $DefaultPassword -AsPlainText -Force
foreach ($name in @("alice.contractor", "bob.helpdesk", "carol.svc.backup",
                    "dave.intern", "dana.admin", "eve.svc.sql")) {
    if (-not (Get-ADUser -Filter "SamAccountName -eq '$name'" -ErrorAction SilentlyContinue)) {
        New-ADUser -Name $name -SamAccountName $name -Path $ouDn `
            -AccountPassword $pw -Enabled $true -PasswordNeverExpires $true
    }
}

foreach ($g in @("Helpdesk", "IT Admins", "Server Operators",
                 "Backup Operators", "SQL Admins")) {
    if (-not (Get-ADGroup -Filter "Name -eq '$g'" -ErrorAction SilentlyContinue)) {
        New-ADGroup -Name $g -GroupScope Global -Path $ouDn
    }
}

function Add-IfMissing {
    param([string]$Group, [string]$Member)
    $existing = (Get-ADGroupMember -Identity $Group -ErrorAction SilentlyContinue).SamAccountName
    if ($existing -notcontains $Member) {
        Add-ADGroupMember -Identity $Group -Members $Member
    }
}

Add-IfMissing -Group "Helpdesk"         -Member "alice.contractor"
Add-IfMissing -Group "Helpdesk"         -Member "bob.helpdesk"
Add-IfMissing -Group "IT Admins"        -Member "dave.intern"
Add-IfMissing -Group "Backup Operators" -Member "carol.svc.backup"
Add-IfMissing -Group "SQL Admins"       -Member "eve.svc.sql"

try {
    Invoke-Command -ComputerName $MemberServer -ScriptBlock {
        Add-LocalGroupMember -Group "Administrators" -Member "LAB\Helpdesk" -ErrorAction SilentlyContinue
    }
} catch {
    Write-Warning "Could not set local admin on ${MemberServer}: $_"
}

$daDn = (Get-ADGroup "Domain Admins").DistinguishedName
$acl = Get-Acl "AD:$daDn"

$so = New-Object System.Security.Principal.NTAccount("LAB", "Server Operators")
$rule = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $so,
    [System.DirectoryServices.ActiveDirectoryRights]::GenericAll,
    [System.Security.AccessControl.AccessControlType]::Allow)
$acl.AddAccessRule($rule)

$bo = New-Object System.Security.Principal.NTAccount("LAB", "Backup Operators")
$rule = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $bo,
    [System.DirectoryServices.ActiveDirectoryRights]::WriteDacl,
    [System.Security.AccessControl.AccessControlType]::Allow)
$acl.AddAccessRule($rule)

Set-Acl "AD:$daDn" $acl

$dana = Get-ADUser "dana.admin" -Properties DistinguishedName
$danaAcl = Get-Acl "AD:$($dana.DistinguishedName)"
$it = New-Object System.Security.Principal.NTAccount("LAB", "IT Admins")
$guid = [Guid]"00299570-246d-11d0-a768-00aa006e0529"
$rule = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $it,
    [System.DirectoryServices.ActiveDirectoryRights]::ExtendedRight,
    [System.Security.AccessControl.AccessControlType]::Allow,
    $guid)
$danaAcl.AddAccessRule($rule)
Set-Acl "AD:$($dana.DistinguishedName)" $danaAcl

$domainAcl = Get-Acl "AD:$domainDn"
$sqla = New-Object System.Security.Principal.NTAccount("LAB", "SQL Admins")
$dsync = [Guid]"1131f6ad-9c07-11d1-f79f-00c04fc2dcd2"
$rule = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $sqla,
    [System.DirectoryServices.ActiveDirectoryRights]::ExtendedRight,
    [System.Security.AccessControl.AccessControlType]::Allow,
    $dsync)
$domainAcl.AddAccessRule($rule)
Set-Acl "AD:$domainDn" $domainAcl

Set-ADAccountControl -Identity "carol.svc.backup" -TrustedForDelegation $true

Write-Host ""
Write-Host "Lab built. Take a hypervisor snapshot named 'post-build' now."
Write-Host "Domain: $((Get-ADDomain).DNSRoot)"
