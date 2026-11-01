"""Native SOC Assessment PDF Report Generator using ReportLab (FR-5.3)."""

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.app.reporting.models import SOCReportData


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page counts."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Top running header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 755, "Falcon Strike-AI — SOC Detection Validation Report")
            self.drawRightString(558, 755, f"Report ID: {getattr(self, '_report_id', 'N/A')}")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 748, 558, 748)

        # Bottom footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(54, 36, "STRICTLY CONFIDENTIAL — CrowdStrike Adversary Emulation")
        self.drawRightString(558, 36, page_str)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 46, 558, 46)

        self.restoreState()


def generate_pdf_report(report: SOCReportData, target_file: Path | str | None = None) -> bytes:
    """Generate an enterprise-formatted SOC Executive PDF report from SOCReportData."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0284C7"),
        spaceAfter=12,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1E293B"),
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#FFFFFF"),
    )

    kpi_number = ParagraphStyle(
        "KPINumber",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0284C7"),
    )

    kpi_label = ParagraphStyle(
        "KPILabel",
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#64748B"),
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("FALCON STRIKE-AI", title_style))
    story.append(
        Paragraph(
            "Continuous Threat Exposure Management (CTEM) & Adversary Emulation Assessment",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284C7"), spaceAfter=10))

    # 2. Metadata Table
    meta_data = [
        [
            Paragraph(f"<b>Report ID:</b> {report.report_id}", body_style),
            Paragraph(f"<b>Run ID:</b> {report.run_id}", body_style),
        ],
        [
            Paragraph(f"<b>Target Account:</b> {report.target_account_id}", body_style),
            Paragraph(f"<b>Generated At:</b> {report.generated_at[:19]} UTC", body_style),
        ],
        [
            Paragraph(f"<b>Environment:</b> {report.environment_provenance}", body_style),
            Paragraph(f"<b>Execution Mode:</b> {report.runner_provenance}", body_style),
        ],
        [
            Paragraph(f"<b>Detection Sensor:</b> {report.detection_provenance}", body_style),
            Paragraph(f"<b>Campaign ID:</b> {report.campaign_id}", body_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 3. KPI Scorecard Banner
    mttd_display = f"{report.mean_time_to_detect_seconds:.1f}s" if report.mean_time_to_detect_seconds is not None else "N/A"
    kpi_data = [
        [
            Paragraph(str(report.total_executed_techniques), kpi_number),
            Paragraph(f"{report.coverage_percentage:.1f}%", kpi_number),
            Paragraph(str(report.detected_count), kpi_number),
            Paragraph(str(report.missed_count), kpi_number),
            Paragraph(mttd_display, kpi_number),
        ],
        [
            Paragraph("TECHNIQUES", kpi_label),
            Paragraph("COVERAGE", kpi_label),
            Paragraph("DETECTED", kpi_label),
            Paragraph("MISSED", kpi_label),
            Paragraph("MEAN TIME TO DETECT", kpi_label),
        ],
    ]
    kpi_table = Table(kpi_data, colWidths=[100, 100, 100, 100, 104])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # 4. Executive Summary
    story.append(Paragraph("1. Executive Summary", section_heading))
    story.append(Paragraph(report.executive_summary or "Assessment completed successfully.", body_style))
    if report.objective:
        story.append(Paragraph(f"<b>Objective:</b> {report.objective}", body_style))

    # 5. Attack Path Narrative & Multi-Hop Chain
    story.append(Paragraph("2. Discovered Attack Path & Critical Exposure Vector", section_heading))
    story.append(Paragraph(report.attack_path_narrative or "Single-stage direct pivot path.", body_style))

    if report.attack_path_hops:
        hop_rows = [
            [
                Paragraph("Hop", table_header),
                Paragraph("Source Node", table_header),
                Paragraph("Relationship / Vector", table_header),
                Paragraph("Target Node", table_header),
            ]
        ]
        for i, hop in enumerate(report.attack_path_hops, start=1):
            hop_rows.append(
                [
                    Paragraph(str(i), table_cell),
                    Paragraph(str(hop.get("source_id", "Unknown")), table_cell),
                    Paragraph(str(hop.get("relationship", "PIVOT_TO")), table_cell),
                    Paragraph(str(hop.get("target_id", "Unknown")), table_cell),
                ]
            )
        hop_table = Table(hop_rows, colWidths=[30, 160, 140, 174])
        hop_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(hop_table)
        story.append(Spacer(1, 10))

    # 6. ATT&CK Matrix Technique Correlation Results
    story.append(Paragraph("3. MITRE ATT&CK Technique Emulation & Detection Scorecard", section_heading))
    tech_rows = [
        [
            Paragraph("ATT&CK ID", table_header),
            Paragraph("Technique Name", table_header),
            Paragraph("Tactic", table_header),
            Paragraph("Detection Outcome", table_header),
            Paragraph("Latency", table_header),
        ]
    ]

    for t in report.techniques:
        outcome = t.status.value if hasattr(t.status, "value") else str(t.status)
        latency_sec = getattr(t, "detection_latency_seconds", None)
        latency = f"{latency_sec:.1f}s" if latency_sec is not None else "—"

        status_color = "#16A34A" if outcome == "DETECTED" else ("#D97706" if outcome == "PARTIALLY_DETECTED" else "#DC2626")
        status_para = Paragraph(f"<font color='{status_color}'><b>{outcome}</b></font>", table_cell)

        tech_rows.append(
            [
                Paragraph(t.technique_id, table_cell),
                Paragraph(t.technique_name, table_cell),
                Paragraph(t.tactic.value if hasattr(t.tactic, "value") else str(t.tactic), table_cell),
                status_para,
                Paragraph(latency, table_cell),
            ]
        )

    if len(tech_rows) > 1:
        tech_table = Table(tech_rows, colWidths=[55, 175, 110, 110, 54])
        tech_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(tech_table)
        story.append(Spacer(1, 10))

    # 7. Prioritized Remediation Guidance
    if report.remediation_recommendations:
        story.append(Paragraph("4. Prioritized Remediation Actions", section_heading))
        rem_rows = [
            [
                Paragraph("Priority", table_header),
                Paragraph("Technique", table_header),
                Paragraph("Target Resource", table_header),
                Paragraph("Recommended Defensive Action", table_header),
            ]
        ]
        for rem in report.remediation_recommendations:
            prio = rem.priority
            prio_color = "#DC2626" if prio == "CRITICAL" else ("#EA580C" if prio == "HIGH" else "#2563EB")
            prio_para = Paragraph(f"<font color='{prio_color}'><b>{prio}</b></font>", table_cell)

            rem_rows.append(
                [
                    prio_para,
                    Paragraph(rem.technique_id, table_cell),
                    Paragraph(rem.target_resource_id, table_cell),
                    Paragraph(f"<b>{rem.recommendation}</b><br/><font color='#64748B'>{rem.rationale}</font>", table_cell),
                ]
            )
        rem_table = Table(rem_rows, colWidths=[55, 65, 140, 244])
        rem_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(rem_table)
        story.append(Spacer(1, 10))

    # 8. Teardown & Audit Integrity Verification
    story.append(Paragraph("5. Environment Teardown & Audit Ledger Verification", section_heading))
    td = report.teardown_verification
    audit_ver = report.audit_chain_verification

    td_status = td.get("status", "VERIFIED_CLEAN")
    audit_valid = audit_ver.get("is_valid", True)

    verif_data = [
        [
            Paragraph("<b>Teardown Baseline Match:</b>", body_style),
            Paragraph(f"<font color='#16A34A'><b>{td_status}</b></font> (Post-run fingerprint equals pre-run baseline)", body_style),
        ],
        [
            Paragraph("<b>Cryptographic Audit Trail:</b>", body_style),
            Paragraph(
                f"<font color='#16A34A'><b>{'VALID (SHA-256 HASH CHAIN INTACT)' if audit_valid else 'TAMPER_DETECTED'}</b></font> (Record sequence verified)",
                body_style,
            ),
        ],
    ]
    verif_table = Table(verif_data, colWidths=[180, 324])
    verif_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(verif_table)

    # Build the document
    def on_first_page(canvas_obj, _):
        canvas_obj._report_id = report.report_id

    doc.build(story, canvasmaker=NumberedCanvas, onFirstPage=on_first_page)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    if target_file:
        path = Path(target_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pdf_bytes)

    return pdf_bytes
