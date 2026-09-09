from datetime import date

import streamlit as st

from repositories.sample_repository import (
    approve_sample_request,
    cancel_booking,
    get_bookings,
    get_sample_requests,
    reject_sample_request,
)


def render_sample_booking_management(hero):
    hero(
        "Sample Booking Management",
        (
            "Review upcoming bookings, cancel reservations, "
            "and manage unavailable sample requests."
        ),
    )

    flash = st.session_state.pop(
        "booking_management_flash",
        None,
    )

    if flash:
        if flash["type"] == "success":
            st.success(flash["message"])
        else:
            st.error(flash["message"])

    try:
        bookings = get_bookings()
        sample_requests = get_sample_requests()

    except Exception as exc:
        st.error(
            f"Could not load booking management data: {exc}"
        )
        return

    today = date.today()

    upcoming_bookings = [
        booking
        for booking in bookings
        if booking["end_date"] >= today
        and booking["booking_status"] == "Reserved"
    ]

    booking_history = [
        booking
        for booking in bookings
        if booking["booking_status"] != "Reserved"
        or booking["end_date"] < today
    ]

    pending_requests = [
        request
        for request in sample_requests
        if request["request_status"] == "Pending Review"
    ]

    tabs = st.tabs(
        [
            f"Upcoming Bookings ({len(upcoming_bookings)})",
            f"Sample Requests ({len(pending_requests)})",
            "Booking History",
        ]
    )

    # ---------------------------------------------------------
    # Upcoming Bookings
    # ---------------------------------------------------------

    with tabs[0]:
        if not upcoming_bookings:
            st.info("No upcoming bookings.")

        for booking in upcoming_bookings:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(
                    [2.5, 1.5, 1.5, 1]
                )

                with col1:
                    display_name = booking["sample_name"]

                    if booking["location_code"]:
                        display_name += (
                            f" ({booking['location_code']})"
                        )

                    st.markdown(
                        f"### {display_name}"
                    )

                    st.caption(
                        booking["sample_id"]
                    )

                with col2:
                    st.caption("Booking Dates")

                    st.write(
                        booking["start_date"].strftime(
                            "%d %b %Y"
                        )
                    )

                    st.write(
                        f"to "
                        f"{booking['end_date'].strftime('%d %b %Y')}"
                    )

                with col3:
                    st.caption("Requested By")

                    st.write(
                        booking["booked_by"]
                    )

                    if booking["team"]:
                        st.caption(
                            booking["team"]
                        )

                    st.write(
                        booking["purpose"]
                        or "—"
                    )

                with col4:
                    st.caption("Status")
                    st.write(
                        booking["booking_status"]
                    )

                    if st.button(
                        "Cancel",
                        key=(
                            f"cancel_booking_"
                            f"{booking['id']}"
                        ),
                        width="stretch",
                    ):
                        st.session_state[
                            "cancel_booking_id"
                        ] = booking["id"]

                        st.rerun()

    # ---------------------------------------------------------
    # Cancellation Form
    # ---------------------------------------------------------

    cancel_booking_id = st.session_state.get(
        "cancel_booking_id"
    )

    if cancel_booking_id:
        selected_booking = next(
            (
                booking
                for booking in upcoming_bookings
                if booking["id"]
                == cancel_booking_id
            ),
            None,
        )

        if selected_booking:
            st.divider()

            st.subheader("Cancel Booking")

            st.write(
                selected_booking["sample_name"]
            )

            st.caption(
                selected_booking["sample_id"]
            )

            with st.form(
                "cancel_booking_form"
            ):
                cancelled_by = st.text_input(
                    "Cancelled By *"
                )

                cancellation_reason = st.selectbox(
                    "Reason *",
                    [
                        "Please Select a Reason",
                        "Plan changed",
                        "Event cancelled",
                        "Different sample selected",
                        "No longer required",
                        "Other",
                    ],
                )

                other_reason = ""

                if cancellation_reason == "Other":
                    other_reason = st.text_area(
                        "Other Reason *"
                    )

                col1, col2 = st.columns(2)

                with col1:
                    confirm_cancel = st.form_submit_button(
                        "Confirm Cancellation",
                        type="primary",
                        width="stretch",
                    )

                with col2:
                    close_cancel = st.form_submit_button(
                        "Keep Booking",
                        width="stretch",
                    )

                if close_cancel:
                    st.session_state.pop(
                        "cancel_booking_id",
                        None,
                    )
                    st.rerun()

                if confirm_cancel:
                    if not cancelled_by.strip():
                        st.error(
                            "Please enter who is cancelling "
                            "the booking."
                        )

                    elif (
                        cancellation_reason
                        == "Please Select a Reason"
                    ):
                        st.error(
                            "Please select a cancellation reason."
                        )

                    elif (
                        cancellation_reason == "Other"
                        and not other_reason.strip()
                    ):
                        st.error(
                            "Please enter the cancellation reason."
                        )

                    else:
                        final_reason = (
                            other_reason.strip()
                            if cancellation_reason == "Other"
                            else cancellation_reason
                        )

                        try:
                            cancel_booking(
                                booking_id=cancel_booking_id,
                                cancelled_by=cancelled_by.strip(),
                                reason=final_reason,
                            )

                            st.session_state.pop(
                                "cancel_booking_id",
                                None,
                            )

                            st.session_state[
                                "booking_management_flash"
                            ] = {
                                "type": "success",
                                "message": (
                                    "Booking cancelled successfully."
                                ),
                            }

                            st.rerun()

                        except Exception as exc:
                            st.error(
                                f"Could not cancel booking: {exc}"
                            )

    # ---------------------------------------------------------
    # Sample Requests
    # ---------------------------------------------------------

    with tabs[1]:
        if not pending_requests:
            st.info(
                "No sample requests are waiting for review."
            )

        for request in pending_requests:
            with st.container(border=True):
                product_name = (
                    request["product_name"]
                    or request["requested_sample_name"]
                    or "Unnamed Product"
                )

                st.markdown(
                    f"### {product_name}"
                )

                if request["product_code"]:
                    st.caption(
                        request["product_code"]
                    )

                col1, col2, col3 = st.columns(
                    [1.5, 1.5, 1]
                )

                with col1:
                    st.caption("Required Dates")

                    st.write(
                        request["required_from"].strftime(
                            "%d %b %Y"
                        )
                    )

                    st.write(
                        f"to "
                        f"{request['required_until'].strftime('%d %b %Y')}"
                    )

                with col2:
                    st.caption("Requested By")

                    st.write(
                        request["requested_by"]
                    )

                    if request["team"]:
                        st.caption(
                            request["team"]
                        )

                    st.write(
                        request["requester_email"]
                    )

                with col3:
                    st.caption("Quantity")

                    st.write(
                        request["quantity_required"]
                    )

                    st.caption("Status")

                    st.write(
                        request["request_status"]
                    )

                if request["purpose"]:
                    st.write(
                        f"**Purpose:** {request['purpose']}"
                    )

                if request["request_notes"]:
                    st.write(
                        f"**Notes:** {request['request_notes']}"
                    )

                action_col1, action_col2 = st.columns(2)

                with action_col1:
                    if st.button(
                        "Approve",
                        key=(
                            f"approve_request_"
                            f"{request['id']}"
                        ),
                        type="primary",
                        width="stretch",
                    ):
                        st.session_state[
                            "approve_request_id"
                        ] = request["id"]

                        st.session_state.pop(
                            "reject_request_id",
                            None,
                        )

                        st.rerun()

                with action_col2:
                    if st.button(
                        "Reject",
                        key=(
                            f"reject_request_"
                            f"{request['id']}"
                        ),
                        width="stretch",
                    ):
                        st.session_state[
                            "reject_request_id"
                        ] = request["id"]

                        st.session_state.pop(
                            "approve_request_id",
                            None,
                        )

                        st.rerun()

    # ---------------------------------------------------------
    # Approve Sample Request
    # ---------------------------------------------------------

    approve_request_id = st.session_state.get(
        "approve_request_id"
    )

    if approve_request_id:
        selected_request = next(
            (
                request
                for request in pending_requests
                if request["id"] == approve_request_id
            ),
            None,
        )

        if selected_request:
            st.divider()
            st.subheader("Approve Sample Request")

            st.write(
                selected_request["product_name"]
                or selected_request["requested_sample_name"]
                or "Unnamed Product"
            )

            if selected_request["product_code"]:
                st.caption(
                    selected_request["product_code"]
                )

            with st.form("approve_sample_request_form"):
                reviewed_by = st.text_input(
                    "Reviewed By *"
                )

                operations_email = st.text_input(
                    "Operations Staff Email *"
                )

                manager_notes = st.text_area(
                    "Manager Notes"
                )

                col1, col2 = st.columns(2)

                with col1:
                    confirm_approve = st.form_submit_button(
                        "Confirm Approval",
                        type="primary",
                        width="stretch",
                    )

                with col2:
                    close_approve = st.form_submit_button(
                        "Close",
                        width="stretch",
                    )

                if close_approve:
                    st.session_state.pop(
                        "approve_request_id",
                        None,
                    )
                    st.rerun()

                if confirm_approve:
                    if not reviewed_by.strip():
                        st.error(
                            "Please enter who reviewed the request."
                        )

                    elif not operations_email.strip():
                        st.error(
                            "Please enter the Operations Staff email."
                        )

                    elif "@" not in operations_email:
                        st.error(
                            "Please enter a valid email address."
                        )

                    else:
                        try:
                            approve_sample_request(
                                request_id=approve_request_id,
                                reviewed_by=reviewed_by.strip(),
                                operations_email=operations_email.strip(),
                                manager_notes=manager_notes.strip(),
                            )

                            st.session_state.pop(
                                "approve_request_id",
                                None,
                            )

                            st.session_state[
                                "booking_management_flash"
                            ] = {
                                "type": "success",
                                "message": (
                                    "Sample request approved successfully."
                                ),
                            }

                            st.rerun()

                        except Exception as exc:
                            st.error(
                                f"Could not approve request: {exc}"
                            )

    # ---------------------------------------------------------
    # Reject Sample Request
    # ---------------------------------------------------------

    reject_request_id = st.session_state.get(
        "reject_request_id"
    )

    if reject_request_id:
        selected_request = next(
            (
                request
                for request in pending_requests
                if request["id"] == reject_request_id
            ),
            None,
        )

        if selected_request:
            st.divider()
            st.subheader("Reject Sample Request")

            st.write(
                selected_request["product_name"]
                or selected_request["requested_sample_name"]
                or "Unnamed Product"
            )

            if selected_request["product_code"]:
                st.caption(
                    selected_request["product_code"]
                )

            with st.form("reject_sample_request_form"):
                reviewed_by = st.text_input(
                    "Reviewed By *",
                    key="reject_reviewed_by",
                )

                rejection_reason = st.text_area(
                    "Rejection Reason *"
                )

                col1, col2 = st.columns(2)

                with col1:
                    confirm_reject = st.form_submit_button(
                        "Confirm Rejection",
                        type="primary",
                        width="stretch",
                    )

                with col2:
                    close_reject = st.form_submit_button(
                        "Close",
                        width="stretch",
                    )

                if close_reject:
                    st.session_state.pop(
                        "reject_request_id",
                        None,
                    )
                    st.rerun()

                if confirm_reject:
                    if not reviewed_by.strip():
                        st.error(
                            "Please enter who reviewed the request."
                        )

                    elif not rejection_reason.strip():
                        st.error(
                            "Please enter the rejection reason."
                        )

                    else:
                        try:
                            reject_sample_request(
                                request_id=reject_request_id,
                                reviewed_by=reviewed_by.strip(),
                                rejection_reason=rejection_reason.strip(),
                            )

                            st.session_state.pop(
                                "reject_request_id",
                                None,
                            )

                            st.session_state[
                                "booking_management_flash"
                            ] = {
                                "type": "success",
                                "message": (
                                    "Sample request rejected successfully."
                                ),
                            }

                            st.rerun()

                        except Exception as exc:
                            st.error(
                                f"Could not reject request: {exc}"
                            )

    # ---------------------------------------------------------
    # Booking History
    # ---------------------------------------------------------

    with tabs[2]:
        if not booking_history:
            st.info(
                "No booking history yet."
            )

        for booking in reversed(
            booking_history
        ):
            with st.container(border=True):
                st.write(
                    f"**{booking['sample_name']}**"
                )

                st.caption(
                    booking["sample_id"]
                )

                st.write(
                    (
                        f"{booking['start_date'].strftime('%d %b %Y')}"
                        f" – "
                        f"{booking['end_date'].strftime('%d %b %Y')}"
                    )
                )

                st.write(
                    f"Status: "
                    f"**{booking['booking_status']}**"
                )