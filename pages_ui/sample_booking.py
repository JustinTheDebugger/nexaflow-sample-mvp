from datetime import date, timedelta

import streamlit as st

from repositories.sample_repository import (
    create_sample_bookings,
    create_sample_request,
    get_active_products,
    search_available_samples,
)

def render_sample_booking(hero):
    hero(
        "Sample Booking",
        (
            "Find samples available for the required dates "
            "and create a booking request."
        ),
    )

    if "booking_cart" not in st.session_state:
        st.session_state["booking_cart"] = []

    flash = st.session_state.pop(
        "booking_flash",
        None,
    )

    if flash:
        if flash["type"] == "success":
            st.success(flash["message"])
        else:
            st.error(flash["message"])

    today = date.today()

    st.markdown("### Booking Request")

    # ---------------------------------------------------------
    # Booking Search Details
    # ---------------------------------------------------------

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
            "Next",
            type="primary",
            width="stretch",
        )

    # ---------------------------------------------------------
    # Save Booking Search
    # ---------------------------------------------------------

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

        st.session_state["booking_search"] = {
            "start_date": start_date,
            "end_date": end_date,
            "booked_by": booked_by.strip(),
            "team": team,
            "purpose": purpose,
            "notes": notes.strip(),
        }

        # New date/search criteria means old search/cart is invalid.
        st.session_state["booking_search_results"] = []
        st.session_state["booking_search_performed"] = False
        st.session_state["booking_cart"] = []

    booking_search = st.session_state.get(
        "booking_search"
    )

    if not booking_search:
        return

    # ---------------------------------------------------------
    # Find Samples
    # ---------------------------------------------------------

    st.divider()

    st.markdown("### Find Samples")

    st.caption(
        (
            f"Required from "
            f"{booking_search['start_date']:%d %b %Y} "
            f"to "
            f"{booking_search['end_date']:%d %b %Y}"
        )
    )

    search_text = st.text_input(
        "Search samples",
        placeholder=(
            "Enter sample name, sample ID or product code, then press Enter"
        ),
        key="booking_sample_search",
    )

    st.caption(
        "Press Enter to search available samples for the selected dates."
    )

    search_results = []
    search_performed = False

    if len(search_text.strip()) >= 2:
        search_performed = True

        try:
            search_results = search_available_samples(
                search_text=search_text.strip(),
                start_date=booking_search["start_date"],
                end_date=booking_search["end_date"],
                limit=10,
            )

        except Exception as exc:
            st.error(
                f"Could not search samples: {exc}"
            )

    # ---------------------------------------------------------
    # Matching Samples
    # ---------------------------------------------------------

    if search_results:
        st.markdown("### Suggested Matches")

        for sample in search_results:
            with st.container(border=True):
                col1, col2 = st.columns(
                    [4, 1]
                )

                with col1:
                    display_name = sample[
                        "sample_name"
                    ]

                    if sample["location_code"]:
                        display_name += (
                            f" ({sample['location_code']})"
                        )

                    st.write(
                        f"**{display_name}**"
                    )

                    st.caption(
                        (
                            f"{sample['sample_id']} · "
                            f"{sample['sample_type_name']}"
                        )
                    )

                with col2:
                    already_added = any(
                        item["sample_record_id"]
                        == sample["sample_record_id"]
                        for item
                        in st.session_state[
                            "booking_cart"
                        ]
                    )

                    if already_added:
                        st.caption("Added")

                    else:
                        if st.button(
                            "Add",
                            key=(
                                f"add_booking_sample_"
                                f"{sample['sample_record_id']}"
                            ),
                            width="stretch",
                        ):
                            st.session_state[
                                "booking_cart"
                            ].append(sample)

                            st.rerun()

    elif (
        search_performed
        and search_text.strip()
    ):
        st.warning(
            "No available samples matched your search "
            "for the selected dates."
        )

        if st.button(
            "Request a Sample",
            key="open_sample_request",
            width="content",
        ):
            st.session_state[
                "show_sample_request_form"
            ] = True

    st.divider()

    st.subheader(
        f"Selected Samples "
        f"({len(st.session_state['booking_cart'])})"
    )

    if not st.session_state["booking_cart"]:
        st.info(
            "No samples have been added yet."
        )

    else:
        for sample in st.session_state[
            "booking_cart"
        ]:
            with st.container(border=True):
                col1, col2 = st.columns(
                    [4, 1]
                )

                with col1:
                    display_name = sample[
                        "sample_name"
                    ]

                    if sample["location_code"]:
                        display_name += (
                            f" ({sample['location_code']})"
                        )

                    st.write(
                        f"**{display_name}**"
                    )

                    st.caption(
                        sample["sample_id"]
                    )

                with col2:
                    if st.button(
                        "Remove",
                        key=(
                            f"remove_booking_sample_"
                            f"{sample['sample_record_id']}"
                        ),
                        width="stretch",
                    ):
                        st.session_state[
                            "booking_cart"
                        ] = [
                            item
                            for item
                            in st.session_state[
                                "booking_cart"
                            ]
                            if item["sample_record_id"]
                            != sample["sample_record_id"]
                        ]

                        st.rerun()

        if st.session_state["booking_cart"]:

            st.markdown("---")

            sample_count = len(
                st.session_state["booking_cart"]
            )

            st.caption(
                (
                    f"You are booking {sample_count} "
                    f"sample{'s' if sample_count != 1 else ''} "
                    f"from "
                    f"{booking_search['start_date']:%d %b %Y} "
                    f"to "
                    f"{booking_search['end_date']:%d %b %Y}."
                )
            )

            if st.button(
                "Confirm Booking",
                type="primary",
                width="stretch",
            ):
                sample_record_ids = [
                    sample["sample_record_id"]
                    for sample
                    in st.session_state["booking_cart"]
                ]

                try:
                    created_bookings = create_sample_bookings(
                        sample_record_ids=sample_record_ids,
                        booked_by=booking_search[
                            "booked_by"
                        ],
                        team=booking_search[
                            "team"
                        ],
                        purpose=booking_search[
                            "purpose"
                        ],
                        start_date=booking_search[
                            "start_date"
                        ],
                        end_date=booking_search[
                            "end_date"
                        ],
                        notes=booking_search[
                            "notes"
                        ],
                    )

                    booking_count = len(
                        created_bookings
                    )

                    st.session_state[
                        "booking_flash"
                    ] = {
                        "type": "success",
                        "message": (
                            f"{booking_count} "
                            f"sample"
                            f"{'s' if booking_count != 1 else ''} "
                            f"booked successfully."
                        ),
                    }

                    # Clear completed workflow
                    st.session_state[
                        "booking_cart"
                    ] = []

                    st.session_state.pop(
                        "booking_search",
                        None,
                    )

                    st.session_state.pop(
                        "booking_search_results",
                        None,
                    )

                    st.session_state.pop(
                        "booking_search_performed",
                        None,
                    )

                    st.session_state.pop(
                        "booking_sample_search",
                        None,
                    )

                    st.rerun()

                except Exception as exc:
                    st.error(
                        f"Could not complete booking: {exc}"
                    )