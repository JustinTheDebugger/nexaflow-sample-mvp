import streamlit as st

from repositories.sample_repository import (
    get_booking_preparation,
    mark_booking_item_prepared,    
    report_booking_item_missing,
    start_booking_preparation,
    submit_booking_preparation,
    undo_booking_item_prepared,
)


def _location_text(item):
    code = item.get("location_code")
    name = item.get("location_name")

    if code and name:
        return f"{code} — {name}"

    return code or name or "No recorded location"


def render_booking_preparation_page(hero):
    """
    Physical preparation workflow for a sample booking.
    """

    booking_group_id = st.session_state.get(
        "selected_preparation_booking_group_id"
    )

    if not booking_group_id:
        st.error(
            "No booking has been selected for preparation."
        )

        if st.button(
            "Back to Bookings",
            width="content",
        ):
            st.session_state.pop(
                "workflow_page",
                None,
            )
            st.rerun()

        return

    data = get_booking_preparation(
        booking_group_id
    )

    if not data:
        st.error(
            "The selected booking could not be found."
        )
        return

    booking = data["booking"]
    items = data["items"]

    hero(
        f"Prepare {booking['booking_number']}",
        (
            "Locate the booked samples and prepare "
            "available items for collection."
        ),
    )

    # ---------------------------------------------------------
    # Back
    # ---------------------------------------------------------

    if st.button(
        "← Back to Bookings",
        width="content",
        key="back_from_preparation",
    ):
        st.session_state.pop(
            "selected_preparation_booking_group_id",
            None,
        )
        st.session_state.pop(
            "workflow_page",
            None,
        )
        st.rerun()

    st.write("")

    # ---------------------------------------------------------
    # Booking summary
    # ---------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Requester",
        booking["booked_by"],
    )

    col2.metric(
        "Start Date",
        booking["start_date"].strftime(
            "%d %b %Y"
        ),
    )

    col3.metric(
        "End Date",
        booking["end_date"].strftime(
            "%d %b %Y"
        ),
    )

    st.markdown(
        f"**Status:** {booking['booking_status']}"
    )

    st.divider()

    # ---------------------------------------------------------
    # Reserved → Preparing
    # ---------------------------------------------------------

    if booking["booking_status"] == "Reserved":

        st.info(
            (
                "Start preparation when you are ready "
                "to physically locate these samples."
            )
        )

        if st.button(
            "Start Preparing",
            type="primary",
            width="content",
            key="start_booking_preparation",
        ):
            try:
                start_booking_preparation(
                    booking_group_id
                )

                st.success(
                    "Booking preparation started."
                )
                st.rerun()

            except Exception as exc:
                st.error(str(exc))

        return

    # ---------------------------------------------------------
    # Preparation progress
    # ---------------------------------------------------------

    prepared_count = sum(
        1
        for item in items
        if item["preparation_status"]
        in {"Prepared", "Replaced"}
    )

    missing_count = sum(
        1
        for item in items
        if item["preparation_status"]
        == "Missing"
    )

    outstanding_count = sum(
        1
        for item in items
        if item["preparation_status"]
        == "Not Prepared"
    )

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "Prepared",
        prepared_count,
    )

    metric2.metric(
        "Missing",
        missing_count,
    )

    metric3.metric(
        "Still to Check",
        outstanding_count,
    )

    st.divider()

    # ---------------------------------------------------------
    # Items
    # ---------------------------------------------------------

    st.markdown("### Samples")

    for item in items:

        status = item["preparation_status"]

        with st.container(border=True):

            top_left, top_right = st.columns(
                [4, 1]
            )

            with top_left:
                st.markdown(
                    f"**{item['sample_id']} — "
                    f"{item['sample_name']}**"
                )

                st.caption(
                    (
                        "Current location: "
                        f"{_location_text(item)}"
                    )
                )

            with top_right:
                st.markdown(
                    f"**{status}**"
                )

            # ---------------------------------------------
            # Not yet processed
            # ---------------------------------------------

            if status == "Not Prepared":

                action_col1, action_col2 = (
                    st.columns(2)
                )

                with action_col1:

                    if st.button(
                        "Mark Prepared",
                        type="primary",
                        width="stretch",
                        key=(
                            "prepare_item_"
                            f"{item['booking_id']}"
                        ),
                    ):
                        try:
                            mark_booking_item_prepared(
                                item["booking_id"]
                            )

                            st.rerun()

                        except Exception as exc:
                            st.error(str(exc))

                with action_col2:

                    if st.button(
                        "Report Missing",
                        width="stretch",
                        key=(
                            "report_missing_"
                            f"{item['booking_id']}"
                        ),
                    ):
                        st.session_state[
                            "missing_booking_item_id"
                        ] = item["booking_id"]

                        st.rerun()

                # Missing form only appears for
                # the selected item.
                if (
                    st.session_state.get(
                        "missing_booking_item_id"
                    )
                    == item["booking_id"]
                ):

                    with st.form(
                        (
                            "missing_item_form_"
                            f"{item['booking_id']}"
                        )
                    ):
                        st.warning(
                            (
                                "Report this sample as missing "
                                "from its expected location."
                            )
                        )

                        missing_note = st.text_area(
                            "Missing note *",
                            placeholder=(
                                "Example: Could not locate "
                                "sample on the S1 shelf."
                            ),
                        )

                        confirm_missing = (
                            st.form_submit_button(
                                "Confirm Missing",
                                type="primary",
                            )
                        )

                        if confirm_missing:
                            try:
                                report_booking_item_missing(
                                    item["booking_id"],
                                    missing_note,
                                )

                                st.session_state.pop(
                                    "missing_booking_item_id",
                                    None,
                                )

                                st.rerun()

                            except Exception as exc:
                                st.error(str(exc))

            # ---------------------------------------------
            # Prepared
            # ---------------------------------------------

            elif status == "Prepared":

                st.success(
                    (
                        "Prepared and moved to "
                        "C1 — Collection / Dispatch Area."
                    )
                )

                if (
                    booking["booking_status"]
                    == "Preparing"
                ):
                    if st.button(
                        "Undo Prepared",
                        width="content",
                        key=(
                            "undo_prepared_"
                            f"{item['booking_id']}"
                        ),
                    ):
                        try:
                            undo_booking_item_prepared(
                                item["booking_id"]
                            )

                            st.rerun()

                        except Exception as exc:
                            st.error(str(exc))

            # ---------------------------------------------
            # Missing
            # ---------------------------------------------

            elif status == "Missing":

                st.warning(
                    (
                        "This sample was reported missing. "
                        "Preparation can continue without it."
                    )
                )

                if item.get("missing_note"):
                    st.caption(
                        f"Note: {item['missing_note']}"
                    )

            # ---------------------------------------------
            # Replacement
            # ---------------------------------------------

            elif status == "Replaced":

                st.info(
                    "A replacement sample will be supplied."
                )

                replacement_id = item.get(
                    "replacement_sample_id"
                )

                replacement_name = item.get(
                    "replacement_sample_name"
                )

                if replacement_id:
                    st.write(
                        (
                            f"{replacement_id} — "
                            f"{replacement_name}"
                        )
                    )

    # ---------------------------------------------------------
    # Submit preparation
    # ---------------------------------------------------------

    if booking["booking_status"] == "Preparing":

        st.divider()

        if outstanding_count:
            st.info(
                (
                    f"{outstanding_count} sample"
                    f"{'s' if outstanding_count != 1 else ''} "
                    "still need to be prepared or "
                    "reported missing."
                )
            )

        else:

            if missing_count:
                st.warning(
                    (
                        f"{missing_count} sample"
                        f"{'s' if missing_count != 1 else ''} "
                        "will remain recorded as missing. "
                        "This will not prevent collection."
                    )
                )
            else:
                st.success(
                    "All booked samples are prepared."
                )

            if st.button(
                "Submit Prepared Samples",
                type="primary",
                width="stretch",
                key="submit_booking_preparation",
            ):
                try:
                    result = (
                        submit_booking_preparation(
                            booking_group_id
                        )
                    )

                    st.session_state[
                        "preparation_result"
                    ] = result

                    st.rerun()

                except Exception as exc:
                    st.error(str(exc))

    # ---------------------------------------------------------
    # Ready
    # ---------------------------------------------------------

    if (
        booking["booking_status"]
        == "Ready for Collection"
    ):

        if missing_count:

            st.warning(
                (
                    "Booking is ready for collection "
                    "with an exception."
                )
            )

            st.write(
                (
                    f"{prepared_count} of {len(items)} "
                    "requested samples are prepared at "
                    "C1 — Collection / Dispatch Area."
                )
            )

            st.error(
                (
                    f"{missing_count} requested sample"
                    f"{'s are' if missing_count != 1 else ' is'} "
                    "missing and will not be supplied."
                )
            )

        else:

            st.success(
                (
                    "Preparation complete. All requested "
                    "samples are ready at "
                    "C1 — Collection / Dispatch Area."
                )
            )