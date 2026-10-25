Lab Handoff — Vanguard AD Attack Path (vanguard.local)
This document describes the Active Directory lab used to demo Vanguard, how the
attack path was built, and how to reproduce or re-misconfigure it for another
test run.
1. Environment
VM	Role	Hostname	IP
VM1	Domain Controller	DC01	10.10.10.10
VM2	Member Server	SRV01	DHCP/static on the internal lab network
Hypervisor: VirtualBox, both VMs on an Internal Network adapter (not NAT),
so the lab is fully isolated from the host's real network.
Domain: vanguard.local
DC01 runs AD DS (Active Directory Domain Services) and is the domain's DNS server.
SRV01 is domain-joined as a regular member server.
2. Accounts, groups, and OUs
OU structure holds the lab's custom users and groups (created via dsadd/
New-ADUser/New-ADGroup, separate from the built-in Users container).
Key identities:
kyle.it — a low-privileged Helpdesk account. Member of Helpdesk-Team.
svc.backup — a service account used by a scheduled backup task on
SRV01. Member of Domain Admins.
Key groups:
Helpdesk-Team — ordinary helpdesk staff group.
Server-Admins — intended to hold legitimate server administrators;
this is the group the misconfiguration abuses.
3. The planted attack path
The scenario: a helpdesk technician's account (kyle.it) can reach Domain Admin
through a chain of everyday-looking permissions, none of which look alarming in
isolation:
kyle.it  --MemberOf-->  Server-Admins  --AdminTo-->  SRV01
                                                        |
                                                 (scheduled task runs as)
                                                        v
                                                  svc.backup  --MemberOf--> Domain Admins
Misconfiguration: kyle.it was added to the Server-Admins group — a
group that should only ever contain real server admins, not helpdesk staff.
Server-Admins → SRV01: the Server-Admins group has local admin rights
on SRV01.
Credential exposure on SRV01: a scheduled task on SRV01 runs under the
svc.backup service account (schtasks /create ... /ru svc.backup),
meaning anyone with admin rights on SRV01 can extract or trigger actions as
svc.backup.
svc.backup → Domain Admins: svc.backup is itself a member of
Domain Admins.
End result: a helpdesk account with no special rights of its own can walk this
chain to full Domain Admin control — a textbook "assumed breach" privilege
escalation path, and exactly what Vanguard is built to find and fix.
4. Collecting the data (SharpHound)
From SRV01 (domain-joined), run SharpHound to collect the AD data as the
vanguard.local domain:
.\SharpHound.exe -c All -d vanguard.local
This produces a timestamped *_BloodHound.zip containing users.json,
groups.json, computers.json, ous.json, domains.json, gpos.json,
containers.json, sites.json, and siteservers.json.
5. Running the Vanguard pipeline
From the repo root, with Python 3 installed (no third-party packages required
for the CLI path):
python cli.py pipeline path\to\your_BloodHound.zip
This runs all five stages — Discover → Analyze → Fix → Re-attack → Verify —
and prints a findings summary. A findings count of 0 almost always means the
export didn't load correctly, not that the lab is clean; check that the zip
actually contains the group-membership and ACE data before assuming there's
nothing to find.
6. Applying a fix for real (for the demo recording)
The generated Apply-Fix.ps1 contains one targeted line that undoes the real
misconfiguration — removing kyle.it from Server-Admins:
Remove-ADGroupMember -Identity "<Server-Admins SID>" -Members "<kyle.it SID>" -Confirm:$false
Run this single line on DC01 (it has the AD PowerShell module; SRV01 does
not). Do not blindly run the entire generated script — several of its
other suggested fixes target built-in groups like Domain Admins/Enterprise
Admins/Schema Admins membership for the real Administrator account, which
are normal, expected memberships, not vulnerabilities. Only the
Server-Admins / kyle.it line reflects an actual planted issue.
7. Re-misconfiguring for another take
To run the demo again (for a re-recording or a second rehearsal), just redo
step 3 of the misconfiguration:
Add-ADGroupMember -Identity "Server-Admins" -Members "kyle.it"
Then re-run SharpHound and the pipeline from scratch (step 4–5 above) to
capture a fresh "before" state. This round-trip (break → scan → fix → scan
again) is exactly what proves the fix is real and not just a simulated result.
8. Known limitations / notes for reviewers
AD's AdminSDHolder/SDProp background process periodically strips custom
ACEs from accounts that look "protected" (e.g. ones associated with
privileged groups) and resets their ACLs to a protected template. If a
custom permission you planted on a privileged-adjacent account disappears
on its own between runs, this is almost always why — check
admincount/adminsdholderprotected/isaclprotected on the account to
confirm, and re-apply the misconfiguration before the next scan.
The web UI (backend/main.py + backend/ui.py) only accepts a real
SharpHound/BloodHound .zip or .json export — there is no demo/sample
data option, so anything shown in the UI reflects a genuine uploaded scan.