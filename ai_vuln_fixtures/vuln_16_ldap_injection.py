# INTENTIONALLY VULNERABLE — AI / training fixture only.
import ldap


def find_user(filter_value: str):
    conn = ldap.initialize("ldap://directory.internal")
    base = "ou=users,dc=corp,dc=local"
    filt = f"(uid={filter_value})"
    return conn.search_s(base, ldap.SCOPE_SUBTREE, filt)
