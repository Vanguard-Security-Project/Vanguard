USER = "User"
GROUP = "Group"
COMPUTER = "Computer"
GPO = "GPO"
OU = "OU"
DOMAIN = "Domain"
UNKNOWN = "Unknown"

NODE_KINDS = {USER, GROUP, COMPUTER, GPO, OU, DOMAIN, UNKNOWN}


def normalize_kind(raw):
    
    table = {
        "user": USER, "users": USER, "person": USER,
        "group": GROUP, "groups": GROUP,
        "computer": COMPUTER, "computers": COMPUTER, "machine": COMPUTER,
        "gpo": GPO, "gpos": GPO,
        "ou": OU, "organizationalunit": OU,
        "domain": DOMAIN, "domains": DOMAIN,
    }
    return table.get(str(raw or "").strip().lower(), UNKNOWN)



PRIVILEGED_NAMES = {
    "DOMAIN ADMINS", "ENTERPRISE ADMINS", "SCHEMA ADMINS",
    "ADMINISTRATORS", "DOMAIN CONTROLLERS",
    "ENTERPRISE KEY ADMINS", "KEY ADMINS", "PROTECTED USERS",
    "ACCOUNT OPERATORS", "SERVER OPERATORS", "BACKUP OPERATORS",
    "PRINT OPERATORS", "KRBTGT",
}


def is_privileged_name(name):
    return str(name or "").strip().upper() in PRIVILEGED_NAMES
