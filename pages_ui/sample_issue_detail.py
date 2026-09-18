import streamlit as st

from repositories.sample_repository import (
    get_sample_issue_details,
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

    st.divider()
    st.subheader("Resolution")

    if issue["issue_status"] == "Open":

        if issue["issue_type"] == "Damaged":
            st.info(
                "Review the damage before deciding "
                "whether to repair or retire this sample."
            )

        elif issue["issue_type"] == "Incomplete":
            st.info(
                "This sample is being held until the "
                "missing component can be replenished."
            )

        elif issue["issue_type"] == "Not Returned":
            st.info(
                "This sample remains unresolved until "
                "it is found, returned, or retired."
            )

    else:
        st.write(
            f"Current workflow status: "
            f"**{issue['issue_status']}**"
        )