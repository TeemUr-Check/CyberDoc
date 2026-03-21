import asyncio
import socket


WELL_KNOWN_SERVICES = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    8080: "HTTP-Proxy",
    8443: "HTTPS-Alt",
}

DEFAULT_PORTS = sorted(WELL_KNOWN_SERVICES.keys())


class PortScanner:
    """Asynchronous TCP port scanner."""

    CONNECT_TIMEOUT = 3.0

    async def scan(self, host: str) -> list[dict]:
        try:
            infos = await asyncio.get_running_loop().getaddrinfo(
                host, None, family=socket.AF_INET, type=socket.SOCK_STREAM
            )
            ip = infos[0][4][0] if infos else host
        except socket.gaierror:
            ip = host

        tasks = [self._check_port(ip, port) for port in DEFAULT_PORTS]
        results = await asyncio.gather(*tasks)
        return sorted(
            [r for r in results if r is not None],
            key=lambda r: r["port"],
        )

    async def _check_port(self, host: str, port: int) -> dict | None:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.CONNECT_TIMEOUT,
            )
            writer.close()
            await writer.wait_closed()
            return {
                "port": port,
                "status": "OPEN",
                "service": WELL_KNOWN_SERVICES.get(port, "Unknown"),
            }
        except (asyncio.TimeoutError, OSError, ConnectionRefusedError):
            return None
