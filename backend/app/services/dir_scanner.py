import asyncio
import httpx


PATHS = [
    "/admin", "/admin/", "/administrator",
    "/login", "/signin", "/auth",
    "/api", "/api/v1", "/api/docs", "/api/swagger",
    "/docs", "/swagger", "/graphql", "/graphiql",
    "/phpmyadmin", "/pma", "/adminer",
    "/wp-admin", "/wp-login.php", "/wp-content",
    "/.git", "/.git/config", "/.git/HEAD",
    "/.env", "/.env.backup", "/.env.local",
    "/.htaccess", "/.htpasswd",
    "/backup", "/backup.sql", "/backup.zip", "/dump.sql",
    "/robots.txt", "/sitemap.xml", "/crossdomain.xml",
    "/server-status", "/server-info",
    "/.well-known/security.txt",
    "/config.php", "/config.yml", "/config.json",
    "/debug", "/trace", "/info.php", "/phpinfo.php",
    "/console", "/shell", "/terminal",
    "/.DS_Store", "/Thumbs.db", "/web.config",
]


class DirScanner:
    """Scan common paths/directories for accessible resources."""

    CONCURRENCY = 15
    TIMEOUT = 8.0
    USER_AGENT = "CyberDoc-Scanner/3.0"

    async def scan(self, url: str) -> dict:
        url = url.rstrip("/")
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        sem = asyncio.Semaphore(self.CONCURRENCY)
        found: list[dict] = []

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.TIMEOUT, connect=5.0),
            headers={"User-Agent": self.USER_AGENT},
            follow_redirects=False,
            verify=False,
            trust_env=False,
        ) as client:

            async def check(path: str) -> dict | None:
                full = f"{url}{path}"
                async with sem:
                    try:
                        resp = await client.head(full)
                        code = resp.status_code
                        if code < 400:
                            severity = self._classify(path, code)
                            return {
                                "path": path,
                                "status": code,
                                "severity": severity,
                            }
                    except (httpx.TimeoutException, httpx.ConnectError, OSError):
                        pass
                    return None

            tasks = [check(p) for p in PATHS]
            results = await asyncio.gather(*tasks)

        found = [r for r in results if r is not None]
        found.sort(key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}.get(x["severity"], 5))

        return {
            "url": url,
            "total_checked": len(PATHS),
            "found": len(found),
            "paths": found,
        }

    @staticmethod
    def _classify(path: str, status: int) -> str:
        critical = (".env", ".git", "backup", "dump", "config.php", "config.yml", "config.json")
        high = ("admin", "phpmyadmin", "adminer", "console", "shell", "debug", "phpinfo")
        medium = ("wp-admin", "wp-login", "login", "signin", "auth", "server-status")

        p = path.lower()
        if any(k in p for k in critical):
            return "CRITICAL"
        if any(k in p for k in high):
            return "HIGH"
        if any(k in p for k in medium):
            return "MEDIUM"
        if status in (301, 302):
            return "INFO"
        return "LOW"
