import streamlit as st

from repositories.sample_repository import (
    get_refurbished_item,
)

def detail_field(
    label,
    value,
):
    """
    Display a consistent label/value pair.
    """

    display_value = (
        value
        if value not in (
            None,
            "",
        )
        else "—"
    )

    st.markdown(
        f"""
        <div class="refurb-field-label">
            {label}
        </div>
        <div class="refurb-field-value">
            {display_value}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_refurbished_item_detail_page(hero):
    """
    Display the details and provenance of one
    refurbished inventory item.
    """

    refurbished_item_id = st.session_state.get(
        "selected_refurbished_item_id"
    )

    if not refurbished_item_id:
        st.warning(
            "No refurbished item has been selected."
        )

        if st.button(
            "Back to Refurbished Items",
            width="content",
        ):
            st.session_state.pop(
                "workflow_page",
                None,
            )
            st.rerun()

        return

    item = get_refurbished_item(
        refurbished_item_id
    )

    if not item:
        st.error(
            "Refurbished item could not be found."
        )
        return

    # -----------------------------------------
    # Hero
    # -----------------------------------------

    hero(
        "Refurbished Item",
        (
            "Refurbished inventory item "
            "and lifecycle provenance."
        ),
    )

    st.markdown(
        """
        <style>
        .refurb-record-id {
            font-size: 1.75rem;
            font-weight: 700;
            color: #17365d;
            margin-bottom: 0.15rem;
        }

        .refurb-record-name {
            font-size: 1.05rem;
            color: #1a65cf;
            margin-bottom: 1.25rem;
        }

        .refurb-summary-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 14px 16px;
            min-height: 92px;
        }

        .refurb-label {
            font-size: 0.78rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 6px;
        }

        .refurb-value {
            font-size: 1rem;
            font-weight: 600;
            color: #273a67;
            line-height: 1.35;
        }

        .refurb-field-label {
            font-size: 0.82rem;
            font-weight: 600;
            color: #64748b;
            margin-bottom: 2px;
        }

        .refurb-field-value {
            font-size: 1rem;
            font-weight: 500;
            color: #273a67;
            margin-bottom: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------
    # Back
    # -----------------------------------------

    if st.button(
        "← Back to Refurbished Items",
        width="content",
    ):
        st.session_state.pop(
            "selected_refurbished_item_id",
            None,
        )
        st.session_state.pop(
            "workflow_page",
            None,
        )
        st.rerun()

    # -----------------------------------------
    # Header
    # -----------------------------------------

    st.markdown(
        f"""
        <div style="
            font-size: 1.75rem;
            font-weight: 700;
            color: #17365d !important;
            line-height: 1.2;
            margin-top: 0.5rem;
            margin-bottom: 0.25rem;
        ">
            {item["refurbished_id"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            f'<div class="refurb-record-name">'
            f'{item["source_sample_name"]}'
            f'</div>'
        ),
        unsafe_allow_html=True,
    )

    location = (
        f"{item['location_code']} — "
        f"{item['location_name']}"
        if item["location_code"]
        else "No location"
    )

    header_col1, header_col2, header_col3 = (
        st.columns([1, 1, 2])
    )

    with header_col1:
        st.markdown(
            f"""
            <div class="refurb-summary-card">
                <div class="refurb-label">
                    Status
                </div>
                <div class="refurb-value">
                    {item["refurbished_status"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with header_col2:
        st.markdown(
            f"""
            <div class="refurb-summary-card">
                <div class="refurb-label">
                    Grade
                </div>
                <div class="refurb-value">
                    {item["condition_grade"] or "—"}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with header_col3:
        st.markdown(
            f"""
            <div class="refurb-summary-card">
                <div class="refurb-label">
                    Location
                </div>
                <div class="refurb-value">
                    {location}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # -----------------------------------------
    # Original Sample
    # -----------------------------------------

    st.subheader("Original Sample")

    sample_col1, sample_col2 = st.columns(2)

    with sample_col1:
        st.markdown("**Sample ID**")
        st.write(
            item["source_sample_id"]
        )

    with sample_col2:
        st.markdown("**Sample Name**")
        st.write(
            item["source_sample_name"]
        )

    st.divider()

    # -----------------------------------------
    # Conversion
    # -----------------------------------------

    st.subheader("Conversion")

    converted_date = (
        item["converted_at"].strftime(
            "%d %b %Y"
        )
        if item["converted_at"]
        else "—"
    )

    conversion_col1, conversion_col2 = (
        st.columns(2)
    )

    with conversion_col1:
        detail_field(
            "Converted On",
            converted_date,
        )

    with conversion_col2:
        detail_field(
            "Converted By",
            item["converted_by"],
        )

    detail_field(
        "Conversion Notes",
        item["conversion_notes"],
    )

    st.divider()

    # -----------------------------------------
    # Repair Provenance
    # -----------------------------------------

    st.subheader("Repair Provenance")

    if item["repair_id"]:

        repair_started = (
            item["repair_started_at"].strftime(
                "%d %b %Y"
            )
            if item["repair_started_at"]
            else "—"
        )

        repair_completed = (
            item["repair_completed_at"].strftime(
                "%d %b %Y"
            )
            if item["repair_completed_at"]
            else "—"
        )

        repair_col1, repair_col2 = st.columns(2)

        with repair_col1:
            detail_field(
                "Original Issue",
                item["issue_type"],
            )

            detail_field(
                "Issue Description",
                item["issue_description"],
            )

        with repair_col2:
            detail_field(
                "Repair Started",
                repair_started,
            )

            detail_field(
                "Repair Completed",
                repair_completed,
            )

        detail_field(
            "Repair Arranged By",
            item["repair_started_by"],
        )

        detail_field(
            "Repair Notes",
            item["repair_notes"],
        )

        detail_field(
            "Repair Completion Notes",
            item["repair_completion_notes"],
        )

        detail_field(
            "Completion Recorded By",
            item["repair_completed_by"],
        )

    else:
        st.info(
            "No linked repair record was found."
        )

    st.divider()

    # -----------------------------------------
    # Commercial
    # -----------------------------------------

    st.subheader("Commercial")

    commercial_col1, commercial_col2 = (
        st.columns(2)
    )

    sale_price = (
        f"${item['sale_price']:,.2f}"
        if item["sale_price"] is not None
        else "Not set"
    )

    with commercial_col1:
        detail_field(
            "Sale Price",
            sale_price,
        )

    with commercial_col2:
        detail_field(
            "Inventory Status",
            item["refurbished_status"],
        )

    st.caption(
        "Commercial actions will be added "
        "after the inventory detail workflow "
        "has been verified."
    )