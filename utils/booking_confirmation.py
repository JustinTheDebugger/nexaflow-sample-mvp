from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_booking_confirmation_pdf(
    booking,
    samples,
):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "BookingTitle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=4 * mm,
    )

    subtitle_style = ParagraphStyle(
        "BookingSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        spaceAfter=6 * mm,
    )

    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=4 * mm,
        spaceAfter=3 * mm,
    )

    normal_style = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )

    story = []

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "ZEMPIRE SAMPLE BOOKING",
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"Booking {booking['booking_number']}",
            subtitle_style,
        )
    )

    # ---------------------------------------------------------
    # Booking details
    # ---------------------------------------------------------

    booking_data = [
        [
            Paragraph("<b>Required From</b>", normal_style),
            booking["start_date"].strftime("%d %b %Y"),
            Paragraph("<b>Required Until</b>", normal_style),
            booking["end_date"].strftime("%d %b %Y"),
        ],
        [
            Paragraph("<b>Requested By</b>", normal_style),
            booking["booked_by"],
            Paragraph("<b>Department</b>", normal_style),
            booking["team"] or "-",
        ],
        [
            Paragraph("<b>Purpose</b>", normal_style),
            booking["purpose"] or "-",
            Paragraph("<b>Status</b>", normal_style),
            booking["booking_status"],
        ],
    ]

    booking_table = Table(
        booking_data,
        colWidths=[
            30 * mm,
            55 * mm,
            30 * mm,
            55 * mm,
        ],
    )

    booking_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CCCCCC"),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#F2F2F2"),
                ),
                (
                    "BACKGROUND",
                    (2, 0),
                    (2, -1),
                    colors.HexColor("#F2F2F2"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(booking_table)

    # ---------------------------------------------------------
    # Notes
    # ---------------------------------------------------------

    if booking.get("notes"):
        story.append(
            Paragraph(
                "Notes",
                section_style,
            )
        )

        story.append(
            Paragraph(
                booking["notes"],
                normal_style,
            )
        )

    # ---------------------------------------------------------
    # Samples
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            f"Items to Prepare ({len(samples)})",
            section_style,
        )
    )

    sample_rows = [
        [
            "",
            "Sample ID",
            "Sample Name",
            "Location",
        ]
    ]

    for sample in samples:

        location = "-"

        if sample["location_code"]:
            location = sample["location_code"]

            if sample["location_name"]:
                location += (
                    f" - {sample['location_name']}"
                )

        sample_rows.append(
            [
                "☐",
                sample["sample_id"],
                Paragraph(
                    sample["sample_name"],
                    normal_style,
                ),
                Paragraph(
                    location,
                    normal_style,
                ),
            ]
        )

    sample_table = Table(
        sample_rows,
        colWidths=[
            10 * mm,
            28 * mm,
            82 * mm,
            50 * mm,
        ],
        repeatRows=1,
    )

    sample_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAEAEA"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#BBBBBB"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 1),
                    (0, -1),
                    "CENTER",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(sample_table)

    # ---------------------------------------------------------
    # Warehouse preparation
    # ---------------------------------------------------------

    story.append(
        Spacer(
            1,
            10 * mm,
        )
    )

    preparation_data = [
        [
            "Prepared By:",
            "________________________________",
        ],
        [
            "Date:",
            "________________________________",
        ],
    ]

    preparation_table = Table(
        preparation_data,
        colWidths=[
            35 * mm,
            90 * mm,
        ],
    )

    preparation_table.setStyle(
        TableStyle(
            [
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(preparation_table)

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()