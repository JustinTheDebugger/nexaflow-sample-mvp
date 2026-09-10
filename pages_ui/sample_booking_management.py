from datetime import date

import streamlit as st

from repositories.sample_repository import (
    approve_sample_request,
    cancel_booking,
    get_booking_group_details,
    get_booking_groups,
    get_sample_requests,
    reject_sample_request,
)

from utils.booking_confirmation import (
    generate_booking_confirmation_pdf,
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
        sample_requests = get_sample_requests()

    except Exception as exc:
        st.error(
            f"Could not load booking management data: {exc}"
        )
        return

    today = date.today()

    try:
        booking_history = get_booking_groups()

    except Exception as exc:
        st.error(
            f"Could not load booking history: {exc}"
        )
        booking_history = []


    upcoming_bookings = get_booking_groups(
        status="Reserved",
    )

    historical_bookings = [
        booking
        for booking in booking_history
        if booking["booking_status"]
        in (
            "Cancelled",
            "Completed",
        )
    ]

    booking_history = get_booking_groups()

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

        try:
            upcoming_bookings = get_booking_groups(
                status="Reserved",
            )
        except Exception as exc:
            st.error(
                f"Could not load upcoming bookings: {exc}"
            )
            upcoming_bookings = []

        st.subheader(
            f"Upcoming Bookings "
            f"({len(upcoming_bookings)})"
        )

        if not upcoming_bookings:
            st.info(
                "There are no upcoming bookings."
            )

        else:
            for booking in upcoming_bookings:

                with st.container(border=True):

                    col1, col2, col3, col4, col5 = st.columns(
                        [1.4, 2.4, 1.7, 0.8, 1.2]
                    )

                    # -----------------------------------------------------
                    # Booking number / requester
                    # -----------------------------------------------------

                    with col1:

                        st.write(
                            f"**{booking['booking_number']}**"
                        )

                        st.caption(
                            booking["booked_by"]
                        )

                    # -----------------------------------------------------
                    # Dates / purpose
                    # -----------------------------------------------------

                    with col2:

                        st.write(
                            (
                                f"{booking['start_date']:%d %b %Y}"
                                f" → "
                                f"{booking['end_date']:%d %b %Y}"
                            )
                        )

                        st.caption(
                            booking["purpose"]
                            or "No purpose"
                        )

                    # -----------------------------------------------------
                    # Sample count / department
                    # -----------------------------------------------------

                    with col3:

                        sample_count = booking[
                            "sample_count"
                        ]

                        st.write(
                            (
                                f"**{sample_count} "
                                f"sample"
                                f"{'s' if sample_count != 1 else ''}**"
                            )
                        )

                        st.caption(
                            booking["team"]
                            or "No department"
                        )

                    # -----------------------------------------------------
                    # View
                    # -----------------------------------------------------

                    with col4:

                        if st.button(
                            "View",
                            key=(
                                f"view_booking_"
                                f"{booking['booking_group_id']}"
                            ),
                            width="stretch",
                        ):

                            st.session_state[
                                "selected_booking_group_id"
                            ] = booking[
                                "booking_group_id"
                            ]

                            st.rerun()

                    # -----------------------------------------------------
                    # Print / Download PDF
                    # -----------------------------------------------------

                    with col5:

                        try:
                            print_details = (
                                get_booking_group_details(
                                    booking[
                                        "booking_group_id"
                                    ]
                                )
                            )

                            if print_details:

                                pdf_bytes = (
                                    generate_booking_confirmation_pdf(
                                        print_details["booking"],
                                        print_details["samples"],
                                    )
                                )

                                st.download_button(
                                    "Print PDF",
                                    data=pdf_bytes,
                                    file_name=(
                                        f"{booking['booking_number']}_"
                                        f"Booking_Confirmation.pdf"
                                    ),
                                    mime="application/pdf",
                                    key=(
                                        f"print_booking_row_"
                                        f"{booking['booking_group_id']}"
                                    ),
                                    width="stretch",
                                )

                        except Exception as exc:

                            st.button(
                                "Print PDF",
                                disabled=True,
                                key=(
                                    f"print_booking_error_"
                                    f"{booking['booking_group_id']}"
                                ),
                                help=(
                                    f"Could not generate PDF: {exc}"
                                ),
                                width="stretch",
                            )

        selected_booking_group_id = (
            st.session_state.get(
                "selected_booking_group_id"
            )
        )

        if selected_booking_group_id:

            st.divider()

            try:
                booking_details = (
                    get_booking_group_details(
                        selected_booking_group_id
                    )
                )
            except Exception as exc:
                st.error(
                    f"Could not load booking details: {exc}"
                )
                booking_details = None

            if booking_details:

                booking = booking_details[
                    "booking"
                ]

                samples = booking_details[
                    "samples"
                ]

                col1, col2 = st.columns(
                    [4, 1]
                )

                with col1:
                    st.subheader(
                        booking["booking_number"]
                    )

                with col2:
                    if st.button(
                        "Close",
                        key="close_booking_details",
                        width="stretch",
                    ):
                        st.session_state.pop(
                            "selected_booking_group_id",
                            None,
                        )

                        st.rerun()

                info1, info2, info3 = st.columns(3)

                with info1:
                    st.caption("Requested By")
                    st.write(
                        booking["booked_by"]
                    )

                    st.caption("Department")
                    st.write(
                        booking["team"]
                        or "—"
                    )

                with info2:
                    st.caption("Required From")
                    st.write(
                        booking[
                            "start_date"
                        ].strftime(
                            "%d %b %Y"
                        )
                    )

                    st.caption("Required Until")
                    st.write(
                        booking[
                            "end_date"
                        ].strftime(
                            "%d %b %Y"
                        )
                    )

                with info3:
                    st.caption("Purpose")
                    st.write(
                        booking["purpose"]
                        or "—"
                    )

                    st.caption("Status")
                    st.write(
                        booking[
                            "booking_status"
                        ]
                    )

                if booking["notes"]:
                    st.caption("Notes")
                    st.write(
                        booking["notes"]
                    )

                st.markdown(
                    f"### Samples ({len(samples)})"
                )

                for sample in samples:

                    with st.container(
                        border=True
                    ):

                        col1, col2 = (
                            st.columns(
                                [3, 2]
                            )
                        )

                        with col1:

                            st.write(
                                f"**{sample['sample_name']}**"
                            )

                            st.caption(
                                (
                                    f"{sample['sample_id']} · "
                                    f"{sample['sample_type_name']}"
                                )
                            )

                        with col2:

                            if sample[
                                "location_name"
                            ]:
                                st.write(
                                    (
                                        f"{sample['location_code']} · "
                                        f"{sample['location_name']}"
                                    )
                                )
                            else:
                                st.write(
                                    "Location not assigned"
                                )

                st.markdown("---")

                pdf_bytes = generate_booking_confirmation_pdf(
                    booking,
                    samples,
                )

                st.download_button(
                    "Print / Download Booking Confirmation",
                    data=pdf_bytes,
                    file_name=(
                        f"{booking['booking_number']}_"
                        f"Booking_Confirmation.pdf"
                    ),
                    mime="application/pdf",
                    type="primary",
                    width="stretch",
                    key=(
                        f"download_booking_"
                        f"{booking['booking_group_id']}"
                    ),
                )

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

        try:
            booking_history = get_booking_groups()

        except Exception as exc:
            st.error(
                f"Could not load booking history: {exc}"
            )
            booking_history = []

        historical_bookings = [
            booking
            for booking in booking_history
            if booking["booking_status"]
            in (
                "Cancelled",
                "Completed",
            )
        ]

        st.subheader(
            f"Booking History "
            f"({len(historical_bookings)})"
        )

        if not historical_bookings:
            st.info(
                "No completed or cancelled bookings."
            )

        else:
            for booking in historical_bookings:

                with st.container(border=True):

                    col1, col2, col3 = st.columns(
                        [2, 3, 2]
                    )

                    with col1:
                        st.write(
                            f"**{booking['booking_number']}**"
                        )

                        st.caption(
                            booking["booking_status"]
                        )

                    with col2:
                        st.write(
                            (
                                f"{booking['start_date']:%d %b %Y}"
                                f" → "
                                f"{booking['end_date']:%d %b %Y}"
                            )
                        )

                        st.caption(
                            booking["booked_by"]
                        )

                    with col3:
                        sample_count = booking[
                            "sample_count"
                        ]

                        st.write(
                            (
                                f"{sample_count} "
                                f"sample"
                                f"{'s' if sample_count != 1 else ''}"
                            )
                        )