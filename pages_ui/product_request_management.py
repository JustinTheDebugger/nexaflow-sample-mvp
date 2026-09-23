import streamlit as st

from repositories.sample_repository import (
    get_sample_requests,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _format_date(value):
    """Format dates for display."""

    if not value:
        return "—"

    return value.strftime(
        "%d %b %Y"
    )


def _status_icon(status):
    """Return a simple status indicator."""

    icons = {
        "Pending Review": "🟠",
        "Approved": "🟢",
        "Rejected": "🔴",
        "Cancelled": "⚪",
    }

    return icons.get(
        status,
        "⚪",
    )


# ------------------------------------------------------------------
# Product Sample Request Listing
# ------------------------------------------------------------------

def render_product_request_management_page(hero):
    """
    Display Product Sample Requests for
    Operations / Admin review.
    """

    hero(
        "Product Sample Request Listing",
        (
            "Review and manage product sample "
            "requests submitted to Operations."
        ),
    )

    # --------------------------------------------------------------
    # Status filter
    # --------------------------------------------------------------

    filter_col, _ = st.columns(
        [2, 5]
    )

    with filter_col:

        status_filter = st.selectbox(
            "Status",
            options=[
                "All",
                "Pending Review",
                "Approved",
                "Rejected",
                "Cancelled",
            ],
            key=(
                "product_request_status_filter"
            ),
        )

    selected_status = (
        None
        if status_filter == "All"
        else status_filter
    )

    # --------------------------------------------------------------
    # Load requests
    # --------------------------------------------------------------

    requests = get_sample_requests(
        status=selected_status
    )

    if not requests:

        st.info(
            "No Product Sample Requests found."
        )
        return

    # --------------------------------------------------------------
    # Summary
    # --------------------------------------------------------------

    total_requests = len(
        requests
    )

    pending_count = sum(
        1
        for request in requests
        if request["request_status"]
        == "Pending Review"
    )

    total_products = sum(
        int(
            request["product_count"]
            or 0
        )
        for request in requests
    )

    metric1, metric2, metric3 = st.columns(
        3
    )

    with metric1:

        st.metric(
            "Requests",
            total_requests,
        )

    with metric2:

        st.metric(
            "Pending Review",
            pending_count,
        )

    with metric3:

        st.metric(
            "Products",
            total_products,
        )

    st.divider()

    # --------------------------------------------------------------
    # Request cards
    # --------------------------------------------------------------

    for request in requests:

        status = request[
            "request_status"
        ]

        with st.container(
            border=True
        ):

            (
                request_col,
                dates_col,
                products_col,
                status_col,
                action_col,
            ) = st.columns(
                [2.2, 2.4, 1.3, 1.8, 1.2]
            )

            # ------------------------------------------------------
            # Request number / requester
            # ------------------------------------------------------

            with request_col:

                st.markdown(
                    (
                        f"### "
                        f"{request['request_number']}"
                    )
                )

                st.caption(
                    (
                        "Requested by "
                        f"{request['requested_by']}"
                    )
                )

            # ------------------------------------------------------
            # Required dates
            # ------------------------------------------------------

            with dates_col:

                st.caption(
                    "REQUIRED"
                )

                st.markdown(
                    (
                        f"{_format_date(request['required_from'])}"
                        " → "
                        f"{_format_date(request['required_until'])}"
                    )
                )

            # ------------------------------------------------------
            # Products
            # ------------------------------------------------------

            with products_col:

                st.caption(
                    "PRODUCTS"
                )

                st.markdown(
                    (
                        f"**{request['product_count']}** "
                        "product(s)"
                    )
                )

                st.caption(
                    (
                        f"{request['total_quantity']} "
                        "unit(s)"
                    )
                )

            # ------------------------------------------------------
            # Status
            # ------------------------------------------------------

            with status_col:

                st.caption(
                    "STATUS"
                )

                st.markdown(
                    (
                        f"{_status_icon(status)} "
                        f"**{status}**"
                    )
                )

            # ------------------------------------------------------
            # View action
            # ------------------------------------------------------

            with action_col:

                st.write("")

                if st.button(
                    "View",
                    key=(
                        "view_product_request_"
                        f"{request['id']}"
                    ),
                    width="stretch",
                ):

                    st.session_state[
                        "selected_product_request_id"
                    ] = request["id"]

                    st.session_state[
                        "workflow_page"
                    ] = (
                        "Product Request Detail"
                    )

                    st.rerun()

            # ------------------------------------------------------
            # Purpose
            # ------------------------------------------------------

            if request["purpose"]:

                st.caption(
                    "PURPOSE"
                )

                st.write(
                    request["purpose"]
                )