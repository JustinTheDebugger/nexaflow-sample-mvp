import html
import os
import resend


# ------------------------------------------------------------
# Email configuration
# ------------------------------------------------------------

RESEND_API_KEY = os.getenv(
    "RESEND_API_KEY"
)

NEXAFLOW_FROM_EMAIL = os.getenv(
    "NEXAFLOW_FROM_EMAIL"
)

if (
    not NEXAFLOW_FROM_EMAIL
    or "@" not in NEXAFLOW_FROM_EMAIL
):
    raise RuntimeError(
        "NEXAFLOW_FROM_EMAIL must contain "
        "a valid sender email address."
    )

PRODUCT_REQUEST_ADMIN_EMAIL = os.getenv(
    "PRODUCT_REQUEST_ADMIN_EMAIL",
    "justin.tys@hotmail.com",
)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _escape(value):
    """
    Safely escape values before inserting them
    into an HTML email.
    """

    if value is None:
        return ""

    return html.escape(
        str(value)
    )


def _format_date(value):
    """
    Format dates for operational emails.
    """

    if not value:
        return ""

    return value.strftime(
        "%d %b %Y"
    )


# ------------------------------------------------------------
# Product Request email
# ------------------------------------------------------------

def send_product_request_notification(
    request_detail,
):
    """
    Send a Product Request notification to
    the configured NexaFlow administrator.

    Email failure is raised to the caller but does
    not affect the already-created database record.
    """

    if not RESEND_API_KEY:
        raise RuntimeError(
            "RESEND_API_KEY is not configured."
        )

    if not NEXAFLOW_FROM_EMAIL:
        raise RuntimeError(
            "NEXAFLOW_FROM_EMAIL is not configured."
        )

    resend.api_key = RESEND_API_KEY

    request = request_detail[
        "request"
    ]

    items = request_detail[
        "items"
    ]

    request_number = request[
        "request_number"
    ]

    # --------------------------------------------------------
    # Product rows
    # --------------------------------------------------------

    product_rows = ""

    for item in items:

        product_rows += f"""
        <tr>
            <td style="
                padding: 10px 12px;
                border-bottom: 1px solid #e5e7eb;
            ">
                <strong>
                    {_escape(item["product_name"])}
                </strong>
                <br>
                <span style="
                    color: #64748b;
                    font-size: 12px;
                ">
                    {_escape(item["product_code"])}
                </span>
            </td>

            <td style="
                padding: 10px 12px;
                border-bottom: 1px solid #e5e7eb;
                text-align: center;
                vertical-align: top;
            ">
                {_escape(item["quantity_required"])}
            </td>
        </tr>
        """

    # --------------------------------------------------------
    # HTML email
    # --------------------------------------------------------

    html_body = f"""
    <html>
    <body style="
        margin: 0;
        padding: 0;
        background: #f8fafc;
        font-family:
            Arial,
            Helvetica,
            sans-serif;
        color: #1e293b;
    ">

        <div style="
            max-width: 680px;
            margin: 24px auto;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
        ">

            <div style="
                padding: 22px 28px;
                background: #17365d;
                color: #ffffff;
            ">
                <div style="
                    font-size: 12px;
                    letter-spacing: 1px;
                    opacity: 0.8;
                ">
                    NEXAFLOW
                </div>

                <div style="
                    font-size: 22px;
                    font-weight: bold;
                    margin-top: 4px;
                ">
                    New Product Sample Request
                </div>
            </div>

            <div style="
                padding: 28px;
            ">

                <p style="
                    margin-top: 0;
                ">
                    A new product sample request has
                    been submitted and is ready for
                    review.
                </p>

                <table style="
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                ">

                    <tr>
                        <td style="
                            padding: 6px 0;
                            color: #64748b;
                            width: 150px;
                        ">
                            Request
                        </td>
                        <td>
                            <strong>
                                {_escape(request_number)}
                            </strong>
                        </td>
                    </tr>

                    <tr>
                        <td style="
                            padding: 6px 0;
                            color: #64748b;
                        ">
                            Status
                        </td>
                        <td>
                            {_escape(
                                request[
                                    "request_status"
                                ]
                            )}
                        </td>
                    </tr>

                    <tr>
                        <td style="
                            padding: 6px 0;
                            color: #64748b;
                        ">
                            Requested by
                        </td>
                        <td>
                            {_escape(
                                request[
                                    "requested_by"
                                ]
                            )}
                        </td>
                    </tr>

                    <tr>
                        <td style="
                            padding: 6px 0;
                            color: #64748b;
                        ">
                            Required from
                        </td>
                        <td>
                            {_format_date(
                                request[
                                    "required_from"
                                ]
                            )}
                        </td>
                    </tr>

                    <tr>
                        <td style="
                            padding: 6px 0;
                            color: #64748b;
                        ">
                            Required until
                        </td>
                        <td>
                            {_format_date(
                                request[
                                    "required_until"
                                ]
                            )}
                        </td>
                    </tr>

                </table>

                <h3 style="
                    color: #17365d;
                    margin-top: 28px;
                ">
                    Products Requested
                </h3>

                <table style="
                    width: 100%;
                    border-collapse: collapse;
                    border: 1px solid #e5e7eb;
                ">

                    <thead>
                        <tr style="
                            background: #f8fafc;
                        ">
                            <th style="
                                padding: 10px 12px;
                                text-align: left;
                            ">
                                Product
                            </th>

                            <th style="
                                padding: 10px 12px;
                                text-align: center;
                                width: 90px;
                            ">
                                Qty
                            </th>
                        </tr>
                    </thead>

                    <tbody>
                        {product_rows}
                    </tbody>

                </table>

                <h3 style="
                    color: #17365d;
                    margin-top: 28px;
                ">
                    Purpose
                </h3>

                <div style="
                    background: #f8fafc;
                    padding: 14px;
                    border-radius: 6px;
                    line-height: 1.5;
                ">
                    {_escape(
                        request["purpose"]
                        or "Not specified"
                    )}
                </div>

                <p style="
                    margin-top: 28px;
                    color: #475569;
                ">
                    Please review this request
                    in NexaFlow.
                </p>

            </div>

            <div style="
                padding: 16px 28px;
                background: #f8fafc;
                color: #94a3b8;
                font-size: 12px;
            ">
                NexaFlow · Product Request Notification
            </div>

        </div>

    </body>
    </html>
    """

    # --------------------------------------------------------
    # Plain-text fallback
    # --------------------------------------------------------

    product_lines = "\n".join(
        (
            f"{item['quantity_required']} × "
            f"{item['product_name']} "
            f"({item['product_code']})"
        )
        for item in items
    )

    text_body = f"""
New Product Sample Request

Request: {request_number}
Status: {request["request_status"]}
Requested by: {request["requested_by"]}
Required: {_format_date(request["required_from"])} - {_format_date(request["required_until"])}

Products Requested
{product_lines}

Purpose
{request["purpose"] or "Not specified"}

Please review this request in NexaFlow.
""".strip()

    # --------------------------------------------------------
    # Send
    # --------------------------------------------------------

    response = resend.Emails.send(
        {
            "from": NEXAFLOW_FROM_EMAIL,
            "to": [
                PRODUCT_REQUEST_ADMIN_EMAIL
            ],
            "subject": (
                "New Product Sample Request — "
                f"{request_number}"
            ),
            "html": html_body,
            "text": text_body,
        }
    )

    return response