"""
FitLife — Invoice Generator Utility
Generates PDF invoices using ReportLab.
Gracefully handles missing ReportLab.
"""
import logging
import os
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


def generate_invoice_pdf(payment_data: dict) -> dict:
    """
    Generate a PDF invoice from payment data dict.
    Returns {"success": True, "path": "reports/INV-xxx.pdf"} or error.
    payment_data keys: invoice_number, member_name, cnic, email, phone,
                       branch_name, branch_address, plan_name,
                       amount, payment_date, payment_method, status, notes
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                        Paragraph, Spacer, HRFlowable)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT

        inv_num = payment_data.get("invoice_number", "INV-UNKNOWN")
        path = os.path.join(REPORTS_DIR, f"{inv_num}.pdf")

        doc = SimpleDocTemplate(path, pagesize=A4,
                                leftMargin=20*mm, rightMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        brand_blue = colors.HexColor("#0066FF")
        story = []

        # Header
        title_style = ParagraphStyle("title", parent=styles["Title"],
                                     textColor=brand_blue, fontSize=24, spaceAfter=2)
        story.append(Paragraph("FitLife", title_style))
        sub_style = ParagraphStyle("sub", parent=styles["Normal"],
                                   textColor=colors.grey, fontSize=10)
        story.append(Paragraph("Male Fitness Chain ERP", sub_style))
        story.append(HRFlowable(width="100%", thickness=2, color=brand_blue))
        story.append(Spacer(1, 8*mm))

        # Invoice title
        inv_style = ParagraphStyle("inv", parent=styles["Heading1"],
                                   textColor=brand_blue, fontSize=16)
        story.append(Paragraph(f"INVOICE — {inv_num}", inv_style))
        story.append(Spacer(1, 4*mm))

        # Branch + Member info table
        info_data = [
            ["Branch:", payment_data.get("branch_name", "—"),
             "Invoice Date:", str(date.today().strftime("%d/%m/%Y"))],
            ["Address:", payment_data.get("branch_address", "—"),
             "Payment Date:", str(payment_data.get("payment_date", "—"))],
            ["Member:", payment_data.get("member_name", "—"),
             "Method:", payment_data.get("payment_method", "—")],
            ["CNIC:", payment_data.get("cnic", "—"),
             "Status:", payment_data.get("status", "—")],
            ["Plan:", payment_data.get("plan_name", "—"), "", ""],
        ]
        info_table = Table(info_data, colWidths=[35*mm, 65*mm, 35*mm, 45*mm])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN",   (0, 0), (-1, -1), "TOP"),
            ("TEXTCOLOR",(0, 0), (0, -1), brand_blue),
            ("TEXTCOLOR",(2, 0), (2, -1), brand_blue),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 8*mm))

        # Amount table
        amount = payment_data.get("amount", 0)
        amount_data = [
            ["Description", "Amount"],
            [payment_data.get("plan_name", "Gym Membership"), f"Rs. {amount:,.0f}"],
            ["", ""],
            ["TOTAL", f"Rs. {amount:,.0f}"],
        ]
        amt_table = Table(amount_data, colWidths=[130*mm, 40*mm])
        amt_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), brand_blue),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 10),
            ("ALIGN",      (1, 0), (1, -1), "RIGHT"),
            ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F3F4F6")),
            ("LINEBELOW",  (0, -2), (-1, -2), 1, colors.lightgrey),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        story.append(amt_table)
        story.append(Spacer(1, 8*mm))

        # Notes
        if payment_data.get("notes"):
            story.append(Paragraph(f"<b>Notes:</b> {payment_data['notes']}", styles["Normal"]))
            story.append(Spacer(1, 4*mm))

        # Footer
        story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        footer_style = ParagraphStyle("footer", parent=styles["Normal"],
                                      textColor=colors.grey, fontSize=8,
                                      alignment=TA_CENTER)
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(
            "Thank you for choosing FitLife! | fitlife.pk | All amounts in PKR",
            footer_style
        ))

        doc.build(story)
        logger.info(f"Invoice PDF generated: {path}")
        return {"success": True, "path": path}

    except ImportError:
        logger.warning("ReportLab not installed — cannot generate PDF invoice.")
        return {"success": False, "message": "PDF generation requires ReportLab. Run: pip install reportlab"}
    except Exception as e:
        logger.error(f"generate_invoice_pdf error: {e}", exc_info=True)
        return {"success": False, "message": f"PDF generation failed: {e}"}


def generate_member_id_card(member_data: dict) -> dict:
    """Generate a simple member ID card PDF."""
    try:
        from reportlab.lib.pagesizes import landscape
        from reportlab.lib.pagesizes import A6
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        path = os.path.join(REPORTS_DIR,
                            f"ID_{member_data.get('cnic', 'unknown')}.pdf")
        doc = SimpleDocTemplate(path, pagesize=landscape(A6),
                                leftMargin=8*mm, rightMargin=8*mm,
                                topMargin=8*mm, bottomMargin=8*mm)
        styles = getSampleStyleSheet()
        brand_blue = colors.HexColor("#0066FF")
        story = []

        title_style = ParagraphStyle("t", parent=styles["Title"],
                                     textColor=brand_blue, fontSize=16)
        story.append(Paragraph("💪 FitLife — Member ID", title_style))
        story.append(Spacer(1, 3*mm))

        data = [
            ["Name:", member_data.get("full_name", "—")],
            ["CNIC:", member_data.get("cnic", "—")],
            ["Branch:", member_data.get("branch_name", "—")],
            ["Plan:", member_data.get("plan_name", "—")],
            ["Valid Until:", str(member_data.get("expiry_date", "—"))],
            ["Status:", member_data.get("status", "Active")],
        ]
        t = Table(data, colWidths=[25*mm, 80*mm])
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), brand_blue),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t)
        doc.build(story)
        return {"success": True, "path": path}

    except ImportError:
        return {"success": False, "message": "ReportLab required for ID card generation."}
    except Exception as e:
        logger.error(f"generate_member_id_card error: {e}")
        return {"success": False, "message": str(e)}
