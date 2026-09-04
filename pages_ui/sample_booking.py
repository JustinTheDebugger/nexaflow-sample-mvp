from datetime import date, timedelta

import streamlit as st

from repositories.sample_repository import (
    create_sample_booking,
    get_available_samples,
)


def render_sample_booking(hero):
    hero(
        "Sample Booking",
        (
            "Find samples available for the required dates "
            "and create a booking request."
        ),
    )

    flash = st.session_state.pop(
        "booking_flash",
        None,
    )

    if flash:
        if flash["type"] == "success":
            st.success(
                flash["message"]
            )
        else:
            st.error(
                flash["message"]
            )


    today = date.today()

    st.markdown("### Booking Request")

    with st.form(
        "sample_booking_search_form",
        clear_on_submit=False,
    ):
        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "Required From *",
                value=today,
            )

            booked_by = st.text_input(
                "Requested By *",
                placeholder="e.g. Justin",
            )

            team = st.selectbox(
                "Department / Team *",
                [
                    "Sales",
                    "Marketing",
                    "Trade Show",
                    "Photography",
                    "Product",
                    "Other",
                ],
            )

        with col2:
            end_date = st.date_input(
                "Required Until *",
                value=today + timedelta(days=3),
            )

            purpose = st.selectbox(
                "Purpose *",
                [
                    "Customer Demonstration",
                    "Trade Show",
                    "Marketing Photos",
                    "Product Testing",
                    "Factory Review",
                    "Other",
                ],
            )

            notes = st.text_area(
                "Notes",
                placeholder="Additional booking details...",
            )

        find_samples = st.form_submit_button(
            "Find Available Samples",
            type="primary",
            width="stretch",
        )

    if find_samples:
        if end_date < start_date:
            st.error(
                "Required Until cannot be before Required From."
            )
            return

        if not booked_by.strip():
            st.error(
                "Requested By is required."
            )
            return

        st.session_state[
            "booking_search"
        ] = {
            "start_date": start_date,
            "end_date": end_date,
            "booked_by": booked_by.strip(),
            "team": team,
            "purpose": purpose,
            "notes": notes.strip(),
        }

    booking_search = st.session_state.get(
        "booking_search"
    )

    if not booking_search:
        return

    st.markdown("---")
    st.markdown("### Available Samples")

    try:
        available_samples = get_available_samples(
            start_date=booking_search[
                "start_date"
            ],
            end_date=booking_search[
                "end_date"
            ],
        )

    except Exception as exc:
        st.error(
            f"Could not load available samples: {exc}"
        )
        return

    if not available_samples:
        st.info(
            "No bookable samples are available "
            "for the selected dates."
        )
        return

    st.caption(
        f"{len(available_samples)} "
        f"sample(s) available from "
        f"{booking_search['start_date']:%d %b %Y} "
        f"to "
        f"{booking_search['end_date']:%d %b %Y}."
    )

    for sample in available_samples:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(
                [2.5, 1.3, 1.4, 1.2]
            )

            with col1:
                display_name = sample[
                    "sample_name"
                ]

                location_code = sample[
                    "current_location_code"
                ]

                if location_code:
                    display_name += (
                        f" ({location_code})"
                    )

                st.markdown(
                    f"### {display_name}"
                )

                st.caption(
                    sample["sample_id"]
                )

                if sample["category_name"]:
                    st.write(
                        sample["category_name"]
                    )

            with col2:
                st.caption("Sample Type")
                st.write(
                    sample["sample_type_name"]
                )

                if sample[
                    "requires_approval"
                ]:
                    st.caption(
                        "Approval required"
                    )
                else:
                    st.caption(
                        "Direct booking"
                    )

            with col3:
                st.caption("Current Location")
                st.write(
                    sample[
                        "current_location_name"
                    ]
                    or "No Location"
                )

                st.caption("Condition")
                st.write(
                    sample["condition"]
                )

            with col4:
                button_label = (
                    "Request Booking"
                    if sample[
                        "requires_approval"
                    ]
                    else "Book Sample"
                )

                if st.button(
                    button_label,
                    key=(
                        f"book_sample_"
                        f"{sample['id']}"
                    ),
                    type="primary",
                    width="stretch",
                ):
                    try:
                        booking = (
                            create_sample_booking(
                                sample_record_id=(
                                    sample["id"]
                                ),
                                booked_by=(
                                    booking_search[
                                        "booked_by"
                                    ]
                                ),
                                team=(
                                    booking_search[
                                        "team"
                                    ]
                                ),
                                purpose=(
                                    booking_search[
                                        "purpose"
                                    ]
                                ),
                                start_date=(
                                    booking_search[
                                        "start_date"
                                    ]
                                ),
                                end_date=(
                                    booking_search[
                                        "end_date"
                                    ]
                                ),
                                notes=(
                                    booking_search[
                                        "notes"
                                    ]
                                ),
                            )
                        )

                    except Exception as exc:
                        st.error(
                            f"Could not create booking: {exc}"
                        )

                    else:
                        st.session_state[
                            "booking_flash"
                        ] = {
                            "type": "success",
                            "message": (
                                f"{sample['sample_name']} "
                                f"booking created. "
                                f"Status: "
                                f"{booking['booking_status']}."
                            ),
                        }

                        st.rerun()