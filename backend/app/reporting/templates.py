"""Templates for rendering SOC reports into Markdown and HTML formats (FR-5.3)."""

from backend.app.reporting.models import SOCReportData


def render_markdown_report(report: SOCReportData) -> str:
    """Render SOC assessment report as clean, GitHub-flavored Markdown."""
    mttd_display = f"{report.mean_time_to_detect_seconds} seconds" if report.mean_time_to_detect_seconds is not None else "N/A (No detected techniques)"

    lines = [
        "# Falcon Strike-AI: SOC Adversary Emulation Assessment Report",
        f"**Report ID**: `{report.report_id}`  ",
        f"**Run ID**: `{report.run_id}`  ",
        f"**Campaign ID**: `{report.campaign_id}`  ",
        f"**Target Account**: `{report.target_account_id}`  ",
        f"**Generated At**: `{report.generated_at}`  ",
        "",
        "---",
        "",
        "## 1. Provenance & Integrity Classification",
        "",
        "| Evaluation Domain | Classified Provenance | Verification Guarantee |",
        "| :--- | :--- | :--- |",
        f"| **Environment State** | `{report.environment_provenance}` | Controlled deterministic topology |",
        f"| **Emulation Runtime** | `{report.runner_provenance}` | Bounded, non-destructive behavioral execution |",
        f"| **Detection Source** | `{report.detection_provenance}` | Explicitly labelled sensor/stub attribution |",
        "",
        "> [!IMPORTANT]",
        "> This report explicitly identifies all synthetic data, in-memory simulation, and stub alert sources.",
        "> Synthetic alerts are never claimed to originate from real-world enterprise SIEM or EDR deployments.",
        "",
        "---",
        "",
        "## 2. Executive Summary",
        "",
        report.executive_summary,
        "",
        f"- **Primary Objective**: {report.objective}",
        f"- **Detection Coverage**: **{report.coverage_percentage}%** ({report.detected_count} Detected, {report.partially_detected_count} Partial, {report.missed_count} Missed)",
        f"- **Mean Time to Detect (MTTD)**: **{mttd_display}**",
        "",
        "---",
        "",
        "## 3. Attack Path Narrative & Graph Traversal",
        "",
        report.attack_path_narrative,
        "",
        "### Attack Path Progression",
        "",
        "| Hop # | Source Resource | Relationship / Action | Target Resource |",
        "| :---: | :--- | :--- | :--- |",
    ]

    for hop in report.attack_path_hops:
        hop_num = hop.get("hop_number", 1)
        src = hop.get("source", "Unknown")
        rel = hop.get("relationship", "TRAVERSES")
        tgt = hop.get("target", "Unknown")
        lines.append(f"| {hop_num} | `{src}` | `{rel}` | `{tgt}` |")

    lines.extend([
        "",
        "---",
        "",
        "## 4. MITRE ATT&CK Technique Detection Matrix",
        "",
        "| Technique ID | Name | Tactic | Status | Alerts Matched | Latency (s) |",
        "| :--- | :--- | :--- | :---: | :---: | :---: |",
    ])

    for tech in report.techniques:
        status_badge = f"**{tech.status}**"
        latency_str = f"{tech.detection_latency_seconds}s" if tech.detection_latency_seconds is not None else "—"
        lines.append(
            f"| `{tech.technique_id}` | {tech.technique_name} | {tech.tactic} | {status_badge} | {tech.detection_count} | {latency_str} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 5. Ground-Truth Synthetic Indicators of Compromise (IOCs)",
        "",
        "| IOC Type | Indicator Value | Technique | Benign Marker |",
        "| :--- | :--- | :---: | :---: |",
    ])

    for ioc in report.synthetic_iocs[:15]:
        val_display = ioc.value if len(ioc.value) <= 50 else f"{ioc.value[:47]}..."
        lines.append(f"| `{ioc.ioc_type}` | `{val_display}` | `{ioc.technique_id}` | `{ioc.is_benign_marker}` |")

    lines.extend([
        "",
        "---",
        "",
        "## 6. Defensive Remediation Guidance",
        "",
        "| Priority | Technique | Resource | Action Item |",
        "| :---: | :--- | :--- | :--- |",
    ])

    for rem in report.remediation_recommendations:
        lines.append(
            f"| **{rem.priority}** | `{rem.technique_id}` | `{rem.target_resource_id}` | {rem.recommendation} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 7. Operational Integrity & Verification Audit",
        "",
        f"- **Teardown Baseline Recovery**: `{'PASSED' if report.teardown_verification.get('baseline_verified') else 'FAILED'}`",
        f"- **Actions Cleaned Up**: `{report.teardown_verification.get('actions_succeeded', 0)} / {report.teardown_verification.get('actions_attempted', 0)}`",
        f"- **Audit Hash-Chain Status**: `{'VERIFIED_UNBROKEN' if report.audit_chain_verification.get('is_valid') else 'INTEGRITY_COMPROMISED'}`",
        f"- **Audit Records Sealed**: `{report.audit_chain_verification.get('total_records', 0)}`",
        "",
        "---",
        "",
        "## 8. Limitations & Disclaimers",
        "",
    ])

    for disc in report.limitations_and_disclaimers:
        lines.append(f"- {disc}")

    lines.append("")
    return "\n".join(lines)


