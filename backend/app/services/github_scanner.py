import re
import logging
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

SECRET_PATTERNS = [
    ("AWS Access Key", r"AKIA[0-9A-Z]{16}"),
    ("AWS Secret Key", r"(?i)aws.{0,20}['\"][0-9a-zA-Z/+=]{40}['\"]"),
    ("GitHub Token", r"gh[pousr]_[A-Za-z0-9_]{36,255}"),
    ("Generic API Key", r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{20,}"),
    ("Generic Secret", r"(?i)(secret|password|passwd|pwd|token)\s*[=:]\s*['\"]?[^\s'\"]{8,}"),
    ("Private Key Header", r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    ("JWT Token", r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("Database URL", r"(?i)(postgres|mysql|mongodb|redis)://[^\s'\"]+"),
    ("Slack Token", r"xox[baprs]-[0-9a-zA-Z\-]{10,}"),
    ("Telegram Bot Token", r"\d{8,10}:AA[0-9A-Za-z_-]{33}"),
    ("Stripe Key", r"(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{20,}"),
    ("SendGrid Key", r"SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}"),
]

SUSPICIOUS_FILENAMES = {
    ".env", ".env.local", ".env.production", ".env.development", ".env.staging",
    "credentials.json", "secrets.json", "service-account.json",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
    ".htpasswd", ".netrc", ".pgpass",
    "wp-config.php", "configuration.php",
}

SCANNABLE_EXTENSIONS = (
    ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yml", ".yaml",
    ".env", ".cfg", ".conf", ".ini", ".php", ".rb", ".java", ".go",
    ".rs", ".toml", ".xml", ".properties", ".sh", ".bash",
)


class GitHubScanner:
    def __init__(self):
        self._timeout = 30.0

    @staticmethod
    def _parse_repo(url: str) -> tuple[str, str]:
        url = url.strip().rstrip("/").removesuffix(".git")
        if "github.com" in url:
            path = urlparse(url).path.strip("/")
            parts = path.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
        if "/" in url and not url.startswith("http"):
            parts = url.split("/")
            if len(parts) == 2:
                return parts[0], parts[1]
        raise ValueError(f"Не удалось разобрать GitHub URL: {url}")

    async def scan(self, url: str) -> dict:
        owner, repo = self._parse_repo(url)
        findings: list[dict] = []
        scanned = 0

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            tree_resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD",
                params={"recursive": "1"},
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            if tree_resp.status_code == 404:
                return {
                    "error": "Репозиторий не найден или является приватным.",
                    "repository": f"{owner}/{repo}",
                    "findings": [],
                    "scanned_files": 0,
                    "total_files": 0,
                }
            tree_resp.raise_for_status()
            tree = tree_resp.json().get("tree", [])

            blobs = [i for i in tree if i["type"] == "blob"]

            for item in blobs:
                path = item["path"]
                fname = path.rsplit("/", 1)[-1] if "/" in path else path
                if fname in SUSPICIOUS_FILENAMES:
                    findings.append({
                        "severity": "HIGH",
                        "file": path,
                        "line": None,
                        "detail": f"Подозрительный файл в репозитории: {fname}",
                    })

            files_to_scan = [
                i["path"] for i in blobs
                if i.get("size", 0) < 60_000
                and any(i["path"].endswith(ext) for ext in SCANNABLE_EXTENSIONS)
            ]

            for path in files_to_scan[:80]:
                try:
                    resp = await client.get(
                        f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}",
                    )
                    if resp.status_code != 200:
                        continue
                    content = resp.text
                    scanned += 1

                    for name, pattern in SECRET_PATTERNS:
                        for match in re.finditer(pattern, content):
                            line_num = content[: match.start()].count("\n") + 1
                            snippet = match.group()
                            if len(snippet) > 50:
                                snippet = snippet[:25] + "..." + snippet[-15:]
                            findings.append({
                                "severity": "CRITICAL",
                                "file": path,
                                "line": line_num,
                                "detail": f"{name}: {snippet}",
                            })
                except Exception as exc:
                    logger.debug("Error scanning %s: %s", path, exc)

        return {
            "repository": f"{owner}/{repo}",
            "scanned_files": scanned,
            "total_files": len(blobs),
            "findings": findings,
            "findings_count": len(findings),
        }
