from datetime import date



import streamlit as st



from repositories.sample_repository import (

    approve_sample_request,

    cancel_booking_group,

    get_booking_group_details,

    get_booking_groups,

    get_booking_return_checks,

    save_sample_return_check,

    get_booking_history_items,

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



    st.markdown(

        """

        <style>



        /* -----------------------------------------

        View button - blue

        ----------------------------------------- */



        div[class*="st-key-booking_view_"] button {

            background-color: #2563eb !important;

            color: white !important;

            border: 1px solid #2563eb !important;

        }



        div[class*="st-key-booking_view_"] button:hover {

            background-color: #1d4ed8 !important;

            color: white !important;

            border-color: #1d4ed8 !important;

        }





        /* -----------------------------------------

        Return Samples button - grey

        ----------------------------------------- */



        div[class*="st-key-booking_return_"] button {

            background-color: #606060 !important;

            color: white !important;

            border: 1px solid #606060 !important;

        }



        div[class*="st-key-booking_return_"] button:hover {

            background-color: #777777 !important;

            color: white !important;

            border-color: #777777 !important;

        }





        /* -----------------------------------------

        Print PDF button - white

        ----------------------------------------- */



        div[class*="st-key-booking_row_print_"] button {

            background-color: white !important;

            color: #1f2937 !important;

            border: 1px solid #d1d5db !important;

        }



        div[class*="st-key-booking_row_print_"] button:hover {

            background-color: #f3f4f6 !important;

            color: #1f2937 !important;

            border-color: #9ca3af !important;

        }





        /* -----------------------------------------

        Cancel Booking button - red

        ----------------------------------------- */



        div[class*="st-key-booking_cancel_"] button {

            background-color: #dc2626 !important;

            color: white !important;

            border: 1px solid #dc2626 !important;

        }



        div[class*="st-key-booking_cancel_"] button:hover {

            background-color: #b91c1c !important;

            color: white !important;

            border-color: #b91c1c !important;

        }



        </style>

        """,

        unsafe_allow_html=True,

    )



    flash = st.session_state.pop(

        "booking_management_flash",

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



    # ---------------------------------------------------------

    # Load page data

    # ---------------------------------------------------------



    booking_history = []



    try:

        booking_history = get_booking_groups()



    except Exception as exc:

        st.error(

            f"Could not load booking management data: {exc}"

        )





    # ---------------------------------------------------------

    # Derived booking lists

    # ---------------------------------------------------------



    active_booking_statuses = {

        "Reserved",

        "Preparing",

        "Ready for Collection",

        "Checked Out",

    }



    upcoming_bookings = [

        booking

        for booking in booking_history

        if booking["booking_status"]

        in active_booking_statuses

    ]



    historical_bookings = [

        booking

        for booking in booking_history

        if booking["booking_status"]

        in (

            "Cancelled",

            "Completed",

            "Closed - Not Supplied",

        )

    ]





    # TEMPORARY DEBUG

    # st.write(

    #     "DEBUG booking statuses:",

    #     [

    #         (

    #             booking["booking_number"],

    #             booking["booking_status"],

    #         )

    #         for booking in booking_history

    #     ],

    # )





    # ---------------------------------------------------------

    # Tabs

    # ---------------------------------------------------------



    tabs = st.tabs(

        [

            f"Bookings ({len(upcoming_bookings)})",

            f"Booking History ({len(historical_bookings)})",

        ]

    )



    # ---------------------------------------------------------

    # Upcoming Bookings

    # ---------------------------------------------------------



    with tabs[0]:



        st.subheader(

            f"Bookings "

            f"({len(upcoming_bookings)})"

        )



        if not upcoming_bookings:

            st.info(

                "There are no upcoming bookings."

            )



        else:

            for booking in upcoming_bookings:



                with st.container(border=True):



                    col1, col2, col3, col4, col5, col6 = st.columns(

                        [1.4, 2.4, 1.7, 0.8, 1.4, 1.1],

                        vertical_alignment="center",

                    )



                    # -----------------------------------------

                    # Booking

                    # -----------------------------------------



                    with col1:

                        st.write(

                            f"**{booking['booking_number']}**"

                        )

                        st.caption(

                            booking["booked_by"]

                        )



                    # -----------------------------------------

                    # Dates

                    # -----------------------------------------



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



                    # -----------------------------------------

                    # Samples

                    # -----------------------------------------



                    with col3:

                        sample_count = booking[

                            "sample_count"

                        ]



                        st.write(

                            (

                                f"**{sample_count} sample"

                                f"{'s' if sample_count != 1 else ''}**"

                            )

                        )



                        st.caption(

                            booking["team"]

                            or "No department"

                        )



                    # -----------------------------------------

                    # View

                    # -----------------------------------------



                    with col4:



                        with st.container(

                            key=(

                                f"booking_view_"

                                f"{booking['booking_group_id']}"

                            )

                        ):



                            if booking["booking_status"] == "Reserved":

                                if st.button(

                                    "Prepare Items",

                                    type="primary",

                                    width="content",

                                    key=f"prepare_booking_{booking['booking_group_id']}",

                                ):

                                    st.session_state[

                                        "selected_preparation_booking_group_id"

                                    ] = booking["booking_group_id"]



                                    st.session_state[

                                        "workflow_page"

                                    ] = "Booking Preparation"



                                    st.rerun()



                            elif booking["booking_status"] == "Preparing":

                                if st.button(

                                    "Continue Preparing",

                                    type="primary",

                                    width="content",

                                    key=f"continue_preparation_{booking['booking_group_id']}",

                                ):

                                    st.session_state[

                                        "selected_preparation_booking_group_id"

                                    ] = booking["booking_group_id"]



                                    st.session_state[

                                        "workflow_page"

                                    ] = "Booking Preparation"



                                    st.rerun()



                            elif (

                                booking["booking_status"]

                                == "Ready for Collection"

                            ):

                                if st.button(

                                    "Check Out",

                                    type="primary",

                                    width="content",

                                    key=(

                                        "checkout_booking_"

                                        f"{booking['booking_group_id']}"

                                    ),

                                ):

                                    st.session_state[

                                        "selected_preparation_booking_group_id"

                                    ] = booking["booking_group_id"]



                                    st.session_state[

                                        "workflow_page"

                                    ] = "Booking Preparation"



                                    st.rerun()





                    # -----------------------------------------

                    # Return Samples

                    # Only available after checkout

                    # -----------------------------------------



                    with col5:



                        if booking["booking_status"] == "Checked Out":



                            with st.container(

                                key=(

                                    f"booking_return_"

                                    f"{booking['booking_group_id']}"

                                )

                            ):



                                if st.button(

                                    "Return Samples",

                                    key=f"return_{booking['booking_group_id']}",

                                ):

                                    st.session_state[

                                        "selected_return_booking_group_id"

                                    ] = booking["booking_group_id"]



                                    st.session_state["workflow_page"] = (

                                        "Booking Return"

                                    )



                                    st.rerun()





                    # -----------------------------------------

                    # Print Booking Confirmation Form

                    # -----------------------------------------



                    with col6:



                        if booking["booking_status"] in (

                            "Reserved",

                            "Preparing",

                        ):



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



                                    with st.container(

                                        key=(

                                            f"booking_row_print_"

                                            f"{booking['booking_group_id']}"

                                        )

                                    ):



                                        st.download_button(

                                            "Print",

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

                                    help=str(exc),

                                    width="stretch",

                                )



        # -------------------------------------------------

        # Booking Item Lisings

        # -------------------------------------------------



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



                        st.session_state.pop(

                            "show_cancel_booking",

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



                # -------------------------------------------------

                # Booking Actions

                # -------------------------------------------------



                booking_status = str(

                    booking["booking_status"]

                ).strip()



                is_reserved = (

                    booking_status.lower()

                    == "reserved"

                )



                # -------------------------------------------------

                # Cancel Booking

                # -------------------------------------------------



                if booking["booking_status"] == "Reserved":



                    with st.container(

                        key=(

                            f"booking_cancel_"

                            f"{booking['booking_group_id']}"

                        )

                    ):



                        cancel_clicked = st.button(

                            "Cancel Booking",

                            key=(

                                f"open_cancel_booking_"

                                f"{booking['booking_group_id']}"

                            ),

                            width="stretch",

                        )



                    if cancel_clicked:

                        st.session_state[

                            "cancel_booking_group_id"

                        ] = str(

                            booking["booking_group_id"]

                        )





                # -------------------------------------------------

                # Print Booking

                # -------------------------------------------------



                with st.container(

                    key=(

                        f"booking_print_"

                        f"{booking['booking_group_id']}"

                    )

                ):



                    pdf_bytes = generate_booking_confirmation_pdf(

                        booking,

                        samples,

                    )



                    st.download_button(

                        "Print / Download Confirmation",

                        data=pdf_bytes,

                        file_name=(

                            f"{booking['booking_number']}_"

                            f"Booking_Confirmation.pdf"

                        ),

                        mime="application/pdf",

                        key=(

                            f"download_booking_"

                            f"{booking['booking_group_id']}"

                        ),

                        width="stretch",

                    )





                cancel_booking_group_id = (

                    st.session_state.get(

                        "cancel_booking_group_id"

                    )

                )



                current_booking_group_id = str(

                    booking["booking_group_id"]

                )



                if (

                    booking["booking_status"] == "Reserved"

                    and cancel_booking_group_id

                    == current_booking_group_id

                ):



                    st.markdown("### Cancel Booking")



                    st.warning(

                        (

                            f"Cancel {booking['booking_number']}? "

                            f"This will release all "

                            f"{len(samples)} samples."

                        )

                    )



                    with st.form(

                        (

                            f"cancel_booking_group_form_"

                            f"{booking['booking_group_id']}"

                        )

                    ):



                        cancelled_by = st.text_input(

                            "Cancelled By *"

                        )



                        cancellation_reason = st.selectbox(

                            "Reason *",

                            [

                                "Plan changed",

                                "Event cancelled",

                                "Different samples selected",

                                "No longer required",

                                "Other",

                            ],

                        )



                        other_reason = ""



                        if cancellation_reason == "Other":

                            other_reason = st.text_area(

                                "Other reason *"

                            )



                        confirm_cancel = (

                            st.form_submit_button(

                                "Confirm Cancellation",

                                type="primary",

                                width="stretch",

                            )

                        )



                    if confirm_cancel:



                        final_reason = (

                            other_reason.strip()

                            if cancellation_reason == "Other"

                            else cancellation_reason

                        )



                        if not cancelled_by.strip():

                            st.error(

                                "Cancelled By is required."

                            )



                        elif not final_reason:

                            st.error(

                                "Cancellation reason is required."

                            )



                        else:



                            try:

                                booking_number = (

                                    cancel_booking_group(

                                        booking_group_id=booking[

                                            "booking_group_id"

                                        ],

                                        cancelled_by=cancelled_by,

                                        reason=final_reason,

                                    )

                                )



                                st.session_state.pop(

                                    "cancel_booking_group_id",

                                    None,

                                )



                                st.session_state.pop(

                                    "selected_booking_group_id",

                                    None,

                                )



                                st.session_state[

                                    "booking_management_flash"

                                ] = {

                                    "type": "success",

                                    "message": (

                                        f"{booking_number} "

                                        "cancelled successfully."

                                    ),

                                }



                                st.rerun()



                            except Exception as exc:

                                st.error(

                                    f"Could not cancel booking: {exc}"

                                )



                # -------------------------------------------------

                # Return Inspection

                # -------------------------------------------------



                if booking["booking_status"] == "Checked Out":



                    st.markdown("### Return Inspection")



                    try:

                        return_checks = (

                            get_booking_return_checks(

                                booking[

                                    "booking_group_id"

                                ]

                            )

                        )



                    except Exception as exc:

                        st.error(

                            (

                                "Could not load return "

                                f"inspection data: {exc}"

                            )

                        )

                        return_checks = []



                    return_checks_by_item = {

                        str(check["booking_item_id"]): check

                        for check in return_checks

                    }



                    checked_count = len(

                        return_checks_by_item

                    )



                    st.caption(

                        (

                            f"{checked_count} of "

                            f"{len(samples)} samples checked"

                        )

                    )



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



                            st.write(

                                f"**{sample['sample_name']}**"

                            )



                            st.caption(

                                (

                                    f"{sample['sample_id']} · "

                                    f"{sample['location_code'] or ''} "

                                    f"{sample['location_name'] or ''}"

                                )

                            )



                            if existing_check:



                                status = existing_check[

                                    "return_status"

                                ]



                                if status == "Good":

                                    st.success(

                                        "Return checked - Good"

                                    )



                                elif status == "Damaged":

                                    st.error(

                                        "Return checked - Damaged"

                                    )



                                elif status == "Incomplete":

                                    st.warning(

                                        "Return checked - Incomplete"

                                    )



                                elif status == "Missing":

                                    st.error(

                                        "Return checked - Missing"

                                    )



                                st.caption(

                                    (

                                        "Checked by "

                                        f"{existing_check['checked_by']}"

                                    )

                                )



                            inspect_key = (

                                f"inspect_return_"

                                f"{booking_item_id}"

                            )



                            if st.button(

                                (

                                    "Update Return Check"

                                    if existing_check

                                    else "Check Return"

                                ),

                                key=inspect_key,

                                width="stretch",

                            ):



                                st.session_state[

                                    "return_inspection_item_id"

                                ] = booking_item_id



                            selected_return_item = (

                                st.session_state.get(

                                    "return_inspection_item_id"

                                )

                            )



                            if (

                                selected_return_item

                                == booking_item_id

                            ):



                                with st.form(

                                    (

                                        f"return_form_"

                                        f"{booking_item_id}"

                                    )

                                ):



                                    return_status = (

                                        st.radio(

                                            "Return Status *",

                                            [

                                                "Good",

                                                "Damaged",

                                                "Incomplete",

                                                "Missing",

                                            ],

                                            horizontal=True,

                                        )

                                    )



                                    damage_details = None

                                    missing_details = None



                                    if (

                                        return_status

                                        == "Damaged"

                                    ):



                                        damage_details = (

                                            st.text_area(

                                                "Describe the damage *"

                                            )

                                        )



                                    elif (

                                        return_status

                                        == "Incomplete"

                                    ):



                                        missing_details = (

                                            st.text_area(

                                                (

                                                    "What part or "

                                                    "component is missing? *"

                                                )

                                            )

                                        )



                                    elif (

                                        return_status

                                        == "Missing"

                                    ):



                                        missing_details = (

                                            st.text_area(

                                                (

                                                    "Missing item "

                                                    "details"

                                                )

                                            )

                                        )



                                    checked_by = (

                                        st.text_input(

                                            "Checked By *"

                                        )

                                    )



                                    return_notes = (

                                        st.text_area(

                                            "Notes"

                                        )

                                    )



                                    save_return = (

                                        st.form_submit_button(

                                            "Save Return Check",

                                            type="primary",

                                            width="stretch",

                                        )

                                    )



                                if save_return:



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

                                            checked_by=checked_by,

                                            damage_details=damage_details,

                                            missing_details=missing_details,

                                            notes=return_notes,

                                        )



                                        st.session_state.pop(

                                            "return_inspection_item_id",

                                            None,

                                        )



                                        st.session_state[

                                            "booking_management_flash"

                                        ] = {

                                            "type": "success",

                                            "message": (

                                                f"Return check saved "

                                                f"for "

                                                f"{sample['sample_id']}."

                                            ),

                                        }



                                        st.rerun()



                                    except Exception as exc:



                                        st.error(

                                            (

                                                "Could not save "

                                                "return check: "

                                                f"{exc}"

                                            )

                                        )





        # ---------------------------------------------------------

        # Booking History

        # ---------------------------------------------------------



        with tabs[1]:



            st.subheader(

                f"Booking History ({len(historical_bookings)})"

            )



            if not historical_bookings:

                st.info("No booking history available.")



            else:

                for booking in historical_bookings:



                    booking_group_id = booking["booking_group_id"]

                    booking_status = booking["booking_status"]

                    sample_count = booking["sample_count"]



                    with st.container(border=True):



                        # -----------------------------------------

                        # Booking summary

                        # -----------------------------------------



                        col1, col2, col3 = st.columns(

                            [2, 3, 2],

                            vertical_alignment="center",

                        )



                        with col1:

                            st.write(

                                f"**{booking['booking_number']}**"

                            )

                            st.caption(booking_status)



                        with col2:

                            st.write(

                                f"{booking['start_date']:%d %b %Y}"

                                f" → "

                                f"{booking['end_date']:%d %b %Y}"

                            )

                            st.caption(booking["booked_by"])



                        with col3:

                            st.write(

                                f"{sample_count} requested sample"

                                f"{'s' if sample_count != 1 else ''}"

                            )



                        # -----------------------------------------

                        # Individual booking outcomes

                        # -----------------------------------------



                        with st.expander(

                            "View Booking Details",

                            expanded=False,

                        ):



                            try:

                                history_items = (

                                    get_booking_history_items(

                                        booking_group_id

                                    )

                                )



                            except Exception as exc:

                                st.error(

                                    f"Could not load booking items: {exc}"

                                )

                                history_items = []



                            if history_items:



                                supplied_count = sum(

                                    1

                                    for item in history_items

                                    if item["preparation_status"]

                                    in ("Prepared", "Replaced")

                                    and item["item_booking_status"]

                                    != "Cancelled"

                                )



                                not_supplied_count = sum(

                                    1

                                    for item in history_items

                                    if item["preparation_status"]

                                    in ("Missing", "Cannot Supply")

                                )



                                # ---------------------------------

                                # Summary counts

                                # ---------------------------------



                                if (

                                    booking_status

                                    == "Closed - Not Supplied"

                                ):



                                    m1, m2, m3 = st.columns(3)



                                    m1.metric(

                                        "Requested",

                                        len(history_items),

                                    )



                                    m2.metric(

                                        "Supplied",

                                        supplied_count,

                                    )



                                    m3.metric(

                                        "Not Supplied",

                                        not_supplied_count,

                                    )



                                    st.caption(

                                        "No collection or return required."

                                    )



                                # ---------------------------------

                                # Requested items

                                # ---------------------------------



                                st.markdown("**Requested Samples**")



                                for item in history_items:



                                    sample_id = item["sample_id"]

                                    sample_name = item["sample_name"]

                                    preparation_status = (

                                        item["preparation_status"]

                                        or "Not Recorded"

                                    )



                                    item_col1, item_col2 = (

                                        st.columns([4, 1])

                                    )



                                    with item_col1:

                                        st.write(

                                            f"**{sample_id}** — "

                                            f"{sample_name}"

                                        )



                                    with item_col2:

                                        st.caption(

                                            preparation_status

                                        )



                                    if preparation_status in (

                                        "Missing",

                                        "Cannot Supply",

                                    ):

                                        if item["missing_note"]:

                                            st.caption(

                                                f"Reason: "

                                                f"{item['missing_note']}"

                                            )



                            else:

                                st.caption(

                                    "No booking items found."

                                )