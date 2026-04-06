import re
import logging
import httpx

logger = logging.getLogger(__name__)

OSV_API = "https://api.osv.dev/v1/query"


def _parse_requirements(text: str) -> list[dict]:
    """Parse requirements.txt / Pipfile / pyproject.toml style deps."""
    packages = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        m = re.match(r"^([A-Za-z0-9_\-\.]+)\s*[=<>~!]=?\s*([0-9][0-9A-Za-z\.\-\*]*)", line)
        if m:
            packages.append({"name": m.group(1).lower(), "version": m.group(2), "ecosystem": "PyPI"})
        else:
            name_only = re.match(r"^([A-Za-z0-9_\-\.]+)\s*$", line)
            if name_only:
                packages.append({"name": name_only.group(1).lower(), "version": "", "ecosystem": "PyPI"})
    return packages


def _parse_package_json(text: str) -> list[dict]:
    """Parse package.json dependencies."""
    import json
    packages = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return packages
    for section in ("dependencies", "devDependencies"):
        deps = data.get(section, {})
        if isinstance(deps, dict):
            for name, ver in deps.items():
                clean = re.sub(r"^[\^~>=<]*", "", str(ver))
                packages.append({"name": name.lower(), "version": clean, "ecosystem": "npm"})
    return packages


def _parse_gomod(text: str) -> list[dict]:
    packages = []
    for line in text.strip().splitlines():
        m = re.match(r"^\s+(\S+)\s+(v[0-9][0-9A-Za-z\.\-]*)", line)
        if m:
            packages.append({"name": m.group(1), "version": m.group(2).lstrip("v"), "ecosystem": "Go"})
    return packages


def detect_and_parse(content: str) -> tuple[str, list[dict]]:
    stripped = content.strip()
    if stripped.startswith("{"):
        return "package.json", _parse_package_json(stripped)
    if "require (" in stripped or "require(" in stripped:
        return "go.mod", _parse_gomod(stripped)
    return "requirements.txt", _parse_requirements(stripped)


async def scan_dependencies(content: str) -> dict:
    file_type, packages = detect_and_parse(content)
    if not packages:
        return {
            "file_type": file_type,
            "total_packages": 0,
            "vulnerabilities": [],
            "summary": "Не удалось распознать зависимости. Поддерживаются: requirements.txt, package.json, go.mod.",
        }

    vulns = []
    async with httpx.AsyncClient(timeout=20.0, verify=False, trust_env=False) as client:
        for pkg in packages:
            if not pkg["version"]:
                continue
            try:
                payload = {
                    "package": {
                        "name": pkg["name"],
                        "ecosystem": pkg["ecosystem"],
                    },
                    "version": pkg["version"],
                }
                resp = await client.post(OSV_API, json=payload)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                osv_vulns = data.get("vulns", [])
                for v in osv_vulns:
                    severity = "MEDIUM"
                    severities = v.get("database_specific", {}).get("severity", "")
                    if isinstance(severities, str):
                        s_upper = severities.upper()
                        if "CRITICAL" in s_upper:
                            severity = "CRITICAL"
                        elif "HIGH" in s_upper:
                            severity = "HIGH"
                        elif "LOW" in s_upper:
                            severity = "LOW"

                    for sev_entry in v.get("severity", []):
                        score_str = sev_entry.get("score", "")
                        if "CVSS" in sev_entry.get("type", ""):
                            try:
                                base = float(score_str.split("/")[0].split(":")[-1])
                                if base >= 9.0:
                                    severity = "CRITICAL"
                                elif base >= 7.0:
                                    severity = "HIGH"
                                elif base >= 4.0:
                                    severity = "MEDIUM"
                                else:
                                    severity = "LOW"
                            except (ValueError, IndexError):
                                pass

                    fix_version = ""
                    for affected in v.get("affected", []):
                        for r in affected.get("ranges", []):
                            for evt in r.get("events", []):
                                if "fixed" in evt:
                                    fix_version = evt["fixed"]
                                    break

                    vulns.append({
                        "package": pkg["name"],
                        "installed_version": pkg["version"],
                        "vulnerability_id": v.get("id", "N/A"),
                        "aliases": v.get("aliases", []),
                        "summary": v.get("summary", v.get("details", "")[:200]),
                        "severity": severity,
                        "fix_version": fix_version,
                    })
            except Exception as exc:
                logger.warning("OSV query failed for %s: %s", pkg["name"], exc)

    summary_parts = []
    sev_counts = {}
    for vv in vulns:
        sev_counts[vv["severity"]] = sev_counts.get(vv["severity"], 0) + 1
    if not vulns:
        summary_parts.append("Известных уязвимостей не обнаружено.")
    else:
        summary_parts.append(f"Обнаружено {len(vulns)} уязвимостей в {len(set(v['package'] for v in vulns))} пакетах.")
        for s in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            if sev_counts.get(s):
                summary_parts.append(f"  {s}: {sev_counts[s]}")

    return {
        "file_type": file_type,
        "total_packages": len(packages),
        "scanned_packages": len([p for p in packages if p["version"]]),
        "vulnerabilities_count": len(vulns),
        "vulnerabilities": vulns,
        "summary": "\n".join(summary_parts),
    }
