import streamlit as st

from repositories.sample_repository import (
    get_sample_request_detail,
    update_sample_request_status,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _format_date(value):
    """Format a date for display."""

    if not value:
        return "—"

    return value.strftime(
        "%d %b %Y"
    )


def _format_datetime(value):
    """Format a timestamp for display."""

    if not value:
        return "—"

    return value.strftime(
        "%d %b %Y · %H:%M"
    )


def _status_icon(status):
    """Return the status indicator."""

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
# Product Request Detail
# ------------------------------------------------------------------

def render_product_request_detail_page(hero):
    """
    Display and review one Product Request.
    """

    request_id = st.session_state.get(
        "selected_product_request_id"
    )

    if not request_id:

        hero(
            "Product Request",
            "No Product Request selected.",
        )

        st.warning(
            "No Product Request has been selected."
        )

        if st.button(
            "← Back to Product Sample Request Listing"
        ):
            st.session_state.pop(
                "workflow_page",
                None,
            )

            st.rerun()

        return

    # --------------------------------------------------------------
    # Load request
    # --------------------------------------------------------------

    detail = get_sample_request_detail(
        request_id
    )

    if not detail:

        hero(
            "Product Request",
            "Product Request not found.",
        )

        st.error(
            "The Product Request could not be found."
        )

        return

    request = detail["request"]
    items = detail["items"]

    status = request[
        "request_status"
    ]

    # --------------------------------------------------------------
    # Hero
    # --------------------------------------------------------------

    hero(
        request["request_number"],
        "Product Sample Request",
    )

    # --------------------------------------------------------------
    # Back
    # --------------------------------------------------------------

    if st.button(
        "← Back to Product Sample Request Listing",
        key="back_product_request_listing",
    ):

        st.session_state.pop(
            "selected_product_request_id",
            None,
        )

        st.session_state.pop(
            "workflow_page",
            None,
        )

        st.rerun()

    # --------------------------------------------------------------
    # Review success message
    # --------------------------------------------------------------

    review_success = st.session_state.pop(
        "product_request_review_success",
        None,
    )

    if review_success:

        st.success(
            (
                f"{request['request_number']} "
                f"{review_success.lower()}."
            )
        )

    # --------------------------------------------------------------
    # Request summary
    # --------------------------------------------------------------

    st.markdown(
        "### Request Summary"
    )

    (
        status_col,
        requester_col,
        submitted_col,
    ) = st.columns(3)

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

    with requester_col:

        st.caption(
            "REQUESTED BY"
        )

        st.markdown(
            f"**{request['requested_by']}**"
        )

    with submitted_col:

        st.caption(
            "SUBMITTED"
        )

        st.markdown(
            _format_datetime(
                request["created_at"]
            )
        )

    st.write("")

    (
        from_col,
        until_col,
        quantity_col,
    ) = st.columns(3)

    with from_col:

        st.caption(
            "REQUIRED FROM"
        )

        st.markdown(
            (
                f"**{_format_date(request['required_from'])}**"
            )
        )

    with until_col:

        st.caption(
            "REQUIRED UNTIL"
        )

        st.markdown(
            (
                f"**{_format_date(request['required_until'])}**"
            )
        )

    total_quantity = sum(
        int(
            item["quantity_required"]
        )
        for item in items
    )

    with quantity_col:

        st.caption(
            "TOTAL QUANTITY"
        )

        st.markdown(
            f"**{total_quantity}**"
        )

    # --------------------------------------------------------------
    # Purpose
    # --------------------------------------------------------------

    st.divider()

    st.markdown(
        "### Purpose"
    )

    if request["purpose"]:
        st.write(
            request["purpose"]
        )
    else:
        st.caption(
            "No purpose provided."
        )

    # --------------------------------------------------------------
    # Requested products
    # --------------------------------------------------------------

    st.divider()

    st.markdown(
        (
            "### Products Requested "
            f"({len(items)})"
        )
    )

    if not items:

        st.warning(
            "No products are recorded against "
            "this request."
        )

    else:

        for item in items:

            with st.container(
                border=True
            ):

                product_col, qty_col = (
                    st.columns(
                        [5, 1]
                    )
                )

                with product_col:

                    st.markdown(
                        (
                            f"**{item['product_name']}**"
                        )
                    )

                    st.caption(
                        item["product_code"]
                    )

                with qty_col:

                    st.caption(
                        "QUANTITY"
                    )

                    st.markdown(
                        (
                            f"**{item['quantity_required']}**"
                        )
                    )

    # --------------------------------------------------------------
    # Existing review result
    # --------------------------------------------------------------

    if status != "Pending Review":

        st.divider()

        st.markdown(
            "### Review"
        )

        review_col1, review_col2 = (
            st.columns(2)
        )

        with review_col1:

            st.caption(
                "REVIEWED BY"
            )

            st.write(
                request["reviewed_by"]
                or "—"
            )

        with review_col2:

            st.caption(
                "REVIEWED"
            )

            st.write(
                _format_datetime(
                    request["reviewed_at"]
                )
            )

        if request["manager_notes"]:

            st.caption(
                "MANAGER NOTES"
            )

            st.write(
                request["manager_notes"]
            )

        if (
            status == "Rejected"
            and request[
                "rejection_reason"
            ]
        ):

            st.caption(
                "REJECTION REASON"
            )

            st.error(
                request[
                    "rejection_reason"
                ]
            )

        return

    
    # --------------------------------------------------------------
    # Pending Review actions
    # --------------------------------------------------------------

    st.divider()

    st.markdown(
        "### Review Request"
    )

    st.caption(
        "Approve the request or reject it with a reason."
    )

    # --------------------------------------------------------------
    # Rejection reason
    # --------------------------------------------------------------

    rejection_reason = st.text_area(
        "Rejection Reason",
        placeholder=(
            "Required only when rejecting "
            "the request."
        ),
        height=90,
        key=(
            f"product_request_rejection_{request_id}"
        ),
    )

    # --------------------------------------------------------------
    # Actions
    # --------------------------------------------------------------

    approve_col, reject_col, _ = st.columns(
        [1.4, 1.4, 3]
    )

    with approve_col:

        approve = st.button(
            "Approve Request",
            type="primary",
            width="stretch",
            key=(
                f"approve_product_request_{request_id}"
            ),
        )

    with reject_col:

        reject = st.button(
            "Reject Request",
            width="stretch",
            key=(
                f"reject_product_request_{request_id}"
            ),
        )

    # --------------------------------------------------------------
    # Approve
    # --------------------------------------------------------------

    if approve:

        try:

            update_sample_request_status(
                request_id=request_id,
                new_status="Approved",
            )

            st.session_state[
                "product_request_review_success"
            ] = "Approved"

            st.rerun()

        except Exception as exc:

            st.error(
                (
                    "Could not approve Product "
                    f"Request: {exc}"
                )
            )

    # --------------------------------------------------------------
    # Reject
    # --------------------------------------------------------------

    if reject:

        if not rejection_reason.strip():

            st.error(
                "Enter a reason for rejecting "
                "this request."
            )

            return

        try:

            update_sample_request_status(
                request_id=request_id,
                new_status="Rejected",
                rejection_reason=(
                    rejection_reason
                ),
            )

            st.session_state[
                "product_request_review_success"
            ] = "Rejected"

            st.rerun()

        except Exception as exc:

            st.error(
                (
                    "Could not reject Product "
                    f"Request: {exc}"
                )
            )

    

    # --------------------------------------------------------------
    # Approval processing
    # --------------------------------------------------------------

    if approve:

        if not reviewed_by.strip():

            st.error(
                "Reviewed By is required."
            )

            return

        try:

            update_sample_request_status(
                request_id=request_id,
                new_status="Approved",
                reviewed_by=(
                    reviewed_by
                ),
                manager_notes=(
                    manager_notes
                ),
            )

            st.session_state[
                "product_request_review_success"
            ] = "Approved"

            st.rerun()

        except Exception as exc:

            st.error(
                (
                    "Could not approve Product "
                    f"Request: {exc}"
                )
            )

    # --------------------------------------------------------------
    # Rejection processing
    # --------------------------------------------------------------

    if reject:

        if not reviewed_by.strip():

            st.error(
                "Reviewed By is required."
            )

            return

        if not rejection_reason.strip():

            st.error(
                (
                    "Rejection Reason is required "
                    "when rejecting a request."
                )
            )

            return

        try:

            update_sample_request_status(
                request_id=request_id,
                new_status="Rejected",
                reviewed_by=(
                    reviewed_by
                ),
                manager_notes=(
                    manager_notes
                ),
                rejection_reason=(
                    rejection_reason
                ),
            )

            st.session_state[
                "product_request_review_success"
            ] = "Rejected"

            st.rerun()

        except Exception as exc:

            st.error(
                (
                    "Could not reject Product "
                    f"Request: {exc}"
                )
            )