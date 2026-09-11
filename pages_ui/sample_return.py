import streamlit as st

from repositories.sample_repository import (
    get_booking_group_details,
    get_booking_return_checks,
    save_sample_return_check,
)


def render_sample_return_page(hero):

    # -------------------------------------------------
    # Selected booking
    # -------------------------------------------------

    booking_group_id = st.session_state.get(
        "selected_return_booking_group_id"
    )

    # -------------------------------------------------
    # Hero
    # -------------------------------------------------

    hero(
        "Return Samples",
        (
            "Inspect returned samples, record their "
            "condition, and complete the return process."
        ),
    )

    # -------------------------------------------------
    # Flash message
    # -------------------------------------------------

    flash_message = st.session_state.pop(
        "sample_return_flash",
        None,
    )

    if flash_message:
        st.success(flash_message)

    # -------------------------------------------------
    # No booking selected
    # -------------------------------------------------

    if not booking_group_id:

        st.warning(
            "No booking has been selected for return."
        )

        if st.button(
            "← Back to Bookings & Returns",
            key="return_no_booking_back",
        ):

            st.session_state.pop(
                "workflow_page",
                None,
            )

            st.rerun()

        return

    # -------------------------------------------------
    # Load booking
    # -------------------------------------------------

    try:

        booking_details = get_booking_group_details(
            booking_group_id
        )

    except Exception as exc:

        st.error(
            f"Could not load booking: {exc}"
        )

        return

    if not booking_details:

        st.error(
            "Booking could not be found."
        )

        return

    booking = booking_details["booking"]
    samples = booking_details["samples"]

    # -------------------------------------------------
    # Back
    # -------------------------------------------------

    if st.button(
        "← Back to Bookings & Returns",
        key="back_from_sample_return",
    ):

        st.session_state.pop(
            "selected_return_booking_group_id",
            None,
        )

        st.session_state.pop(
            "workflow_page",
            None,
        )

        st.rerun()

    # -------------------------------------------------
    # Booking summary
    # -------------------------------------------------

    st.caption(
        f"Booking {booking['booking_number']}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Requested By",
            booking["booked_by"] or "-",
        )

    with col2:
        st.metric(
            "Department",
            booking["team"] or "-",
        )

    with col3:
        st.metric(
            "Samples",
            len(samples),
        )

    st.write(
        (
            f"**Required:** "
            f"{booking['start_date']:%d %b %Y}"
            f" → "
            f"{booking['end_date']:%d %b %Y}"
        )
    )

    if booking["purpose"]:
        st.write(
            f"**Purpose:** {booking['purpose']}"
        )

    if booking["notes"]:
        st.write(
            f"**Booking Notes:** {booking['notes']}"
        )

    st.divider()

    # -------------------------------------------------
    # Only Reserved bookings can be returned
    # -------------------------------------------------

    if booking["booking_status"] != "Reserved":

        st.info(
            (
                f"This booking is currently "
                f"{booking['booking_status']} "
                "and cannot be processed as a return."
            )
        )

        return

    # -------------------------------------------------
    # Return inspection
    # -------------------------------------------------

    st.subheader("Return Inspection")

    st.caption(
        (
            "Inspect each physical sample and record "
            "its condition when returned."
        )
    )

    # -------------------------------------------------
    # Inspector
    # -------------------------------------------------

    checked_by = st.text_input(
        "Checked By *",
        key="return_checked_by",
        placeholder="Enter staff name",
    )

    # -------------------------------------------------
    # Load existing return checks
    # -------------------------------------------------

    try:

        return_checks = get_booking_return_checks(
            booking_group_id
        )

    except Exception as exc:

        st.error(
            (
                "Could not load return inspection "
                f"records: {exc}"
            )
        )

        return_checks = []

    # -------------------------------------------------
    # Index checks by booking item
    # -------------------------------------------------

    return_checks_by_item = {
        str(check["booking_item_id"]): check
        for check in return_checks
    }

    # -------------------------------------------------
    # Progress
    # -------------------------------------------------

    total_count = len(samples)

    checked_count = len(
        return_checks_by_item
    )

    if total_count > 0:

        st.progress(
            checked_count / total_count
        )

    st.caption(
        (
            f"{checked_count} of "
            f"{total_count} samples checked"
        )
    )

    st.divider()

    # -------------------------------------------------
    # Sample return cards
    # -------------------------------------------------

    for sample in samples:

        booking_item_id = str(
            sample["booking_item_id"]
        )

        existing_check = (
            return_checks_by_item.get(
                booking_item_id
            )
        )

        with st.container(border=True):

            # -----------------------------------------
            # Sample heading
            # -----------------------------------------

            st.markdown(
                f"### {sample['sample_name']}"
            )

            if sample["location_code"]:

                location_text = (
                    f"{sample['location_code']} - "
                    f"{sample['location_name']}"
                )

            else:

                location_text = (
                    sample["location_name"]
                    or "Location not set"
                )

            st.caption(
                (
                    f"{sample['sample_id']} · "
                    f"{location_text}"
                )
            )

            # -----------------------------------------
            # Existing inspection result
            # -----------------------------------------

            if existing_check:

                existing_status = (
                    existing_check[
                        "return_status"
                    ]
                )

                if existing_status == "Good":

                    st.success(
                        "Returned in Good condition"
                    )

                elif existing_status == "Damaged":

                    st.error(
                        "Returned as Damaged"
                    )

                elif existing_status == "Incomplete":

                    st.warning(
                        "Returned as Incomplete"
                    )

                elif existing_status == "Missing":

                    st.error(
                        "Sample reported Missing"
                    )

                st.caption(
                    (
                        "Last checked by "
                        f"{existing_check['checked_by']}"
                    )
                )

                if existing_check.get("notes"):

                    st.write(
                        (
                            "**Inspection Notes:** "
                            f"{existing_check['notes']}"
                        )
                    )

            # -----------------------------------------
            # Return condition
            # -----------------------------------------

            status_options = [
                "Good",
                "Damaged",
                "Incomplete",
                "Missing",
            ]

            default_index = 0

            if existing_check:

                previous_status = (
                    existing_check[
                        "return_status"
                    ]
                )

                if previous_status in status_options:

                    default_index = (
                        status_options.index(
                            previous_status
                        )
                    )

            return_status = st.radio(
                "Return Condition",
                status_options,
                index=default_index,
                horizontal=True,
                key=(
                    f"return_status_"
                    f"{booking_item_id}"
                ),
            )

            # -----------------------------------------
            # Notes
            # -----------------------------------------

            return_notes = st.text_area(
                "Notes",
                value=(
                    existing_check["notes"]
                    if (
                        existing_check
                        and existing_check.get(
                            "notes"
                        )
                    )
                    else ""
                ),
                placeholder=(
                    "Optional. Record any damage, "
                    "missing parts, or other observations."
                ),
                key=(
                    f"return_notes_"
                    f"{booking_item_id}"
                ),
            )

            # -----------------------------------------
            # Save / update
            # -----------------------------------------

            save_label = (
                "Update Return Check"
                if existing_check
                else "Save Return Check"
            )

            if st.button(
                save_label,
                key=(
                    f"save_return_"
                    f"{booking_item_id}"
                ),
                type="primary",
                width="stretch",
            ):

                if not checked_by.strip():

                    st.error(
                        "Please enter Checked By."
                    )

                else:

                    try:

                        save_sample_return_check(
                            booking_group_id=booking[
                                "booking_group_id"
                            ],
                            booking_item_id=sample[
                                "booking_item_id"
                            ],
                            sample_record_id=sample[
                                "sample_record_id"
                            ],
                            return_status=return_status,
                            checked_by=checked_by.strip(),
                            damage_details=None,
                            missing_details=None,
                            notes=return_notes,
                        )

                        st.session_state[
                            "sample_return_flash"
                        ] = (
                            f"{sample['sample_id']} "
                            "return check saved."
                        )

                        st.rerun()

                    except Exception as exc:

                        st.error(
                            (
                                "Could not save "
                                f"return check: {exc}"
                            )
                        )

    # -------------------------------------------------
    # Bottom summary
    # -------------------------------------------------

    st.divider()

    st.subheader("Return Progress")

    checked_count = len(
        return_checks_by_item
    )

    st.write(
        (
            f"**{checked_count} of "
            f"{total_count} samples checked**"
        )
    )

    if checked_count < total_count:

        st.info(
            (
                "Complete the return inspection "
                "for every sample before closing "
                "the booking."
            )
        )

    else:

        st.success(
            (
                "All samples have been inspected. "
                "This booking is ready to complete."
            )
        )

        st.button(
            "Complete Return",
            key="complete_sample_return",
            type="primary",
            width="stretch",
            disabled=True,
            help=(
                "We will connect booking completion "
                "in the next step."
            ),
        )