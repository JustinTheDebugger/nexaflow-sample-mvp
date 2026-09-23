import streamlit as st

from repositories.sample_repository import (
    complete_booking_return,
    get_booking_group_details,
    get_sample_locations,
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
            "Inspect all returned samples and "
            "complete the booking in one step."
        ),
    )

    # -------------------------------------------------
    # Flash
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
    # Load booking details
    # -------------------------------------------------

    try:

        booking_details = (
            get_booking_group_details(
                booking_group_id
            )
        )

    except Exception as exc:

        st.error(
            f"Could not load booking: {exc}"
        )

        return

    try:
        locations = get_sample_locations()

    except Exception as exc:
        st.error(
            f"Could not load sample locations: {exc}"
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

        st.session_state.pop(
            "confirm_booking_return",
            None,
        )

        st.rerun()

    # -------------------------------------------------
    # Booking number
    # -------------------------------------------------

    st.caption(
        f"Booking {booking['booking_number']}"
    )

    # -------------------------------------------------
    # Booking summary
    # -------------------------------------------------

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
    # Already completed
    # -------------------------------------------------

    if (
        booking["booking_status"]
        == "Completed"
    ):

        st.success(
            (
                "This booking has already been "
                "returned and completed."
            )
        )

        st.caption(
            (
                "Return inspection results are "
                "closed and can no longer be changed."
            )
        )

        return

    # -------------------------------------------------
    # Other non-returnable states
    # -------------------------------------------------

    if (
        booking["booking_status"]
        != "Reserved"
    ):

        st.info(
            (
                f"This booking is "
                f"{booking['booking_status']} "
                "and cannot be processed as a return."
            )
        )

        return

    # -------------------------------------------------
    # Inspector
    # -------------------------------------------------

    st.subheader(
        "Return Inspection"
    )

    st.caption(
        (
            "Check every physical sample before "
            "submitting the return."
        )
    )

    checked_by = st.text_input(
        "Checked By *",
        key="return_checked_by",
        placeholder="Enter staff name",
    )

    st.divider()

    # -------------------------------------------------
    # Build return results
    # -------------------------------------------------

    return_items = []

    status_options = [
        "Good",
        "Damaged",
        "Incomplete",
        "Not Returned",
    ]

    # -------------------------------------------------
    # Render each sample
    # -------------------------------------------------

    for index, sample in enumerate(
        samples,
        start=1,
    ):

        booking_item_id = str(
            sample["booking_item_id"]
        )

        with st.container(
            border=True
        ):

            # -----------------------------------------
            # Header
            # -----------------------------------------

            header_col1, header_col2 = (
                st.columns(
                    [4, 1]
                )
            )

            with header_col1:

                st.markdown(
                    (
                        f"### "
                        f"{sample['sample_name']}"
                    )
                )

            with header_col2:

                st.caption(
                    (
                        f"{index} of "
                        f"{len(samples)}"
                    )
                )

            # -----------------------------------------
            # Location
            # -----------------------------------------

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
            # Condition
            # -----------------------------------------

            return_status = st.radio(
                "Return Condition",
                status_options,
                index=0,
                horizontal=True,
                key=(
                    f"return_status_"
                    f"{booking_item_id}"
                ),
            )

            return_location_id = None

            if return_status == "Good":

                location_options = {
                    (
                        f"{location['code']} — "
                        f"{location['name']}"
                    ): location["id"]
                    for location in locations
                    if location["code"] != "H1"
                }

                selected_location = st.selectbox(
                    "Return Location *",
                    options=list(
                        location_options.keys()
                    ),
                    key=(
                        f"return_location_"
                        f"{booking_item_id}"
                    ),
                )

                return_location_id = (
                    location_options[
                        selected_location
                    ]
                )

            elif return_status in {
                "Damaged",
                "Incomplete",
            }:
                st.info(
                    (
                        "Temporary location: "
                        "**H1 — Repair / Hold Area**"
                    )
                )

            else:
                st.warning(
                    (
                        "This sample will be marked as "
                        "**Not Returned / Lost** and will "
                        "have no physical location."
                    )
                )

            # -----------------------------------------
            # Notes
            # -----------------------------------------

            return_notes = st.text_area(
                "Notes",
                placeholder=(
                    "Optional. Record damage, "
                    "missing parts, or other "
                    "observations."
                ),
                key=(
                    f"return_notes_"
                    f"{booking_item_id}"
                ),
            )

            # -----------------------------------------
            # Result explanation
            # -----------------------------------------

            if return_status == "Good":

                st.caption(
                    (
                        "Sample will return to "
                        "Active / Good and will "
                        "be available for booking."
                    )
                )

            elif return_status == "Damaged":

                st.warning(
                    (
                        "Sample will be marked "
                        "Damaged and moved to "
                        "Sample Issues."
                    )
                )

            elif return_status == "Incomplete":

                st.warning(
                    (
                        "Sample will be made "
                        "Inactive and moved to "
                        "Sample Issues."
                    )
                )

            elif return_status == "Not Returned":

                st.error(
                    (
                        "The sample will be recorded as "
                        "Not Returned and marked Lost. "
                        "It will move to Sample Issues "
                        "for follow-up."
                    )
                )

            # -----------------------------------------
            # Add to transaction
            # -----------------------------------------

            return_items.append(
                {
                    "booking_item_id": (
                        sample[
                            "booking_item_id"
                        ]
                    ),
                    "sample_record_id": (
                        sample[
                            "sample_record_id"
                        ]
                    ),
                    "return_status": (
                        return_status
                    ),
                    "return_location_id": (
                        return_location_id
                    ),
                    "notes": (
                        return_notes
                    ),
                }
            )

    # -------------------------------------------------
    # Submit return
    # -------------------------------------------------

    st.divider()

    st.subheader(
        "Complete Return"
    )

    st.caption(
        (
            "Submitting the return will close this "
            "booking. Return results cannot be "
            "edited afterwards."
        )
    )

    # -------------------------------------------------
    # Initial submit
    # -------------------------------------------------

    if not st.session_state.get(
        "confirm_booking_return",
        False,
    ):

        if st.button(
            "Submit Return",
            key="submit_booking_return",
            type="primary",
            width="stretch",
        ):

            if not checked_by.strip():

                st.error(
                    "Please enter Checked By."
                )

            elif not samples:

                st.error(
                    (
                        "This booking does not "
                        "contain any samples."
                    )
                )

            else:

                st.session_state[
                    "confirm_booking_return"
                ] = True

                st.rerun()

    # -------------------------------------------------
    # Confirmation
    # -------------------------------------------------

    else:

        st.warning(
            (
                "Are you sure you want to complete "
                f"booking "
                f"{booking['booking_number']}? "
                "The booking will be closed and "
                "the return results will no longer "
                "be editable."
            )
        )

        # -----------------------------------------
        # Return summary
        # -----------------------------------------

        good_count = sum(
            1
            for item in return_items
            if (
                item["return_status"]
                == "Good"
            )
        )

        damaged_count = sum(
            1
            for item in return_items
            if (
                item["return_status"]
                == "Damaged"
            )
        )

        incomplete_count = sum(
            1
            for item in return_items
            if (
                item["return_status"]
                == "Incomplete"
            )
        )

        not_returned_count = sum(
            1
            for item in return_items
            if (
                item["return_status"]
                == "Not Returned"
            )
        )

        summary_col1, summary_col2 = (
            st.columns(2)
        )

        with summary_col1:

            st.write(
                f"**Good:** {good_count}"
            )

            st.write(
                (
                    f"**Damaged:** "
                    f"{damaged_count}"
                )
            )

        with summary_col2:

            st.write(
                (
                    f"**Incomplete:** "
                    f"{incomplete_count}"
                )
            )

            st.write(
                (
                    f"**Not Returned:** "
                    f"{not_returned_count}"
                )
            )

        confirm_col, cancel_col = (
            st.columns(2)
        )

        # -----------------------------------------
        # Confirm
        # -----------------------------------------

        with confirm_col:

            if st.button(
                "Yes, Complete Return",
                key="confirm_complete_return",
                type="primary",
                width="stretch",
            ):

                if not checked_by.strip():

                    st.error(
                        (
                            "Please enter "
                            "Checked By."
                        )
                    )

                else:

                    try:

                        result = (
                            complete_booking_return(
                                booking_group_id=(
                                    booking_group_id
                                ),
                                checked_by=(
                                    checked_by
                                ),
                                return_items=(
                                    return_items
                                ),
                            )
                        )

                    except Exception as exc:

                        st.error(
                            (
                                "Could not complete "
                                f"return: {exc}"
                            )
                        )

                    else:

                        # ---------------------------------
                        # Clear return workflow
                        # ---------------------------------

                        st.session_state.pop(
                            "confirm_booking_return",
                            None,
                        )

                        st.session_state.pop(
                            (
                                "selected_return_"
                                "booking_group_id"
                            ),
                            None,
                        )

                        st.session_state.pop(
                            "workflow_page",
                            None,
                        )

                        # ---------------------------------
                        # Flash on management page
                        # ---------------------------------

                        st.session_state[
                            "booking_management_flash"
                        ] = {
                            "type": "success",
                            "message": (
                                f"{result['booking_number']} "
                                "return completed "
                                f"with "
                                f"{result['sample_count']} "
                                "samples."
                            ),
                        }

                        st.rerun()

        # -----------------------------------------
        # Cancel confirmation
        # -----------------------------------------

        with cancel_col:

            if st.button(
                "Go Back",
                key="cancel_complete_return",
                width="stretch",
            ):

                st.session_state.pop(
                    "confirm_booking_return",
                    None,
                )

                st.rerun()