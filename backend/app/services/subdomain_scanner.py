import asyncio
import socket


WORDLIST = [
    "www", "mail", "ftp", "smtp", "pop", "imap", "webmail",
    "admin", "panel", "cpanel", "api", "dev", "staging", "test",
    "beta", "app", "m", "mobile", "cdn", "static", "assets",
    "shop", "store", "blog", "forum", "wiki", "docs",
    "git", "gitlab", "jenkins", "ci", "jira", "confluence",
    "vpn", "remote", "gateway", "proxy", "ns1", "ns2",
    "db", "database", "mysql", "postgres", "redis", "mongo",
    "backup", "old", "legacy", "stage", "uat", "qa",
    "auth", "sso", "login", "register", "portal", "intranet",
    "monitor", "grafana", "prometheus", "status", "health",
]


class SubdomainScanner:
    """Brute-force subdomain discovery via DNS resolution."""

    CONCURRENCY = 30
    TIMEOUT = 3.0

    async def scan(self, domain: str) -> dict:
        domain = domain.strip().lower().rstrip(".")
        loop = asyncio.get_running_loop()
        sem = asyncio.Semaphore(self.CONCURRENCY)

        async def check(sub: str) -> dict | None:
            fqdn = f"{sub}.{domain}"
            async with sem:
                try:
                    infos = await asyncio.wait_for(
                        loop.getaddrinfo(fqdn, None, family=socket.AF_INET, type=socket.SOCK_STREAM),
                        timeout=self.TIMEOUT,
                    )
                    if infos:
                        ips = list({i[4][0] for i in infos})
                        return {"subdomain": fqdn, "ips": ips}
                except (socket.gaierror, asyncio.TimeoutError, OSError):
                    return None

        tasks = [check(word) for word in WORDLIST]
        results = await asyncio.gather(*tasks)
        found = [r for r in results if r is not None]
        found.sort(key=lambda x: x["subdomain"])

        return {
            "domain": domain,
            "total_checked": len(WORDLIST),
            "found": len(found),
            "subdomains": found,
        }
