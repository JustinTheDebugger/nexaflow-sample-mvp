from io import BytesIO

from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


TAG_WIDTH = 6 * cm
TAG_HEIGHT = 4 * cm


def split_sample_name(sample_name: str) -> tuple[str, str]:
    """
    Example:

    Test Eco Cupboard - 2026 Test Sample - 03

    becomes:

    Test Eco Cupboard
    2026 Test Sample - 03
    """

    if " - " in sample_name:
        parts = sample_name.split(" - ", 1)

        return (
            parts[0].strip(),
            parts[1].strip(),
        )

    return sample_name, ""


def fit_text(
    pdf,
    text,
    font_name,
    max_font_size,
    min_font_size,
    max_width,
):
    font_size = max_font_size

    while font_size > min_font_size:
        text_width = pdf.stringWidth(
            text,
            font_name,
            font_size,
        )

        if text_width <= max_width:
            break

        font_size -= 0.5

    return font_size


def draw_warehouse_tag(
    pdf,
    *,
    sample_id: str,
    sample_name: str,
    location_name: str,
    qr_bytes: bytes,
):
    centre_x = TAG_WIDTH / 2
    max_text_width = 5.4 * cm

    # ---------------------------------------------------------
    # Sample name
    # ---------------------------------------------------------

    line_1, line_2 = split_sample_name(
        sample_name
    )

    line_1_font = fit_text(
        pdf,
        line_1,
        "Helvetica-Bold",
        9,
        6,
        max_text_width,
    )

    pdf.setFont(
        "Helvetica-Bold",
        line_1_font,
    )

    pdf.drawCentredString(
        centre_x,
        3.55 * cm,
        line_1,
    )

    if line_2:
        line_2_font = fit_text(
            pdf,
            line_2,
            "Helvetica-Bold",
            8,
            6,
            max_text_width,
        )

        pdf.setFont(
            "Helvetica-Bold",
            line_2_font,
        )

        pdf.drawCentredString(
            centre_x,
            3.15 * cm,
            line_2,
        )

    # ---------------------------------------------------------
    # Location
    # ---------------------------------------------------------

    location_font = fit_text(
        pdf,
        location_name,
        "Helvetica",
        7,
        5.5,
        max_text_width,
    )

    pdf.setFont(
        "Helvetica",
        location_font,
    )

    pdf.drawCentredString(
        centre_x,
        2.72 * cm,
        location_name,
    )

    # ---------------------------------------------------------
    # QR
    # ---------------------------------------------------------

    qr_image = ImageReader(
        BytesIO(qr_bytes)
    )

    qr_size = 1.55 * cm

    qr_x = (
        TAG_WIDTH - qr_size
    ) / 2

    qr_y = 0.95 * cm

    pdf.drawImage(
        qr_image,
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        preserveAspectRatio=True,
        mask="auto",
    )

    # ---------------------------------------------------------
    # Sample ID
    # ---------------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        6.5,
    )

    pdf.drawCentredString(
        centre_x,
        0.68 * cm,
        sample_id,
    )

    # ---------------------------------------------------------
    # Footer
    # ---------------------------------------------------------

    pdf.setFont(
        "Helvetica",
        5.5,
    )

    pdf.drawCentredString(
        centre_x,
        0.25 * cm,
        "Zempire Sample Asset",
    )


def build_warehouse_tag(
    *,
    sample_id: str,
    sample_name: str,
    location_name: str,
    qr_bytes: bytes,
) -> bytes:
    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=(
            TAG_WIDTH,
            TAG_HEIGHT,
        ),
    )

    draw_warehouse_tag(
        pdf,
        sample_id=sample_id,
        sample_name=sample_name,
        location_name=location_name,
        qr_bytes=qr_bytes,
    )

    pdf.showPage()
    pdf.save()

    return buffer.getvalue()


def build_warehouse_tag_bundle(
    samples: list[dict],
) -> bytes:
    """
    Generate one PDF containing multiple 6 x 4 cm tags.

    Each sample becomes one PDF page.
    """

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=(
            TAG_WIDTH,
            TAG_HEIGHT,
        ),
    )

    for sample in samples:
        draw_warehouse_tag(
            pdf,
            sample_id=sample["sample_id"],
            sample_name=sample["sample_name"],
            location_name=sample["location_name"],
            qr_bytes=sample["qr_bytes"],
        )

        pdf.showPage()

    pdf.save()

    return buffer.getvalue()