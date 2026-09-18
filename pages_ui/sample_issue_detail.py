import streamlit as st

from repositories.sample_repository import (
    add_sample_issue_media,
    complete_sample_repair,
    get_sample_issue_details,
    get_sample_issue_media,
    get_sample_issue_repair,
    get_sample_locations,
    retire_sample_from_issue,
    start_sample_repair,
)


def _issue_type_badge(issue_type):
    issue_type = issue_type or "Unknown"

    css_class = {
        "Damaged": "issue-type-damaged",
        "Incomplete": "issue-type-incomplete",
        "Not Returned": "issue-type-not-returned",
    }.get(
        issue_type,
        "issue-type-default",
    )

    return (
        f'<span class="issue-type-badge {css_class}">'
        f"{issue_type.upper()}"
        "</span>"
    )


def _format_date(value):
    if not value:
        return "—"

    if hasattr(value, "astimezone"):
        value = value.astimezone()

    return value.strftime("%d %b %Y")


def render_sample_issue_detail_page(hero):

    hero(
        "Sample Issue Detail",
        "Review the issue, evidence, and resolution progress.",
    )

    st.markdown(
        """
        <style>
        .issue-type-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 700;
            line-height: 1.2;
        }

        .issue-type-damaged {
            background: #fee2e2;
            color: #991b1b;
        }

        .issue-type-incomplete {
            background: #fef3c7;
            color: #92400e;
        }

        .issue-type-not-returned {
            background: #e0e7ff;
            color: #3730a3;
        }

        .issue-type-default {
            background: #f3f4f6;
            color: #374151;
        }

        .issue-section {
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    issue_id = st.session_state.get(
        "selected_sample_issue_id"
    )

    if not issue_id:
        st.warning("No sample issue has been selected.")

        if st.button("Back to Sample Issues"):
            st.session_state.pop(
                "workflow_page",
                None,
            )
            st.rerun()

        return

    issue = get_sample_issue_details(
        issue_id
    )

    repair = get_sample_issue_repair(
        issue_id
    )

    if not issue:
        st.error(
            "The selected sample issue could not be found."
        )

        if st.button("Back to Sample Issues"):
            st.session_state.pop(
                "selected_sample_issue_id",
                None,
            )
            st.session_state.pop(
                "workflow_page",
                None,
            )
            st.rerun()

        return

    #
    # Back
    #

    if st.button(
        "← Back to Sample Issues",
        key="back_to_sample_issues",
    ):
        st.session_state.pop(
            "selected_sample_issue_id",
            None,
        )
        st.session_state.pop(
            "workflow_page",
            None,
        )
        st.rerun()

    #
    # Sample heading
    #

    st.caption(
        f"Issue raised: "
        f"{_format_date(issue['reported_at'])}"
    )

    st.subheader(
        issue["sample_name"]
    )

    st.caption(
        issue["sample_id"]
    )

    st.markdown(
        _issue_type_badge(
            issue["issue_type"]
        ),
        unsafe_allow_html=True,
    )

    st.write("")

    #
    # Current issue status
    #

    status_col, location_col, booking_col = (
        st.columns(
            3,
            vertical_alignment="top",
        )
    )

    with status_col:
        st.caption("ISSUE STATUS")
        st.write(
            f"**{issue['issue_status']}**"
        )

    with location_col:
        st.caption("CURRENT LOCATION")

        if issue["issue_type"] == "Not Returned":
            st.write("**Not returned**")

        elif issue["location_name"]:
            st.write(
                f"**{issue['location_name']}**"
            )

            if issue["location_code"]:
                st.caption(
                    issue["location_code"]
                )
        else:
            st.write("—")

    with booking_col:
        st.caption("REPORTED FROM")

        if issue["booking_number"]:
            st.write(
                f"**{issue['booking_number']}**"
            )
        else:
            st.write("—")

    st.divider()

    #
    # Issue
    #

    st.subheader("Issue")

    issue_left, issue_right = st.columns(
        [2, 1],
        vertical_alignment="top",
    )

    with issue_left:
        st.caption("DESCRIPTION")

        if issue["description"]:
            st.write(
                issue["description"]
            )
        else:
            st.write(
                "No issue description was provided."
            )

        if issue["return_notes"]:
            st.caption("RETURN NOTES")
            st.write(
                issue["return_notes"]
            )

    with issue_right:
        st.caption("REPORTED BY")
        st.write(
            issue["reported_by"] or "—"
        )

        st.caption("RETURN CHECKED BY")
        st.write(
            issue["checked_by"] or "—"
        )

        st.caption("RETURN CHECKED")
        st.write(
            _format_date(
                issue["checked_at"]
            )
        )

    #
    # Booking context
    #

    if issue["booking_number"]:
        st.divider()
        st.subheader("Booking")

        col1, col2, col3 = st.columns(
            3,
            vertical_alignment="top",
        )

        with col1:
            st.caption("BOOKING")
            st.write(
                issue["booking_number"]
            )

            st.caption("REQUESTED BY")
            st.write(
                issue["booked_by"] or "—"
            )

        with col2:
            st.caption("TEAM")
            st.write(
                issue["booking_team"] or "—"
            )

            st.caption("PURPOSE")
            st.write(
                issue["booking_purpose"] or "—"
            )

        with col3:
            st.caption("BOOKED FROM")
            st.write(
                _format_date(
                    issue["booking_start_date"]
                )
            )

            st.caption("BOOKED TO")
            st.write(
                _format_date(
                    issue["booking_end_date"]
                )
            )

    #
    # Evidence placeholder
    #

    st.divider()
    st.subheader("Damage Evidence")

    if issue["issue_type"] == "Damaged":
        st.info(
            "No damage photos have been added yet."
        )

        st.button(
            "Add Photos",
            disabled=True,
            help=(
                "Photo upload will be added "
                "in the next step."
            ),
        )

    else:
        st.caption(
            "Photo evidence is not required "
            "for this issue."
        )

    #
    # Action placeholder
    #

    #
    # Resolution
    #

    st.divider()
    st.subheader("Resolution")

    if (
        issue["issue_type"] == "Damaged"
        and issue["issue_status"] == "Open"
    ):

        st.write(
            "Review the damage evidence and decide "
            "how this sample should proceed."
        )

        repair_tab, retire_tab = st.tabs(
            [
                "Send for Repair",
                "Retire Sample",
            ]
        )

        #
        # Send for Repair
        #

        with repair_tab:

            st.caption(
                "Move this sample into the repair workflow."
            )

            repair_started_by = st.text_input(
                "Started by",
                key=(
                    "repair_started_by_"
                    f"{issue['issue_id']}"
                ),
            )

            repair_notes = st.text_area(
                "Repair instructions / notes",
                placeholder=(
                    "e.g. Replace damaged rear pole "
                    "and inspect surrounding fittings."
                ),
                key=(
                    "repair_notes_"
                    f"{issue['issue_id']}"
                ),
            )

            if st.button(
                "Send for Repair",
                type="primary",
                key=(
                    "start_repair_"
                    f"{issue['issue_id']}"
                ),
            ):

                if not repair_started_by.strip():
                    st.error(
                        "Please enter who is "
                        "starting the repair."
                    )

                else:
                    try:
                        start_sample_repair(
                            issue_id=issue["issue_id"],
                            started_by=(
                                repair_started_by
                            ),
                            repair_notes=repair_notes,
                        )

                        st.success(
                            "Sample sent for repair."
                        )

                        st.rerun()

                    except Exception as exc:
                        st.error(
                            f"Could not start repair: {exc}"
                        )

        #
        # Retire Sample
        #

        with retire_tab:

            st.warning(
                "Retiring removes this sample from "
                "the active sample pool."
            )

            retired_by = st.text_input(
                "Retired by",
                key=(
                    "retired_by_"
                    f"{issue['issue_id']}"
                ),
            )

            retirement_reason = st.text_area(
                "Reason for retirement",
                placeholder=(
                    "e.g. Damage is beyond economical repair."
                ),
                key=(
                    "retirement_reason_"
                    f"{issue['issue_id']}"
                ),
            )

            confirm_retirement = st.checkbox(
                "I confirm this sample should be retired.",
                key=(
                    "confirm_retirement_"
                    f"{issue['issue_id']}"
                ),
            )

            if st.button(
                "Retire Sample",
                key=(
                    "retire_sample_"
                    f"{issue['issue_id']}"
                ),
            ):

                if not retired_by.strip():
                    st.error(
                        "Please enter who is "
                        "retiring the sample."
                    )

                elif not retirement_reason.strip():
                    st.error(
                        "Please enter the reason "
                        "for retirement."
                    )

                elif not confirm_retirement:
                    st.error(
                        "Please confirm the retirement."
                    )

                else:
                    try:
                        retire_sample_from_issue(
                            issue_id=issue["issue_id"],
                            retired_by=retired_by,
                            reason=retirement_reason,
                        )

                        st.success(
                            "Sample retired."
                        )

                        st.rerun()

                    except Exception as exc:
                        st.error(
                            f"Could not retire sample: {exc}"
                        )


    elif (
        issue["issue_type"] == "Damaged"
        and issue["issue_status"] == "Under Repair"
    ):

        if not repair:
            st.error(
                "This issue is marked Under Repair, "
                "but no active repair record was found."
            )

        else:

            #
            # Current repair
            #

            st.markdown("### Repair")

            repair_col1, repair_col2 = st.columns(
                2,
                vertical_alignment="top",
            )

            with repair_col1:
                st.caption("REPAIR STATUS")
                st.write(
                    f"**{repair['repair_status']}**"
                )

                st.caption("STARTED BY")
                st.write(
                    repair["repair_started_by"]
                    or "—"
                )

            with repair_col2:
                st.caption("STARTED")
                st.write(
                    _format_date(
                        repair["repair_started_at"]
                    )
                )

                st.caption("CURRENT LOCATION")
                st.write(
                    issue["location_name"]
                    or "—"
                )

            if repair["repair_notes"]:
                st.caption("REPAIR INSTRUCTIONS")
                st.write(
                    repair["repair_notes"]
                )

            st.divider()

            #
            # Complete repair
            #

            st.markdown("### Complete Repair")

            completed_by = st.text_input(
                "Completed by",
                key=(
                    "repair_completed_by_"
                    f"{issue['issue_id']}"
                ),
            )

            completion_notes = st.text_area(
                "Work completed",
                placeholder=(
                    "e.g. Rear pole replaced. "
                    "Tent erected and inspected. "
                    "No further damage found."
                ),
                key=(
                    "repair_completion_notes_"
                    f"{issue['issue_id']}"
                ),
            )

            final_disposition = st.radio(
                "Final disposition",
                [
                    "Return to Sample Pool",
                    "Convert to Refurbished",
                    "Retire",
                ],
                key=(
                    "repair_disposition_"
                    f"{issue['issue_id']}"
                ),
            )

            return_location_id = None

            #
            # Return to sample pool
            #

            if (
                final_disposition
                == "Return to Sample Pool"
            ):

                locations = get_sample_locations()

                available_locations = [
                    location
                    for location in locations
                    if location["code"] != "H1"
                ]

                if not available_locations:
                    st.error(
                        "No active sample-room "
                        "locations are available."
                    )

                else:
                    selected_location = st.selectbox(
                        "Return location",
                        options=available_locations,
                        format_func=lambda location: (
                            f"{location['code']} — "
                            f"{location['name']}"
                        ),
                        key=(
                            "repair_return_location_"
                            f"{issue['issue_id']}"
                        ),
                    )

                    return_location_id = (
                        selected_location["id"]
                    )

                st.info(
                    "The sample will be restored to "
                    "Good / Active and returned to "
                    "the selected sample location."
                )

            #
            # Convert to refurbished
            #

            elif (
                final_disposition
                == "Convert to Refurbished"
            ):

                st.warning(
                    "The sample will leave the active "
                    "sample pool. Its history will be "
                    "preserved for the future "
                    "Refurbished Items workflow."
                )

            #
            # Retire
            #

            else:

                st.warning(
                    "The sample will be retired and "
                    "removed from the active sample pool."
                )

            confirm_completion = st.checkbox(
                "I confirm the repair is complete "
                "and the selected disposition is correct.",
                key=(
                    "confirm_repair_completion_"
                    f"{issue['issue_id']}"
                ),
            )

            if st.button(
                "Complete Repair",
                type="primary",
                key=(
                    "complete_repair_"
                    f"{issue['issue_id']}"
                ),
            ):

                if not completed_by.strip():
                    st.error(
                        "Please enter who completed "
                        "the repair."
                    )

                elif not completion_notes.strip():
                    st.error(
                        "Please describe the work "
                        "completed."
                    )

                elif (
                    final_disposition
                    == "Return to Sample Pool"
                    and not return_location_id
                ):
                    st.error(
                        "Please select the return "
                        "location."
                    )

                elif not confirm_completion:
                    st.error(
                        "Please confirm the repair "
                        "completion."
                    )

                else:
                    try:
                        complete_sample_repair(
                            issue_id=issue["issue_id"],
                            completed_by=completed_by,
                            completion_notes=(
                                completion_notes
                            ),
                            final_disposition=(
                                final_disposition
                            ),
                            return_location_id=(
                                return_location_id
                            ),
                        )

                        st.success(
                            "Repair completed."
                        )

                        st.rerun()

                    except Exception as exc:
                        st.error(
                            "Could not complete "
                            f"repair: {exc}"
                        )


    elif issue["issue_status"] in (
        "Resolved",
        "Retired",
        "Converted to Refurbished",
    ):

        st.success(
            f"This issue is {issue['issue_status']}."
        )

        if issue["resolution_action"]:
            st.write(
                "**Resolution:** "
                f"{issue['resolution_action']}"
            )

        if issue["resolution_notes"]:
            st.write(
                issue["resolution_notes"]
            )

        if issue["resolved_by"]:
            st.caption(
                (
                    f"Resolved by "
                    f"{issue['resolved_by']} · "
                    f"{_format_date(issue['resolved_at'])}"
                )
            )


    elif issue["issue_type"] == "Incomplete":

        st.info(
            "This sample is on hold until the "
            "missing component is replenished."
        )


    elif issue["issue_type"] == "Not Returned":

        st.info(
            "This sample remains unresolved until "
            "it is found/returned or retired."
        )