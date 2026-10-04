import streamlit as st

from repositories.sample_repository import (
    get_sample_activity,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _format_datetime(value):
    """Format an event timestamp for display."""

    if not value:
        return "Date unavailable"

    return value.strftime(
        "%d %b %Y · %H:%M"
    )


def _event_label(event):
    """Return a readable event title."""

    if event.get("title"):
        return event["title"]

    event_type = (
        event.get("event_type")
        or "Activity"
    )

    return (
        event_type
        .replace("_", " ")
        .title()
    )


def _format_location(code, name):
    """Format one sample location."""

    if code and name:
        return f"{code} — {name}"

    return code or name


def _location_text(event):
    """Build readable location movement text."""

    previous_location = _format_location(
        event.get(
            "previous_location_code"
        ),
        event.get(
            "previous_location_name"
        ),
    )

    new_location = _format_location(
        event.get(
            "new_location_code"
        ),
        event.get(
            "new_location_name"
        ),
    )

    if previous_location and new_location:
        return (
            f"{previous_location} → "
            f"{new_location}"
        )

    if new_location:
        return (
            f"Moved to {new_location}"
        )

    if previous_location:
        return (
            f"From {previous_location}"
        )

    return None


def _actor_text(event):
    """Build actor/team information."""

    actor = event.get("actor")
    team = event.get("team")

    if actor and team:
        return f"{actor} · {team}"

    return actor or team


# ------------------------------------------------------------------
# Event card
# ------------------------------------------------------------------

def _render_event_card(event):
    """Render one timeline event."""

    with st.container(
        border=True
    ):

        st.markdown(
            f"**{_event_label(event)}**"
        )

        st.caption(
            _format_datetime(
                event.get("event_date")
            )
        )

        details = event.get(
            "details"
        )

        if details:
            st.write(
                details
            )

        location = _location_text(
            event
        )

        if location:
            st.caption(
                f"📍 {location}"
            )

        actor = _actor_text(
            event
        )

        if actor:
            st.caption(
                f"By {actor}"
            )


# ------------------------------------------------------------------
# Sample Activity Timeline
# ------------------------------------------------------------------

def render_sample_activity(
    sample_record_id,
):
    """
    Render the complete activity history
    for one sample.

    Events are displayed newest first.
    """

    events = get_sample_activity(
        sample_record_id
    )

    if not events:
        st.info(
            "No activity has been recorded "
            "for this sample yet."
        )
        return

    # --------------------------------------------------------------
    # Summary
    # --------------------------------------------------------------

    event_count = len(
        events
    )

    st.caption(
        (
            f"{event_count} "
            f"event{'s' if event_count != 1 else ''}"
            " recorded"
        )
    )

    st.write("")

    # --------------------------------------------------------------
    # Timeline
    # --------------------------------------------------------------

    for index, event in enumerate(
        events
    ):

        left_col, line_col, right_col = (
            st.columns(
                [5, 0.7, 5]
            )
        )

        # Alternate event cards
        if index % 2 == 0:

            with left_col:
                _render_event_card(
                    event
                )

            with line_col:
                st.markdown(
                    """
                    <div style="
                        text-align:center;
                        font-size:20px;
                        color:#17365d;
                        padding-top:18px;
                    ">
                        ●
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:

            with line_col:
                st.markdown(
                    """
                    <div style="
                        text-align:center;
                        font-size:20px;
                        color:#17365d;
                        padding-top:18px;
                    ">
                        ●
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with right_col:
                _render_event_card(
                    event
                )