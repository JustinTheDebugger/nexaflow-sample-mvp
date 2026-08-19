from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

from data import SAMPLES, BOOKINGS, TIMELINE, ACTIVITY, samples_df, bookings_df, timeline_df
from styles import apply_styles

st.set_page_config(
    page_title="NexaFlow Asset Tracking",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()

samples = samples_df()
bookings = bookings_df()
timeline = timeline_df()
today = date.today()

with st.sidebar:
    st.markdown("## ◈ NexaFlow")
    st.caption("Asset Tracking & Operational Visibility")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["Executive Dashboard", "Sample Search", "Sample Detail", "QR Action Hub"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Executive Demo · Streamlit MVP")

def hero(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def metric_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def info_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-label">{label}</div>
            <div class="info-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def sample_selector(key: str):
    labels = {
        f"{row.product_name} · {row.sample_id}": row.sample_id
        for row in samples.itertuples()
    }
    selection = st.selectbox("Select sample", list(labels.keys()), key=key)
    return samples[samples["sample_id"] == labels[selection]].iloc[0]

def availability_text(sample):
    if sample["next_available"] <= today:
        if pd.notna(sample["next_booking"]):
            days = (sample["next_booking"] - today).days
            return f"Available now · next booking in {days} day(s)"
        return "Available now · no upcoming booking"

    days = (sample["next_available"] - today).days
    return f"Available in {days} day(s) · {sample['next_available'].strftime('%d %b')}"

if page == "Executive Dashboard":
    hero(
        "Executive Asset Dashboard",
        "A live view of where physical samples are, who has them, and when they will be available.",
    )

    total = len(samples)
    available = int((samples["next_available"] <= today).sum())
    checked_out = int(samples["status"].isin(["Checked Out", "In Use"]).sum())
    overdue = int((samples["status"] == "Overdue").sum())
    damaged = int((samples["condition"] == "Damaged").sum())
    upcoming = int((bookings["start"] >= today).sum())

    cols = st.columns(6)
    values = [
        ("Total Samples", total),
        ("Available Today", available),
        ("Checked Out", checked_out),
        ("Overdue", overdue),
        ("Damaged", damaged),
        ("Upcoming Reservations", upcoming),
    ]
    for col, (label, value) in zip(cols, values):
        with col:
            metric_card(label, str(value))

    st.markdown("### Operational visibility")
    left, right = st.columns([1.2, 1])

    with left:
        location_counts = (
            samples.assign(
                asset_location=samples["holder_team"].replace(
                    {"Operations": "Warehouse"}
                )
            )
            .groupby("asset_location")
            .size()
            .reset_index(name="Samples")
        )
        fig = px.bar(
            location_counts,
            x="Samples",
            y="asset_location",
            orientation="h",
            text="Samples",
            labels={"asset_location": "Current asset location"},
        )
        fig.update_layout(
            height=330,
            margin=dict(l=10, r=10, t=20, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("#### Recent activity")
        for item in ACTIVITY:
            st.markdown(
                f"""
                <div class="info-card" style="margin-bottom:.65rem;">
                    <div class="info-label">{item['time']} · {item['type']}</div>
                    <div class="info-value">{item['action']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Management attention")
    attention = samples[
        samples["status"].isin(["Overdue", "Damaged"])
    ][["sample_id", "product_name", "status", "holder", "location", "condition"]]
    st.dataframe(attention, use_container_width=True, hide_index=True)

elif page == "Sample Search":
    hero(
        "Find a Sample",
        "Search by product, sample ID, category, holder, or location. Availability is calculated from bookings.",
    )

    query = st.text_input(
        "Search",
        placeholder="Try: Aerospeed, Marketing, Warehouse B, SMP-001...",
    )

    filtered = samples.copy()
    if query:
        searchable = filtered.astype(str).agg(" ".join, axis=1).str.lower()
        filtered = filtered[searchable.str.contains(query.lower(), na=False)]

    status_filter = st.multiselect(
        "Operational state",
        sorted(samples["status"].unique()),
        default=[],
    )
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]

    st.caption(f"{len(filtered)} sample(s) found")

    for _, sample in filtered.iterrows():
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([2.2, 1.3, 1.5, 1])
            with col1:
                st.markdown(f"### {sample['product_name']}")
                st.caption(f"{sample['sample_id']} · {sample['product_code']}")
                st.write(availability_text(sample))
            with col2:
                st.markdown("**Current holder**")
                st.write(sample["holder"])
                st.caption(sample["holder_team"])
            with col3:
                st.markdown("**Location**")
                st.write(sample["location"])
                st.caption(f"Condition: {sample['condition']}")
            with col4:
                st.markdown("**Next booking**")
                if pd.notna(sample["next_booking"]):
                    st.write(sample["next_booking"].strftime("%d %b"))
                    st.caption(sample["next_booking_team"])
                else:
                    st.write("None")
                    st.caption("No booking")

elif page == "Sample Detail":
    hero(
        "Sample Operational Dashboard",
        "One screen answering the essential operational questions for each physical asset.",
    )

    sample = sample_selector("detail_selector")

    top_left, top_right = st.columns([1.15, 2])
    with top_left:
        st.image(sample["photo"], use_container_width=True)
        st.markdown(f"### {sample['product_name']}")
        st.caption(f"{sample['sample_id']} · {sample['product_code']}")
        st.markdown(f"<span class='status'>{sample['status']}</span>", unsafe_allow_html=True)
        st.write(sample["notes"])

    with top_right:
        row1 = st.columns(3)
        with row1[0]:
            info_card("Current holder", f"{sample['holder']} · {sample['holder_team']}")
        with row1[1]:
            info_card("Current location", sample["location"])
        with row1[2]:
            info_card("Availability", availability_text(sample))

        st.write("")
        row2 = st.columns(3)
        with row2[0]:
            next_booking = (
                f"{sample['next_booking'].strftime('%d %b')} · {sample['next_booking_team']}"
                if pd.notna(sample["next_booking"])
                else "No upcoming booking"
            )
            info_card("Next booking", next_booking)
        with row2[1]:
            info_card("Condition", sample["condition"])
        with row2[2]:
            info_card("Usage / inspection", f"{sample['usage_count']} uses · {sample['last_inspection'].strftime('%d %b')}")

    tabs = st.tabs(["Booking Calendar", "Timeline", "Operational History"])

    with tabs[0]:
        sample_bookings = bookings[bookings["sample_id"] == sample["sample_id"]].copy()

        calendar_days = []
        for offset in range(14):
            day = today + timedelta(days=offset)
            matches = sample_bookings[
                (sample_bookings["start"] <= day)
                & (sample_bookings["end"] >= day)
            ]
            if matches.empty:
                calendar_days.append(
                    {"Date": day.strftime("%a %d %b"), "State": "Available", "Holder": "Warehouse"}
                )
            else:
                booking = matches.iloc[0]
                calendar_days.append(
                    {"Date": day.strftime("%a %d %b"), "State": "Booked", "Holder": booking["team"]}
                )

        cal_df = pd.DataFrame(calendar_days)
        st.dataframe(cal_df, use_container_width=True, hide_index=True)

        st.markdown("#### Upcoming bookings")
        if sample_bookings.empty:
            st.info("No bookings recorded.")
        else:
            display = sample_bookings.copy()
            display["Period"] = (
                display["start"].apply(lambda x: x.strftime("%d %b"))
                + " – "
                + display["end"].apply(lambda x: x.strftime("%d %b"))
            )
            st.dataframe(
                display[["Period", "team", "purpose"]],
                use_container_width=True,
                hide_index=True,
            )

    with tabs[1]:
        sample_timeline = (
            timeline[timeline["sample_id"] == sample["sample_id"]]
            .sort_values("date", ascending=False)
        )

        for _, event in sample_timeline.iterrows():
            st.markdown(
                f"""
                <div class="timeline-item">
                    <div class="timeline-date">{event['date'].strftime('%d %b %Y')}</div>
                    <div class="timeline-title">{event['event']}</div>
                    <div class="small-muted">{event['detail']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tabs[2]:
        history = sample_timeline[["date", "event", "detail"]].copy()
        history["date"] = history["date"].apply(lambda x: x.strftime("%d %b %Y"))
        st.dataframe(history, use_container_width=True, hide_index=True)

elif page == "QR Action Hub":
    hero(
        "QR Action Hub",
        "Scanning the tag should help staff perform an action, not merely confirm that the sample exists.",
    )

    sample = sample_selector("action_selector")

    st.markdown(f"### {sample['product_name']}")
    st.caption(f"{sample['sample_id']} · {sample['location']}")
    st.write(availability_text(sample))

    st.markdown("### What would you like to do?")
    action_cols = st.columns(3)
    actions = [
        ("Check Out", "Assign the sample to a person or team."),
        ("Return Sample", "Record the return and confirm its location."),
        ("Move Location", "Update warehouse, rack, bin, or external location."),
        ("Report Damage", "Record condition, description, and evidence."),
        ("Upload Photo", "Add a current condition or location photo."),
        ("View Timeline", "Review the asset's complete lifecycle."),
    ]

    for idx, (label, description) in enumerate(actions):
        with action_cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"#### {label}")
                st.caption(description)
                if st.button(label, key=f"action_{idx}", use_container_width=True):
                    st.success(f"Demo action selected: {label}")

    st.info(
        "In the production Next.js version, each action will open a focused workflow and create an auditable event in the sample timeline."
    )
