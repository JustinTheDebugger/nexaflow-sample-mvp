import streamlit as st

from repositories.sample_repository import (
    get_refurbished_items,
)


def render_refurbished_items_page(hero):
    """
    Display refurbished inventory converted
    from the Sample Management lifecycle.
    """

    hero(
        "Refurbished Items",
        (
            "Track repaired samples converted "
            "into refurbished inventory."
        ),
    )

    items = get_refurbished_items()

    # -----------------------------------------
    # Summary
    # -----------------------------------------

    available_count = sum(
        1
        for item in items
        if item["refurbished_status"]
        == "Available"
    )

    reserved_count = sum(
        1
        for item in items
        if item["refurbished_status"]
        == "Reserved"
    )

    sold_count = sum(
        1
        for item in items
        if item["refurbished_status"]
        == "Sold"
    )

    written_off_count = sum(
        1
        for item in items
        if item["refurbished_status"]
        == "Written Off"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Available",
        available_count,
    )

    col2.metric(
        "Reserved",
        reserved_count,
    )

    col3.metric(
        "Sold",
        sold_count,
    )

    col4.metric(
        "Written Off",
        written_off_count,
    )

    st.markdown("---")

    # -----------------------------------------
    # Filters
    # -----------------------------------------

    filter_col1, filter_col2 = st.columns(
        [2, 1]
    )

    with filter_col1:
        search_text = st.text_input(
            "Search",
            placeholder=(
                "Search REF ID, sample ID "
                "or sample name"
            ),
        )

    with filter_col2:
        status_filter = st.selectbox(
            "Status",
            options=[
                "All",
                "Available",
                "Reserved",
                "Sold",
                "Written Off",
            ],
        )

    # -----------------------------------------
    # Apply filters
    # -----------------------------------------

    filtered_items = items

    if status_filter != "All":
        filtered_items = [
            item
            for item in filtered_items
            if item["refurbished_status"]
            == status_filter
        ]

    if search_text:
        search_value = (
            search_text.strip().lower()
        )

        filtered_items = [
            item
            for item in filtered_items
            if (
                search_value
                in (
                    item["refurbished_id"]
                    or ""
                ).lower()
                or search_value
                in (
                    item["source_sample_id"]
                    or ""
                ).lower()
                or search_value
                in (
                    item["source_sample_name"]
                    or ""
                ).lower()
            )
        ]

    # -----------------------------------------
    # Inventory
    # -----------------------------------------

    st.subheader(
        f"Inventory ({len(filtered_items)})"
    )

    if not filtered_items:
        st.info(
            "No refurbished items match "
            "the current filters."
        )
        return

    for item in filtered_items:

        converted_date = (
            item["converted_at"].strftime(
                "%d %b %Y"
            )
            if item["converted_at"]
            else "—"
        )

        location = (
            f"{item['location_code']} — "
            f"{item['location_name']}"
            if item["location_code"]
            else "No location"
        )

        left, middle, right = st.columns(
            [3, 2, 1],
            vertical_alignment="top",
        )

        with left:
            st.markdown(
                f"### {item['refurbished_id']}"
            )

            st.write(
                item["source_sample_name"]
            )

            st.caption(
                "Source sample: "
                f"{item['source_sample_id']}"
            )

        with middle:
            st.write(
                f"**Grade:** "
                f"{item['condition_grade'] or '—'}"
            )

            st.write(
                f"**Status:** "
                f"{item['refurbished_status']}"
            )

            st.write(
                f"**Location:** {location}"
            )

            st.caption(
                f"Converted {converted_date} "
                f"by {item['converted_by']}"
            )

        with right:
            if st.button(
                "View",
                key=(
                    "view_refurbished_"
                    f"{item['id']}"
                ),
                width="stretch",
            ):
                st.session_state[
                    "selected_refurbished_item_id"
                ] = item["id"]

                st.session_state[
                    "workflow_page"
                ] = "Refurbished Item Detail"

                st.rerun()

        st.divider()