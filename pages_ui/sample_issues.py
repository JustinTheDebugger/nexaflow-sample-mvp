import streamlit as st

from repositories.sample_repository import (
    get_sample_issues,
)

def _sample_state_badge(asset_state):
    state = asset_state or "Unknown"

    css_class = {
        "Active": "sample-state-active",
        "Damaged": "sample-state-damaged",
        "Inactive": "sample-state-inactive",
        "Lost": "sample-state-lost",
        "Retired": "sample-state-retired",
    }.get(
        state,
        "sample-state-inactive",
    )

    return (
        f'<span class="sample-state-badge '
        f'{css_class}">'
        f'{state.upper()}'
        "</span>"
    )

def _issue_type_badge(issue_type):
    issue_type = issue_type or "Unknown"

    css_class = {
        "Damaged": "issue-type-damaged",
        "Incomplete": "issue-type-incomplete",
        "Not Returned": "issue-type-not-returned",
    }.get(
        issue_type,
        "issue-type-incomplete",
    )

    return (
        f'<span class="issue-type-badge '
        f'{css_class}">'
        f'{issue_type.upper()}'
        "</span>"
    )

def render_sample_issues_page(hero):
    """
    Display samples requiring operational follow-up.
    """

    hero(
        "Sample Issues",
        (
            "Review damaged, incomplete, and "
            "not-returned samples requiring attention."
        ),
    )

    st.markdown(
        """
        <style>
        .sample-state-badge {
            display: inline-block;
            padding: 3px 9px;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            line-height: 1.2;
            margin-left: 8px;
        }

        .sample-state-active {
            background: #dcfce7;
            color: #166534;
        }

        .sample-state-damaged {
            background: #fee2e2;
            color: #991b1b;
        }

        .sample-state-inactive {
            background: #fef3c7;
            color: #92400e;
        }

        .sample-state-lost {
            background: #f3f4f6;
            color: #374151;
        }

        .sample-state-retired {
            background: #e5e7eb;
            color: #1f2937;
        }

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
        </style>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------
    # Flash message
    # -------------------------------------------------

    flash = st.session_state.pop(
        "sample_issue_flash",
        None,
    )

    if flash:
        message_type = flash.get(
            "type",
            "success",
        )

        message = flash.get(
            "message",
            "",
        )

        if message_type == "error":
            st.error(message)
        elif message_type == "warning":
            st.warning(message)
        else:
            st.success(message)

    # -------------------------------------------------
    # Load issues
    # -------------------------------------------------

    try:
        issues = get_sample_issues()

    except Exception as exc:
        st.error(
            f"Could not load sample issues: {exc}"
        )
        return

    # -------------------------------------------------
    # Summary
    # -------------------------------------------------

    damaged_count = sum(
        1
        for issue in issues
        if issue["issue_type"] == "Damaged"
    )

    incomplete_count = sum(
        1
        for issue in issues
        if issue["issue_type"] == "Incomplete"
    )

    not_returned_count = sum(
        1
        for issue in issues
        if issue["issue_type"] == "Not Returned"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Open Issues",
        len(issues),
    )

    col2.metric(
        "Damaged",
        damaged_count,
    )

    col3.metric(
        "Incomplete",
        incomplete_count,
    )

    col4.metric(
        "Not Returned",
        not_returned_count,
    )

    st.divider()

    # -------------------------------------------------
    # No issues
    # -------------------------------------------------

    if not issues:
        st.success(
            "There are currently no open sample issues."
        )
        return

    # -------------------------------------------------
    # Issue list
    # -------------------------------------------------

    st.subheader(
        f"Open Issues ({len(issues)})"
    )

    for issue in issues:

        issue_id = str(
            issue["issue_id"]
        )

        with st.container(
            border=True,
            key=f"sample_issue_{issue_id}",
        ):

            left, middle, right = st.columns(
                [3.2, 2.0, 1.2],
                vertical_alignment="top",
            )

            with left:

                if issue["reported_at"]:
                    issue_date = (
                        issue["reported_at"]
                        .astimezone()
                        .strftime("%d %b %Y")
                    )

                    st.caption(
                        f"Issue raised: {issue_date}"
                    )

                st.markdown(
                    f"**{issue['sample_name']}**"
                )

                st.caption(
                    issue["sample_id"]
                )

                if issue["description"]:
                    st.write(
                        issue["description"]
                    )

            with middle:

                st.markdown(
                    _issue_type_badge(
                        issue["issue_type"]
                    ),
                    unsafe_allow_html=True,
                )

                st.caption(
                    (
                        "Status: "
                        f"{issue['issue_status']}"
                    )
                )

                if issue["booking_number"]:
                    st.caption(
                        (
                            "Reported from "
                            f"{issue['booking_number']}"
                        )
                    )

                if issue["issue_type"] == "Not Returned":
                    st.caption(
                        "Location: Not returned"
                    )

                elif issue["location_name"]:
                    st.caption(
                        (
                            "Location: "
                            f"{issue['location_name']}"
                        )
                    )

            with right:

                if st.button(
                    "View Issue",
                    key=f"view_issue_{issue_id}",
                    width="stretch",
                ):
                    st.session_state[
                        "selected_sample_issue_id"
                    ] = issue_id

                    st.session_state[
                        "workflow_page"
                    ] = "Sample Issue Detail"

                    st.rerun()