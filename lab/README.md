# Lab

Only needed if you want to run the pipeline against a real AD domain. The
unit tests already exercise every stage with inline fixtures.

## What you need

- VirtualBox, VMware, or Hyper-V
- Windows Server 2022 ISO
- Two Windows 10 or 11 client ISOs (optional)
- About 16 GB RAM, 200 GB disk on the host

## Build

1. Install Windows Server 2022, name it `LAB-DC01`, static IP 10.10.10.10.
2. Promote to a new forest at a domain like `lab.local`.
3. Join one or two clients. Set their DNS to the DC.
4. On the DC, as Domain Admin:

        Set-ExecutionPolicy -Scope Process Bypass
        .\New-VanguardLab.ps1 -MemberServer "YOUR-SERVER-NAME"

5. Snapshot the DC. Call it `post-build`.

## Collect

On a domain-joined Windows host with RSAT and SharpHound.ps1:

    Import-Module .\SharpHound.ps1
    Invoke-BloodHound -CollectionMethod All -OutputDirectory .\out -OutputPrefix vanguard
    Compress-Archive .\out\* vanguard-bundle.zip

## Reset

Revert the DC to `post-build`, re-run the collector.

## If you renamed the member server

Pass the new name:

    .\New-VanguardLab.ps1 -MemberServer "MY-SERVER"
