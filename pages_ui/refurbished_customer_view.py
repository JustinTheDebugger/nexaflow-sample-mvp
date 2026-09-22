from pathlib import Path

import streamlit as st

from repositories.sample_repository import (
    get_refurbished_customer_media,
    get_refurbished_customer_view,
)


def render_refurbished_customer_view(
    public_token,
):
    """
    Render the customer-safe view of a refurbished item.

    This page intentionally excludes internal issue,
    booking, repair and staff information.
    """

    if not public_token:
        st.error(
            "This refurbished item link is invalid."
        )
        return

    item = get_refurbished_customer_view(
        public_token
    )

    if not item:
        st.error(
            "This refurbished item is not available "
            "for customer viewing."
        )
        return

    photos = get_refurbished_customer_media(
        item["id"]
    )

    # --------------------------------------------------------------
    # Customer page styles
    # --------------------------------------------------------------

    st.markdown(
        """
        <style>

        /* Hide normal Streamlit chrome for customer view. */

        [data-testid="stSidebar"] {
            display: none;
        }

        [data-testid="stHeader"] {
            display: none;
        }

        .block-container {
            max-width: 1000px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        .customer-eyebrow {
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            color: #64748b;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }

        .customer-title {
            font-size: 2rem;
            font-weight: 700;
            color: #17365d;
            line-height: 1.2;
            margin-bottom: 0.35rem;
        }

        .customer-ref {
            font-size: 0.95rem;
            color: #64748b;
            margin-bottom: 1.5rem;
        }

        .customer-summary-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-top: 1rem;
            margin-bottom: 1.5rem;
        }

        .customer-label {
            font-size: 0.78rem;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }

        .customer-grade {
            font-size: 1.25rem;
            font-weight: 700;
            color: #17365d;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------
    # Heading
    # --------------------------------------------------------------

    st.markdown(
        """
        <div class="customer-eyebrow">
            Refurbished Item
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="customer-title">
            {item["sample_name"]}
        </div>

        <div class="customer-ref">
            Refurbished reference:
            {item["refurbished_id"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------
    # Grade
    # --------------------------------------------------------------

    st.markdown(
        f"""
        <div class="customer-summary-card">
            <div class="customer-label">
                Condition
            </div>
            <div class="customer-grade">
                Grade {item["condition_grade"] or "—"}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------
    # Customer description
    # --------------------------------------------------------------

    st.subheader("Refurbishment Summary")

    if item["customer_summary"]:
        st.write(
            item["customer_summary"]
        )
    else:
        st.write(
            "This item has been inspected "
            "following refurbishment."
        )

    # --------------------------------------------------------------
    # Customer-approved photos
    # --------------------------------------------------------------

    if photos:

        st.divider()
        st.subheader("Current Condition")

        columns = st.columns(2)

        for index, photo in enumerate(
            photos
        ):
            with columns[index % 2]:

                storage_path = photo[
                    "storage_path"
                ]

                if (
                    storage_path
                    and Path(storage_path).exists()
                ):
                    st.image(
                        storage_path,
                        width="stretch",
                    )

                    if photo["caption"]:
                        st.caption(
                            photo["caption"]
                        )

    # --------------------------------------------------------------
    # Footer
    # --------------------------------------------------------------

    st.divider()

    st.caption(
        f"Refurbished item reference: "
        f"{item['refurbished_id']}"
    )