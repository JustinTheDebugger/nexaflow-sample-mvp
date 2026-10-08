from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)


def generate_collection_sheet(booking, items):
    """Generate a printable PDF collection sheet."""

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#17365D")
    styles["Title"].alignment = TA_CENTER

    story = []

    def safe(value):
        return escape(str(value)) if value is not None else ""

    def date_text(value):
        return value.strftime("%d %b %Y") if value else "-"

    story.append(Paragraph("NexaFlow", styles["Title"]))
    story.append(
        Paragraph("SAMPLE COLLECTION SHEET", styles["Heading2"])
    )
    story.append(Spacer(1, 12))

    details = [
        ["Booking", booking["booking_number"]],
        ["Requested by", booking["booked_by"]],
        ["Purpose", booking.get("purpose") or "-"],
        ["Collection date", date_text(booking.get("start_date"))],
        ["Expected return", date_text(booking.get("end_date"))],
    ]

    details_table = Table(
        [
            [
                Paragraph(safe(label), styles["Normal"]),
                Paragraph(safe(value), styles["Normal"]),
            ]
            for label, value in details
        ],
        colWidths=[38 * mm, 130 * mm],
    )

    details_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    story.append(details_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Requested Samples", styles["Heading2"]))

    rows = [["Sample ID", "Sample Name", "Outcome"]]

    supplied_count = 0

    for item in items:
        status = item.get("preparation_status") or "Not Prepared"

        supplied = status in ("Prepared", "Replaced")

        if supplied:
            supplied_count += 1

        outcome = "Supplied" if supplied else "Not Supplied"

        rows.append([
            Paragraph(safe(item["sample_id"]), styles["Normal"]),
            Paragraph(safe(item["sample_name"]), styles["Normal"]),
            Paragraph(outcome, styles["Normal"]),
        ])

    table = Table(
        rows,
        colWidths=[35 * mm, 95 * mm, 38 * mm],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F1F5F9")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.lightgrey),
        ])
    )

    story.append(table)
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            f"<b>{supplied_count} of {len(items)} "
            "requested samples supplied.</b>",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 24))

    story.append(
        Paragraph(
            "I confirm that I have collected the samples "
            "marked as supplied above.",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 30))

    signature = Table(
        [
            ["____________________________", "________________________"],
            ["Collected by / Signature", "Date / Time"],
            ["", ""],
            ["____________________________", ""],
            ["Issued by", ""],
        ],
        colWidths=[90 * mm, 78 * mm],
    )

    signature.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])
    )

    story.append(KeepTogether(signature))

    doc.build(story)

    return buffer.getvalue()