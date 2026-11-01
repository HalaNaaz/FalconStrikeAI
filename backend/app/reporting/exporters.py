"""Exporters serializing SOC reports into JSON, Markdown, and HTML artifacts (FR-5.3)."""

from pathlib import Path

from backend.app.core.logging import logger
from backend.app.reporting.models import SOCReportData
from backend.app.reporting.templates import render_html_report, render_markdown_report


class ReportExporter:
    """Exports structured SOC reports to JSON, Markdown, and HTML formats."""

    @staticmethod
    def export_json(report: SOCReportData, file_path: Path | str | None = None) -> str:
        """Serialize SOC report to formatted JSON string and optionally save to disk."""
        json_output = report.model_dump_json(indent=2)
        if file_path:
            target = Path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json_output, encoding="utf-8")
            logger.info(f"Saved SOC JSON report to {target}")
        return json_output

    @staticmethod
    def export_markdown(report: SOCReportData, file_path: Path | str | None = None) -> str:
        """Render SOC report as Markdown string and optionally save to disk."""
        md_output = render_markdown_report(report)
        if file_path:
            target = Path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(md_output, encoding="utf-8")
            logger.info(f"Saved SOC Markdown report to {target}")
        return md_output

    @staticmethod
    def export_html(report: SOCReportData, file_path: Path | str | None = None) -> str:
        """Render SOC report as standalone HTML and optionally save to disk."""
        html_output = render_html_report(report)
        if file_path:
            target = Path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html_output, encoding="utf-8")
            logger.info(f"Saved SOC HTML report to {target}")
        return html_output

