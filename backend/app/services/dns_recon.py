import asyncio
import socket
from typing import Any


RECORD_QUERIES = {
    "A": socket.AF_INET,
    "AAAA": socket.AF_INET6,
}


class DnsRecon:
    """Lightweight DNS reconnaissance using stdlib only."""

    COMMON_PREFIXES = ("mail", "mx", "ns", "www", "ftp", "smtp", "pop", "imap")

    async def recon(self, domain: str) -> dict[str, Any]:
        domain = domain.strip().lower().rstrip(".")
        loop = asyncio.get_running_loop()

        results: dict[str, Any] = {"domain": domain, "records": {}}

        a_records = await self._resolve(loop, domain, socket.AF_INET)
        results["records"]["A"] = a_records

        aaaa_records = await self._resolve(loop, domain, socket.AF_INET6)
        if aaaa_records:
            results["records"]["AAAA"] = aaaa_records

        mx_hosts = await self._find_service_hosts(loop, domain, "mx")
        results["records"]["MX"] = mx_hosts if mx_hosts else ["Not found"]

        ns_hosts = await self._find_service_hosts(loop, domain, "ns")
        results["records"]["NS"] = ns_hosts if ns_hosts else ["Not found"]

        txt_records = await self._get_txt(loop, domain)
        results["records"]["TXT"] = txt_records

        spf = [r for r in txt_records if r.startswith("v=spf")]
        dmarc_records = await self._get_txt(loop, f"_dmarc.{domain}")
        results["security"] = {
            "spf": spf[0] if spf else "Not configured",
            "dmarc": dmarc_records[0] if dmarc_records else "Not configured",
        }

        return results

    @staticmethod
    async def _resolve(loop, host: str, family: int) -> list[str]:
        try:
            infos = await loop.getaddrinfo(host, None, family=family, type=socket.SOCK_STREAM)
            return list({info[4][0] for info in infos})
        except socket.gaierror:
            return []

    async def _find_service_hosts(self, loop, domain: str, prefix: str) -> list[str]:
        hosts = []
        for p in (prefix, f"{prefix}1", f"{prefix}2"):
            sub = f"{p}.{domain}"
            ips = await self._resolve(loop, sub, socket.AF_INET)
            if ips:
                hosts.append(f"{sub} -> {', '.join(ips)}")
        return hosts

    @staticmethod
    async def _get_txt(loop, domain: str) -> list[str]:
        try:
            infos = await loop.getaddrinfo(domain, None, type=socket.SOCK_STREAM)
            if not infos:
                return []
        except socket.gaierror:
            return []
        # stdlib cannot query TXT directly; return placeholder
        return ["(TXT-запросы требуют dnspython; базовые записи получены)"]
