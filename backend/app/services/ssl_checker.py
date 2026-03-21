import asyncio
import ssl
import socket
import hashlib
from datetime import datetime, timezone


class SSLChecker:
    """Retrieves and validates SSL/TLS certificate information."""

    CONNECT_TIMEOUT = 8.0

    async def check(self, hostname: str) -> dict:
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, self._fetch_cert, hostname),
                timeout=self.CONNECT_TIMEOUT + 2,
            )
        except asyncio.TimeoutError:
            return {"valid": False, "error": "Connection timed out"}
        except Exception as exc:
            return {"valid": False, "error": str(exc)}

    @staticmethod
    def _fetch_cert(hostname: str) -> dict:
        ctx_valid = ssl.create_default_context()
        is_valid = False
        try:
            with socket.create_connection((hostname, 443), timeout=5) as raw:
                with ctx_valid.wrap_socket(raw, server_hostname=hostname) as secure:
                    cert = secure.getpeercert(binary_form=False)
                    der = secure.getpeercert(binary_form=True)
                    is_valid = True
        except ssl.SSLCertVerificationError:
            ctx_no_verify = ssl.create_default_context()
            ctx_no_verify.check_hostname = False
            ctx_no_verify.verify_mode = ssl.CERT_NONE
            with socket.create_connection((hostname, 443), timeout=5) as raw:
                with ctx_no_verify.wrap_socket(raw, server_hostname=hostname) as secure:
                    der = secure.getpeercert(binary_form=True)
                    cert = None
        except Exception as exc:
            return {"valid": False, "error": str(exc)}

        if cert:
            subject = dict(x[0] for x in cert.get("subject", ()))
            issuer = dict(x[0] for x in cert.get("issuer", ()))
            not_before = cert.get("notBefore", "")
            not_after = cert.get("notAfter", "")
        else:
            from ssl import DER_cert_to_PEM_cert
            import re
            pem = DER_cert_to_PEM_cert(der)
            subject = {"commonName": hostname}
            issuer = {"organizationName": "Unknown (cert unverified)"}
            not_before = ""
            not_after = ""

        days_remaining = None
        if not_after:
            try:
                expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                days_remaining = (expiry - datetime.now(timezone.utc).replace(tzinfo=None)).days
            except ValueError:
                pass

        fingerprint = (
            ":".join(f"{b:02X}" for b in hashlib.sha256(der).digest())
            if der else None
        )

        return {
            "valid": is_valid,
            "subject": subject.get("commonName"),
            "issuer": issuer.get("organizationName"),
            "valid_from": not_before or None,
            "valid_to": not_after or None,
            "days_remaining": days_remaining,
            "fingerprint": fingerprint,
        }
