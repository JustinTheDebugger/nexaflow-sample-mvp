import streamlit as st

from repositories.sample_repository import (
    get_booking_return,
    return_booking_item,
)


def render_booking_return_page(hero=None):
    """
    Display checked-out samples and process
    individual return inspections.
    """

    st.title("Sample Return Inspection")

    booking_group_id = st.session_state.get(
        "selected_return_booking_group_id"
    )

    if not booking_group_id:
        st.info(
            "Select a checked-out booking from "
            "Booking Management."
        )
        return

    try:
        data = get_booking_return(booking_group_id)
    except Exception as exc:
        st.error(f"Could not load booking: {exc}")
        return

    booking = data["booking"]
    items = data["items"]

    st.caption(
        f"Booking {booking['booking_number']} "
        f"• Requested by {booking['booked_by']}"
    )

    checked_out_items = [
        item for item in items
        if item["booking_status"] == "Checked Out"
    ]

    returned_items = [
        item for item in items
        if item["booking_status"] == "Completed"
    ]

    col1, col2, col3 = st.columns(3)

    col1.metric("Issued Samples", len(items))
    col2.metric("Awaiting Return", len(checked_out_items))
    col3.metric("Returned", len(returned_items))

    if not checked_out_items:
        st.success("No samples are awaiting return in this booking.")

    st.divider()

    for item in checked_out_items:

        sample_id = item["sample_id"]
        sample_name = item["sample_name"]
        booking_item_id = item["booking_id"]

        with st.container(border=True):

            st.subheader(sample_name)
            st.caption(f"Sample ID: {sample_id}")

            st.write(
                f"**Last holder:** "
                f"{item['current_holder'] or 'Unknown'}"
            )

            with st.form(
                key=f"return_form_{booking_item_id}"
            ):

                condition = st.radio(
                    "Return inspection",
                    options=["Good", "Damaged"],
                    horizontal=True,
                )

                notes = st.text_area(
                    "Inspection notes",
                    placeholder=(
                        "Describe any damage, missing parts, "
                        "or observations."
                    ),
                )

                if condition == "Damaged":
                    st.warning(
                        "This sample will be moved to "
                        "Q1 — Inspection / Quarantine."
                    )
                else:
                    st.info(
                        "This sample will return to its "
                        "recorded home location."
                    )

                submitted = st.form_submit_button(
                    "Confirm Return",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                try:
                    result = return_booking_item(
                        booking_group_id=booking_group_id,
                        booking_item_id=booking_item_id,
                        return_condition=condition,
                        notes=notes,
                    )

                    st.success(
                        f"{result['sample_id']} returned "
                        f"to {result['destination']}."
                    )

                    st.rerun()

                except Exception as exc:
                    st.error(
                        f"Could not return sample: {exc}"
                    )

    if returned_items:
        st.divider()
        st.subheader("Returned Samples")

        for item in returned_items:
            st.write(
                f"✓ {item['sample_id']} — "
                f"{item['sample_name']}"
            )