from datetime import datetime, timezone


def generate_report(tool_name: str, target: str, results: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    findings_html = _build_findings(tool_name, results)
    severity_counts = _count_severities(tool_name, results)
    total = sum(severity_counts.values())
    summary_class = "critical" if severity_counts.get("CRITICAL", 0) else (
        "warning" if severity_counts.get("HIGH", 0) else "ok"
    )

    chart_bars = ""
    colors = {"CRITICAL": "#FF4C4C", "HIGH": "#FF8C00", "MEDIUM": "#F39C12", "LOW": "#3498DB", "INFO": "#6B6B6B"}
    max_count = max(severity_counts.values()) if severity_counts else 1
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        cnt = severity_counts.get(sev, 0)
        pct = (cnt / max_count * 100) if max_count else 0
        chart_bars += (
            f'<div class="bar-row">'
            f'<span class="bar-label">{sev}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{colors[sev]}"></div></div>'
            f'<span class="bar-count">{cnt}</span>'
            f'</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CyberDoc Pro — Отчёт безопасности</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:#0f0f0f;color:#e0e0e0;line-height:1.6;padding:40px}}
.report{{max-width:900px;margin:0 auto;background:#1a1a1a;border-radius:16px;border:1px solid #2a2a2a;overflow:hidden}}
.report-header{{background:linear-gradient(135deg,#1a1a1a 0%,#2a2a2a 100%);padding:40px;border-bottom:2px solid #FFDD2D}}
.logo{{display:flex;align-items:center;gap:12px;margin-bottom:24px}}
.logo-box{{width:40px;height:40px;background:#FFDD2D;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:20px;color:#1a1a1a}}
.logo-text{{font-size:22px;font-weight:700;color:#fff}}
.report-header h1{{font-size:28px;font-weight:700;margin-bottom:8px}}
.meta{{color:#888;font-size:14px}}
.meta span{{color:#FFDD2D;font-weight:500}}
.section{{padding:32px 40px;border-bottom:1px solid #2a2a2a}}
.section:last-child{{border-bottom:none}}
.section h2{{font-size:20px;font-weight:600;margin-bottom:20px;color:#FFDD2D}}
.summary-badge{{display:inline-block;padding:8px 20px;border-radius:20px;font-weight:600;font-size:14px;margin-bottom:16px}}
.summary-badge.critical{{background:rgba(255,76,76,0.15);color:#FF4C4C;border:1px solid rgba(255,76,76,0.3)}}
.summary-badge.warning{{background:rgba(255,140,0,0.15);color:#FF8C00;border:1px solid rgba(255,140,0,0.3)}}
.summary-badge.ok{{background:rgba(46,204,113,0.15);color:#2ECC71;border:1px solid rgba(46,204,113,0.3)}}
.chart{{margin:16px 0}}
.bar-row{{display:flex;align-items:center;gap:12px;margin-bottom:8px}}
.bar-label{{width:80px;font-size:12px;font-weight:600;text-transform:uppercase;color:#888}}
.bar-track{{flex:1;height:20px;background:#222;border-radius:4px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:4px;transition:width 0.3s}}
.bar-count{{width:30px;text-align:right;font-size:14px;font-weight:600}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th{{text-align:left;padding:12px 16px;background:#222;color:#888;font-weight:600;text-transform:uppercase;font-size:12px;letter-spacing:0.5px}}
td{{padding:12px 16px;border-bottom:1px solid #2a2a2a}}
tr:hover td{{background:#222}}
.sev{{padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600;text-transform:uppercase}}
.sev-CRITICAL{{background:rgba(255,76,76,0.15);color:#FF4C4C}}
.sev-HIGH{{background:rgba(255,140,0,0.15);color:#FF8C00}}
.sev-MEDIUM{{background:rgba(243,156,18,0.15);color:#F39C12}}
.sev-LOW{{background:rgba(52,152,219,0.15);color:#3498DB}}
.sev-INFO{{background:rgba(107,107,107,0.15);color:#888}}
.footer{{padding:24px 40px;text-align:center;color:#555;font-size:12px}}
code{{font-family:'JetBrains Mono',monospace;background:#222;padding:2px 6px;border-radius:4px;font-size:12px}}
.close-report{{position:fixed;top:20px;right:20px;width:48px;height:48px;background:#FF4C4C;color:#fff;border:none;border-radius:50%;font-size:24px;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 16px rgba(255,76,76,0.4);transition:transform 0.2s,background 0.2s;z-index:100}}
.close-report:hover{{background:#CC3333;transform:scale(1.1)}}
@media print{{
  .close-report{{display:none}}
  body{{background:#fff;color:#222;padding:20px}}
  .report{{border:none;box-shadow:none}}
  .report-header{{background:#f8f8f8;border-bottom:2px solid #333}}
  .logo-box{{background:#333;color:#fff}}
  .logo-text,.report-header h1{{color:#222}}
  .section h2{{color:#333}}
  th{{background:#eee;color:#333}}
  td{{border-color:#ddd}}
  .bar-track{{background:#eee}}
  .meta{{color:#666}} .meta span{{color:#333}}
}}
</style>
</head>
<body>
<button class="close-report" onclick="window.close()" title="Закрыть отчёт">&times;</button>
<div class="report">
  <div class="report-header">
    <div class="logo"><div class="logo-box">C</div><div class="logo-text">CyberDoc Pro</div></div>
    <h1>Отчёт безопасности</h1>
    <div class="meta">Цель: <span>{_esc(target)}</span> &nbsp;|&nbsp; Инструмент: <span>{_esc(tool_name)}</span> &nbsp;|&nbsp; Дата: <span>{now}</span></div>
  </div>
  <div class="section">
    <h2>Сводка</h2>
    <div class="summary-badge {summary_class}">
      {"Обнаружены критические проблемы" if summary_class == "critical" else "Обнаружены проблемы среднего уровня" if summary_class == "warning" else "Серьёзных проблем не найдено"}
    </div>
    <p>Всего находок: <strong>{total}</strong></p>
    <div class="chart">{chart_bars}</div>
  </div>
  <div class="section">
    <h2>Детализация</h2>
    {findings_html}
  </div>
  <div class="footer">Сгенерировано платформой CyberDoc Pro &copy; {datetime.now().year}</div>
</div>
</body>
</html>"""


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _count_severities(tool_name: str, results: dict) -> dict:
    counts: dict[str, int] = {}
    items = _extract_items(tool_name, results)
    for item in items:
        sev = item.get("severity", "INFO").upper()
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _extract_items(tool_name: str, results: dict) -> list[dict]:
    if tool_name == "page-analyzer":
        vulns = results.get("vulnerabilities", [])
        items = []
        for v in vulns:
            sev = "MEDIUM"
            for tag in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
                if f"[{tag}]" in v:
                    sev = tag
                    break
            items.append({"severity": sev, "detail": v})
        return items
    if tool_name == "port-scanner":
        return [{"severity": "MEDIUM", "detail": f"Port {p['port']} ({p['service']}): {p['status']}"} for p in (results if isinstance(results, list) else [])]
    if tool_name == "dir-scanner":
        return [{"severity": p.get("severity", "INFO"), "detail": f"{p['path']} — HTTP {p['status']}"} for p in results.get("paths", [])]
    if tool_name == "github-scanner":
        return results.get("findings", [])
    if tool_name == "ssl-checker":
        items = []
        if results.get("error"):
            items.append({"severity": "HIGH", "detail": results["error"]})
        elif not results.get("valid"):
            items.append({"severity": "CRITICAL", "detail": "Сертификат невалиден"})
        else:
            days = results.get("days_remaining", 999)
            sev = "CRITICAL" if days < 7 else "HIGH" if days < 30 else "INFO"
            items.append({"severity": sev, "detail": f"Сертификат действителен ещё {days} дн."})
        return items
    if tool_name == "dns-recon":
        sec = results.get("security", {})
        items = []
        if not sec.get("spf"):
            items.append({"severity": "MEDIUM", "detail": "SPF-запись не обнаружена"})
        if not sec.get("dmarc"):
            items.append({"severity": "MEDIUM", "detail": "DMARC-запись не обнаружена"})
        return items
    if tool_name == "subdomain-scanner":
        return [{"severity": "INFO", "detail": f"{s['subdomain']} → {', '.join(s['ips'])}"} for s in results.get("subdomains", [])]
    return []


def _build_findings(tool_name: str, results: dict) -> str:
    items = _extract_items(tool_name, results)
    if not items:
        return "<p>Находок нет.</p>"
    rows = ""
    for i, item in enumerate(items, 1):
        sev = item.get("severity", "INFO").upper()
        detail = _esc(item.get("detail", ""))
        file_info = f'<br><code>{_esc(item["file"])}</code>' if "file" in item else ""
        rows += f'<tr><td>{i}</td><td><span class="sev sev-{sev}">{sev}</span></td><td>{detail}{file_info}</td></tr>'
    return f'<table><thead><tr><th>#</th><th>Уровень</th><th>Описание</th></tr></thead><tbody>{rows}</tbody></table>'