def render_html_report(report: SOCReportData) -> str:
    """Render SOC assessment report as standalone styled HTML document."""
    mttd_display = f"{report.mean_time_to_detect_seconds}s" if report.mean_time_to_detect_seconds is not None else "N/A"

    techniques_rows = "".join(
        f"""<tr>
            <td><code>{t.technique_id}</code></td>
            <td>{t.technique_name}</td>
            <td>{t.tactic}</td>
            <td><span class="badge {t.status.lower()}">{t.status}</span></td>
            <td>{t.detection_count}</td>
            <td>{f"{t.detection_latency_seconds}s" if t.detection_latency_seconds is not None else "—"}</td>
        </tr>"""
        for t in report.techniques
    )

    remediation_rows = "".join(
        f"""<tr>
            <td><span class="badge priority-{r.priority.lower()}">{r.priority}</span></td>
            <td><code>{r.technique_id}</code></td>
            <td><code>{r.target_resource_id}</code></td>
            <td>{r.recommendation}</td>
        </tr>"""
        for r in report.remediation_recommendations
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Falcon Strike-AI SOC Report - {report.run_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1f2937; margin: 0; padding: 24px; background: #f9fafb; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: #ffffff; padding: 32px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        h1 {{ color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px; }}
        h2 {{ color: #1f2937; margin-top: 24px; border-bottom: 1px solid #f3f4f6; padding-bottom: 8px; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }}
        .card {{ background: #f3f4f6; padding: 16px; border-radius: 6px; text-align: center; }}
        .card-value {{ font-size: 24px; font-weight: bold; color: #111827; }}
        .card-label {{ font-size: 13px; color: #6b7280; text-transform: uppercase; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px; }}
        th, td {{ padding: 10px 12px; border: 1px solid #e5e7eb; text-align: left; }}
        th {{ background: #f9fafb; font-weight: 600; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .badge.detected {{ background: #def7ec; color: #03543f; }}
        .badge.partially_detected {{ background: #fef08a; color: #713f12; }}
        .badge.missed {{ background: #fde8e8; color: #9b1c1c; }}
        .badge.priority-critical {{ background: #fde8e8; color: #9b1c1c; }}
        .badge.priority-high {{ background: #fed7aa; color: #9a3412; }}
        .badge.priority-medium {{ background: #fef08a; color: #713f12; }}
        code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 3px; font-family: monospace; font-size: 13px; }}
        .provenance-banner {{ background: #eff6ff; border-left: 4px solid #3b82f6; padding: 12px 16px; margin: 16px 0; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Falcon Strike-AI: SOC Emulation Assessment Report</h1>
        <div class="provenance-banner">
            <strong>Provenance Notice:</strong> Environment: <code>{report.environment_provenance}</code> | Runtime: <code>{report.runner_provenance}</code> | Detection: <code>{report.detection_provenance}</code>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-value">{report.coverage_percentage}%</div>
                <div class="card-label">Detection Coverage</div>
            </div>
            <div class="card">
                <div class="card-value">{mttd_display}</div>
                <div class="card-label">Mean Time to Detect</div>
            </div>
            <div class="card">
                <div class="card-value">{report.detected_count} / {report.total_executed_techniques}</div>
                <div class="card-label">Detected Techniques</div>
            </div>
            <div class="card">
                <div class="card-value">{'PASSED' if report.teardown_verification.get('baseline_verified') else 'FAILED'}</div>
                <div class="card-label">Teardown Baseline</div>
            </div>
        </div>

        <h2>Executive Summary</h2>
        <p>{report.executive_summary}</p>

        <h2>ATT&CK Detection Findings</h2>
        <table>
            <thead>
                <tr>
                    <th>Technique ID</th><th>Name</th><th>Tactic</th><th>Status</th><th>Alerts</th><th>Latency</th>
                </tr>
            </thead>
            <tbody>
                {techniques_rows}
            </tbody>
        </table>

        <h2>Remediation Action Items</h2>
        <table>
            <thead>
                <tr>
                    <th>Priority</th><th>Technique</th><th>Resource</th><th>Recommendation</th>
                </tr>
            </thead>
            <tbody>
                {remediation_rows}
            </tbody>
        </table>
    </div>
</body>
</html>"""
    return html
