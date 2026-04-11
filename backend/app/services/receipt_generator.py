import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def generate_receipt(transaction_data: dict, output_folder: str) -> str:
    """
    Generates a PDF receipt for a completed transaction.
    Returns the path to the generated PDF file.
    """

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # File name based on transaction ID and timestamp
    timestamp  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename   = f"receipt_{transaction_data['transaction_id']}_{timestamp}.pdf"
    filepath   = os.path.join(output_folder, filename)

    # Set up the PDF document
    doc    = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    styles  = getSampleStyleSheet()
    story   = []

    # ─── HEADER ──────────────────────────────────────────
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=18,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=2
    )
    story.append(Paragraph("MediScan BD", title_style))
    story.append(Paragraph("Smart Pharmacy Billing System", subtitle_style))
    story.append(Spacer(1, 8*mm))

    # ─── TRANSACTION INFO ────────────────────────────────
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=2
    )
    created_at = transaction_data.get('created_at', str(datetime.datetime.now()))
    story.append(
        Paragraph(f"Transaction ID : #{transaction_data['transaction_id']}", info_style)
    )
    story.append(
        Paragraph(f"Date & Time    : {created_at}", info_style)
    )
    story.append(Spacer(1, 6*mm))

    # ─── ITEMS TABLE ─────────────────────────────────────
    table_data = [
        ["Medicine", "Qty", "Unit Price", "Total"]
    ]

    for item in transaction_data['items']:
        table_data.append([
            item['medicine_name'],
            str(item['quantity']),
            f"৳ {item['unit_price']:.2f}",
            f"৳ {item['total_price']:.2f}"
        ])

    # Add total row
    table_data.append([
        "", "", "TOTAL",
        f"৳ {transaction_data['total_amount']:.2f}"
    ])

    # Table styling
    col_widths = [90*mm, 20*mm, 30*mm, 30*mm]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND',   (0, 0), (-1, 0),  colors.HexColor('#1F3864')),
        ('TEXTCOLOR',    (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',     (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0),  10),
        ('ALIGN',        (0, 0), (-1, 0),  'CENTER'),

        # Data rows
        ('FONTSIZE',     (0, 1), (-1, -2), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2),
         [colors.HexColor('#F5F8FF'), colors.white]),

        # Total row
        ('BACKGROUND',   (0, -1), (-1, -1), colors.HexColor('#DCE6F1')),
        ('FONTNAME',     (2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',     (2, -1), (-1, -1), 10),

        # Alignment
        ('ALIGN',  (1, 1), (1, -1),  'CENTER'),
        ('ALIGN',  (2, 1), (-1, -1), 'RIGHT'),
        ('ALIGN',  (2, -1), (-1, -1), 'RIGHT'),

        # Borders
        ('GRID',         (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW',    (0, 0), (-1, 0),  1,   colors.HexColor('#1F3864')),

        # Padding
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
    ]))

    story.append(table)
    story.append(Spacer(1, 10*mm))

    # ─── FOOTER ──────────────────────────────────────────
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    story.append(
        Paragraph("Thank you for using MediScan BD", footer_style)
    )
    story.append(
        Paragraph(
            "Powered by MediScan BD | Smart Pharmacy System",
            footer_style
        )
    )

    # Build the PDF
    doc.build(story)
    print(f"Receipt generated: {filepath}")
    return filepath