import os
import uuid
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
)
from reportlab.lib import colors

REPORTS_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "reports"
)
if not os.path.exists(REPORTS_FOLDER):
    os.makedirs(REPORTS_FOLDER)

NAVY = colors.HexColor("#0f172a")
BLUE = colors.HexColor("#2563eb")
SLATE_LIGHT = colors.HexColor("#f1f5f9")
SLATE_TEXT = colors.HexColor("#475569")

RISK_COLORS = {
    "High Risk": colors.HexColor("#dc2626"),
    "Medium Risk": colors.HexColor("#d97706"),
    "Low Risk": colors.HexColor("#059669"),
}


def generate_case_id():
    return "DS-" + datetime.datetime.utcnow().strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:8].upper()


def build_pdf_report(case_id, created_at, combined_result, evidence_details, screenshot_image_path=None):
    filename = f"{case_id}.pdf"
    filepath = os.path.join(REPORTS_FOLDER, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=2.2 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()

    brand_style = ParagraphStyle("Brand", parent=styles["Normal"], fontSize=22, textColor=NAVY,
                                  fontName="Helvetica-Bold", alignment=TA_LEFT)
    tagline_style = ParagraphStyle("Tagline", parent=styles["Normal"], fontSize=10, textColor=SLATE_TEXT,
                                    alignment=TA_LEFT, spaceAfter=4)
    heading_style = ParagraphStyle("HeadingStyle", parent=styles["Heading2"], fontSize=13,
                                    spaceBefore=16, spaceAfter=8, textColor=NAVY)
    normal_style = ParagraphStyle("NormalStyle", parent=styles["Normal"], fontSize=10, leading=15,
                                   textColor=SLATE_TEXT)
    bullet_style = ParagraphStyle("BulletStyle", parent=normal_style, leftIndent=10, spaceAfter=3)

    overall_level = combined_result.get("overall_level", "Low Risk")
    risk_color = RISK_COLORS.get(overall_level, colors.grey)

    elements = []

    # Header brand row
    elements.append(Paragraph("DEEP SHIELD", brand_style))
    elements.append(Paragraph("Multimodal Scam Evidence Analysis Report", tagline_style))
    elements.append(HRFlowable(width="100%", thickness=1.2, color=NAVY, spaceAfter=14))

    # Risk verdict banner
    verdict_table = Table(
        [[Paragraph(f'<b><font size="14" color="white">{overall_level}</font></b>',
                     ParagraphStyle("W", alignment=TA_LEFT)),
          Paragraph(f'<font color="white">Score: {combined_result.get("combined_score", 0)}/100 &nbsp;&nbsp;|&nbsp;&nbsp; Confidence: {combined_result.get("confidence", "N/A")}</font>',
                     ParagraphStyle("W2", alignment=TA_LEFT))]],
        colWidths=[8 * cm, 9 * cm]
    )
    verdict_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), risk_color),
        ("PADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(verdict_table)
    elements.append(Spacer(1, 14))

    # Case info table
    case_info = [
        ["Case ID", case_id],
        ["Date & Time", created_at],
    ]
    case_table = Table(case_info, colWidths=[4.5 * cm, 12.5 * cm])
    case_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), SLATE_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), SLATE_TEXT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(case_table)

    # Analysis Summary
    elements.append(Paragraph("Analysis Summary", heading_style))
    elements.append(Paragraph(combined_result.get("explanation", "No explanation available"), normal_style))

    time_window_findings = combined_result.get("time_window_findings", [])
    if time_window_findings:
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("<b>⚠ Cross-Evidence Inconsistencies Detected</b>", normal_style))
        for finding in time_window_findings:
            elements.append(Paragraph(f"– {finding}", bullet_style))

    # Recommended Actions
    elements.append(Paragraph("Recommended Actions", heading_style))
    for action in combined_result.get("recommended_actions", []):
        elements.append(Paragraph(f"→ {action}", bullet_style))

    # Evidence Breakdown
    elements.append(Paragraph("Evidence Breakdown", heading_style))
    for evidence in evidence_details:
        etype = evidence.get("type", "Evidence")
        score = evidence.get("score", 0)
        reasons = evidence.get("reasons", [])

        timestamp_label = evidence.get("timestamp", "")
        header_right = f"<b>Score: {score}/100</b>"
        if timestamp_label:
            header_right += f"<br/><font size=8>{timestamp_label}</font>"

        ev_header = Table(
            [[Paragraph(f"<b>{etype} Analysis</b>", normal_style),
              Paragraph(header_right, normal_style)]],
            colWidths=[13 * cm, 4 * cm]
        )
        ev_header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SLATE_LIGHT),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(ev_header)
        elements.append(Spacer(1, 4))

        for reason in reasons:
            elements.append(Paragraph(f"– {reason}", bullet_style))

        if "transcript" in evidence:
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(f"<i>Transcript:</i> {evidence['transcript']}", normal_style))
        if "extracted_text" in evidence:
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(f"<i>Extracted Text:</i> {evidence['extracted_text']}", normal_style))

        elements.append(Spacer(1, 12))

    if screenshot_image_path and os.path.exists(screenshot_image_path):
        elements.append(Paragraph("Attached Screenshot Evidence", heading_style))
        try:
            img = RLImage(screenshot_image_path, width=9 * cm, height=None)
            img._restrictSize(9 * cm, 11 * cm)
            elements.append(img)
        except Exception:
            elements.append(Paragraph("(Could not embed image in report)", normal_style))

    elements.append(Spacer(1, 24))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=10))
    elements.append(Paragraph(
        "This report was generated by DeepShield for evidence documentation purposes. "
        "It can be attached to a complaint filed on the National Cyber Crime Reporting Portal "
        "(cybercrime.gov.in) or submitted to your local cybercrime cell.",
        ParagraphStyle("Footer", parent=normal_style, fontSize=8, textColor=colors.grey)
    ))

    doc.build(elements)
    return filepath