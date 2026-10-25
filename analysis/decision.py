BLAST = {"low": 1, "medium": 3, "high": 5}


FIXES = [
    {
        "id": "remove_membership",
        "matches": ["MemberOf"],
        "kind": "RemoveMember",
        "blast_radius": "low",
        "ps_apply": 'Remove-ADGroupMember -Identity "{group}" -Members "{principal}" -Confirm:$false',
        "ps_rollback": 'Add-ADGroupMember -Identity "{group}" -Members "{principal}"',
    },
    {
        "id": "remove_local_admin",
        "matches": ["AdminTo"],
        "kind": "RemoveLocalAdmin",
        "blast_radius": "low",
        "ps_apply": ('Invoke-Command -ComputerName "{target}" -ScriptBlock {{ '
                     'Remove-LocalGroupMember -Group "Administrators" -Member "{principal}" }}'),
        "ps_rollback": ('Invoke-Command -ComputerName "{target}" -ScriptBlock {{ '
                        'Add-LocalGroupMember -Group "Administrators" -Member "{principal}" }}'),
    },
    {
        "id": "remove_generic_all",
        "matches": ["GenericAll"],
        "kind": "RemoveDaclAce",
        "blast_radius": "medium",
        "ps_apply": ('$acl = Get-Acl "AD:{target_dn}"; '
                     '$acl.Access | Where-Object {{ $_.IdentityReference -like "*{principal}*" '
                     '-and $_.ActiveDirectoryRights -match "GenericAll" }} | '
                     'ForEach-Object {{ $acl.RemoveAccessRule($_) | Out-Null }}; '
                     'Set-Acl "AD:{target_dn}" $acl'),
        "ps_rollback": "# restore SD from backup",
    },
    {
        "id": "remove_write_dacl",
        "matches": ["WriteDacl"],
        "kind": "RemoveDaclAce",
        "blast_radius": "medium",
        "ps_apply": ('$acl = Get-Acl "AD:{target_dn}"; '
                     '$acl.Access | Where-Object {{ $_.IdentityReference -like "*{principal}*" '
                     '-and $_.ActiveDirectoryRights -match "WriteDacl" }} | '
                     'ForEach-Object {{ $acl.RemoveAccessRule($_) | Out-Null }}; '
                     'Set-Acl "AD:{target_dn}" $acl'),
        "ps_rollback": "# restore SD from backup",
    },
    {
        "id": "remove_force_change_password",
        "matches": ["ForceChangePassword"],
        "kind": "RemoveDaclAce",
        "blast_radius": "medium",
        "ps_apply": ('$acl = Get-Acl "AD:{target_dn}"; '
                     '$acl.Access | Where-Object {{ $_.IdentityReference -like "*{principal}*" '
                     '-and $_.ObjectType -eq "00299570-246d-11d0-a768-00aa006e0529" }} | '
                     'ForEach-Object {{ $acl.RemoveAccessRule($_) | Out-Null }}; '
                     'Set-Acl "AD:{target_dn}" $acl'),
        "ps_rollback": "# restore SD from backup",
    },
    {
        "id": "remove_dcsync",
        "matches": ["GetChanges", "GetChangesAll"],
        "kind": "RemoveDaclAce",
        "blast_radius": "medium",
        "ps_apply": ('$acl = Get-Acl "AD:{target_dn}"; '
                     '$acl.Access | Where-Object {{ $_.IdentityReference -like "*{principal}*" '
                     '-and ($_.ObjectType -eq "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2" '
                     '-or $_.ObjectType -eq "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2") }} | '
                     'ForEach-Object {{ $acl.RemoveAccessRule($_) | Out-Null }}; '
                     'Set-Acl "AD:{target_dn}" $acl'),
        "ps_rollback": "# restore SD from backup",
    },
    {
        "id": "remove_unconstrained_delegation",
        "matches": ["AllowedToDelegate"],
        "kind": "RemoveDelegation",
        "blast_radius": "high",
        "ps_apply": 'Set-ADAccountControl -Identity "{principal}" -TrustedForDelegation $false',
        "ps_rollback": 'Set-ADAccountControl -Identity "{principal}" -TrustedForDelegation $true',
    },
    {
        "id": "remove_rbcd",
        "matches": ["AllowedToAct", "RBCD"],
        "kind": "RemoveRBCD",
        "blast_radius": "high",
        "ps_apply": 'Set-ADComputer -Identity "{target}" -Clear "msDS-AllowedToActOnBehalfOfOtherIdentity"',
        "ps_rollback": "# restore from backup",
    },
]


def _context(finding):
    edges = finding.get("edges", [])
    nodes = finding.get("nodes", [])
    ctx = {"principal": "", "group": "", "target": "", "target_dn": ""}
    if not edges or not nodes:
        return ctx
    ctx["principal"] = edges[0].get("source") or nodes[0]["id"]
    if edges[0].get("relationship") == "MemberOf" and len(nodes) > 1:
        ctx["group"] = edges[0].get("target") or nodes[1]["id"]
    ctx["target"] = edges[-1].get("target") or nodes[-1]["id"]
    ctx["target_dn"] = ctx["target"]
    return ctx


def decide(finding):
    rels = [e.get("relationship", "") for e in finding.get("edges", [])]
    hits = [f for f in FIXES if any(m in rels for m in f["matches"])]

    if not hits:
        return {
            "finding": finding,
            "context": _context(finding),
            "chosen": None,
            "alternatives": [],
            "rationale": "no rule matched, flag for manual review",
        }

    hits.sort(key=lambda f: (BLAST[f["blast_radius"]], f["id"]))
    return {
        "finding": finding,
        "context": _context(finding),
        "chosen": hits[0],
        "alternatives": hits[1:],
        "rationale": "{} (blast: {})".format(hits[0]["id"], hits[0]["blast_radius"]),
    }


def decide_batch(findings):
    return [decide(f) for f in findings]
