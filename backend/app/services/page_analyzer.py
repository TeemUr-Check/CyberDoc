import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class PageAnalyzer:
    """Analyses a web page for common security vulnerabilities."""

    SENSITIVE_PATHS = ("/.env", "/.git/config", "/wp-config.php", "/backup.sql")
    USER_AGENT = "CyberDoc-Scanner/3.0"

    async def analyze(self, url: str) -> dict:
        vulnerabilities: list[str] = []
        timeout = httpx.Timeout(20.0, connect=10.0)

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                headers={"User-Agent": self.USER_AGENT},
                follow_redirects=True,
                verify=False,
            ) as client:
                resp = await client.get(url)
                html = resp.text
                headers = resp.headers

                soup = BeautifulSoup(html, "lxml")

                await self._check_open_redirect(client, url, vulnerabilities)
                await self._check_reflected_xss(client, url, vulnerabilities)
                self._check_csrf_tokens(soup, vulnerabilities)
                self._check_security_headers(headers, vulnerabilities)
                await self._check_sensitive_files(client, url, vulnerabilities)

                formatted = soup.prettify()
        except httpx.TimeoutException:
            raise RuntimeError(
                f"Превышено время ожидания при подключении к {url}. "
                "Проверьте доступность ресурса."
            )
        except httpx.ConnectError as exc:
            raise RuntimeError(f"Не удалось подключиться к {url}: {exc}")

        return {
            "success": True,
            "vulnerabilities": vulnerabilities,
            "source_code": formatted,
        }

    async def _check_open_redirect(
        self, client: httpx.AsyncClient, url: str, vulns: list[str]
    ) -> None:
        try:
            resp = await client.get(
                f"{url}/?url=https://evil.com", follow_redirects=False
            )
            if resp.status_code in (301, 302):
                vulns.append(
                    "[HIGH] Потенциальный Open Redirect: "
                    "сервер обрабатывает внешние редиректы через параметры."
                )
        except Exception:
            pass

    async def _check_reflected_xss(
        self, client: httpx.AsyncClient, url: str, vulns: list[str]
    ) -> None:
        payload = "<script>alert(1)</script>"
        try:
            resp = await client.get(url, params={"search": payload})
            if payload in resp.text:
                vulns.append(
                    "[CRITICAL] Отраженная XSS: "
                    "полезная нагрузка возвращается в теле ответа без фильтрации."
                )
        except Exception:
            pass

    @staticmethod
    def _check_csrf_tokens(soup: BeautifulSoup, vulns: list[str]) -> None:
        for form in soup.find_all("form"):
            if (form.get("method") or "").upper() != "POST":
                continue
            has_token = form.find(
                "input", attrs={"name": lambda n: n and ("csrf" in n or "token" in n)}
            )
            if not has_token:
                action = form.get("action", "current page")
                vulns.append(
                    f"[MEDIUM] POST-форма без CSRF-токена: {action}"
                )

    @staticmethod
    def _check_security_headers(headers, vulns: list[str]) -> None:
        if "strict-transport-security" not in headers:
            vulns.append("[LOW] Отсутствует HSTS-заголовок: риск MITM-атаки.")
        if "x-content-type-options" not in headers:
            vulns.append("[LOW] Отсутствует X-Content-Type-Options.")
        if "x-frame-options" not in headers:
            vulns.append("[LOW] Отсутствует X-Frame-Options: риск Clickjacking.")
        server = headers.get("server")
        if server:
            vulns.append(f"[INFO] Сервер раскрывает версию: {server}")

    async def _check_sensitive_files(
        self, client: httpx.AsyncClient, url: str, vulns: list[str]
    ) -> None:
        origin = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        for path in self.SENSITIVE_PATHS:
            try:
                resp = await client.head(urljoin(origin, path))
                if resp.status_code == 200:
                    vulns.append(f"[CRITICAL] Доступен чувствительный файл: {path}")
            except Exception:
                pass
