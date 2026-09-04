from io import BytesIO
import os

import qrcode


def build_sample_qr(sample_id: str) -> tuple[bytes, str]:
    base_url = os.environ.get(
        "APP_BASE_URL",
        "http://localhost:8501",
    ).rstrip("/")

    qr_url = (
        f"{base_url}"
        f"?page=qr"
        f"&sample_id={sample_id}"
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(qr_url)
    qr.make(fit=True)

    image = qr.make_image()

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return buffer.getvalue(), qr_url