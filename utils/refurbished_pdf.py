from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


NAVY = colors.HexColor("#17365D")
TEXT = colors.HexColor("#273A67")
MUTED = colors.HexColor("#64748B")
BORDER = colors.HexColor("#E2E8F0")
BACKGROUND = colors.HexColor("#F8FAFC")


def _fit_image(
    image_path,
    *,
    max_width,
    max_height,
):
    """
    Create a proportionally scaled ReportLab image.
    """

    image = Image(
        str(image_path)
    )

    scale = min(
        max_width / image.imageWidth,
        max_height / image.imageHeight,
    )

    image.drawWidth = (
        image.imageWidth * scale
    )

    image.drawHeight = (
        image.imageHeight * scale
    )

    image.hAlign = "CENTER"

    return image


def build_refurbished_customer_pdf(
    *,
    item,
    customer_photos,
):
    """
    Build a professional one-page customer condition
    report for a refurbished item.

    Only customer-approved information is included.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=(
            f"{item['refurbished_id']} "
            "Customer Condition Report"
        ),
    )

    styles = getSampleStyleSheet()

    small_label = ParagraphStyle(
        "SmallLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=MUTED,
        spaceAfter=2,
    )

    report_title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        textColor=NAVY,
    )

    product_name = ParagraphStyle(
        "ProductName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=TEXT,
    )

    reference_style = ParagraphStyle(
        "Reference",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=MUTED,
    )

    grade_style = ParagraphStyle(
        "Grade",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=16,
        textColor=NAVY,
        alignment=TA_RIGHT,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=NAVY,
        spaceAfter=5,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=14,
        textColor=TEXT,
    )

    caption_style = ParagraphStyle(
        "Caption",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=10,
        textColor=MUTED,
        alignment=TA_LEFT,
    )

    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=10,
        textColor=MUTED,
    )

    story = []

    # --------------------------------------------------
    # Report header
    # --------------------------------------------------

    header_left = [
        Paragraph(
            "NEXAFLOW",
            small_label,
        ),
        Paragraph(
            "Customer Condition Report",
            report_title,
        ),
    ]

    header_right = [
        Paragraph(
            "REFURBISHED ITEM",
            small_label,
        ),
        Paragraph(
            item["refurbished_id"],
            grade_style,
        ),
    ]

    header = Table(
        [[header_left, header_right]],
        colWidths=[
            120 * mm,
            58 * mm,
        ],
    )

    header.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, -1),
                    1,
                    NAVY,
                ),
            ]
        )
    )

    story.append(header)
    story.append(Spacer(1, 7 * mm))

    # --------------------------------------------------
    # Product / grade
    # --------------------------------------------------

    product_block = [
        Paragraph(
            item["source_sample_name"],
            product_name,
        ),
        Spacer(1, 1.5 * mm),
        Paragraph(
            (
                "Refurbished reference: "
                f"{item['refurbished_id']}"
            ),
            reference_style,
        ),
    ]

    grade = (
        item["condition_grade"]
        or "-"
    )

    grade_block = [
        Paragraph(
            "CONDITION",
            small_label,
        ),
        Paragraph(
            f"Grade {grade}",
            grade_style,
        ),
    ]

    summary = Table(
        [[product_block, grade_block]],
        colWidths=[
            128 * mm,
            50 * mm,
        ],
    )

    summary.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    BACKGROUND,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER,
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
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    story.append(summary)
    story.append(Spacer(1, 8 * mm))

    # --------------------------------------------------
    # Refurbishment summary
    # --------------------------------------------------

    story.append(
        Paragraph(
            "REFURBISHMENT SUMMARY",
            section_heading,
        )
    )

    customer_summary = (
        item["customer_summary"]
        or (
            "This item has been inspected "
            "following refurbishment."
        )
    )

    summary_box = Table(
        [
            [
                Paragraph(
                    customer_summary,
                    body_style,
                )
            ]
        ],
        colWidths=[
            178 * mm,
        ],
    )

    summary_box.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    BACKGROUND,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
            ]
        )
    )

    story.append(summary_box)
    story.append(Spacer(1, 8 * mm))

    # --------------------------------------------------
    # Current condition photos
    # --------------------------------------------------

    story.append(
        Paragraph(
            "CURRENT CONDITION",
            section_heading,
        )
    )

    valid_photos = []

    for photo in customer_photos:

        storage_path = photo.get(
            "storage_path"
        )

        if (
            storage_path
            and Path(storage_path).exists()
        ):
            valid_photos.append(photo)

    if valid_photos:

        # Keep the customer report compact.
        # Maximum four photos on the one-page report.
        valid_photos = valid_photos[:4]

        photo_cells = []

        for photo in valid_photos:

            image = _fit_image(
                photo["storage_path"],
                max_width=80 * mm,
                max_height=82 * mm,
            )

            cell = [
                image,
            ]

            if photo.get("caption"):
                cell.extend(
                    [
                        Spacer(1, 2 * mm),
                        Paragraph(
                            photo["caption"],
                            caption_style,
                        ),
                    ]
                )

            photo_cells.append(cell)

        rows = []

        for index in range(
            0,
            len(photo_cells),
            2,
        ):
            row = photo_cells[
                index:index + 2
            ]

            if len(row) == 1:
                row.append("")

            rows.append(row)

        photo_table = Table(
            rows,
            colWidths=[
                87 * mm,
                87 * mm,
            ],
            hAlign="CENTER",
        )

        photo_table.setStyle(
            TableStyle(
                [
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(photo_table)

    else:
        story.append(
            Paragraph(
                (
                    "No customer-approved condition "
                    "photos are available."
                ),
                body_style,
            )
        )

    # --------------------------------------------------
    # Footer
    # --------------------------------------------------

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    footer = Table(
        [
            [
                Paragraph(
                    (
                        "Refurbished item "
                        f"{item['refurbished_id']}"
                    ),
                    footer_style,
                ),
                Paragraph(
                    "Customer Condition Report",
                    ParagraphStyle(
                        "FooterRight",
                        parent=footer_style,
                        alignment=TA_RIGHT,
                    ),
                ),
            ]
        ],
        colWidths=[
            89 * mm,
            89 * mm,
        ],
    )

    footer.setStyle(
        TableStyle(
            [
                (
                    "LINEABOVE",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(footer)

    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes