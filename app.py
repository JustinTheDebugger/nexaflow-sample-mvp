from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

from data import SAMPLES, BOOKINGS, TIMELINE, ACTIVITY
from styles import apply_styles

st.set_page_config(page_title="NexaFlow Asset Tracking", page_icon="◈", layout="wide")
apply_styles()

# Demo persistence: data survives navigation during the current Streamlit session.
if "samples" not in st.session_state:
    st.session_state.samples = [dict(x) for x in SAMPLES]
if "bookings" not in st.session_state:
    st.session_state.bookings = [dict(x) for x in BOOKINGS]
if "timeline" not in st.session_state:
    st.session_state.timeline = [dict(x) for x in TIMELINE]
if "activity" not in st.session_state:
    st.session_state.activity = [dict(x) for x in ACTIVITY]

today = date.today()

def frames():
    return (
        pd.DataFrame(st.session_state.samples),
        pd.DataFrame(st.session_state.bookings),
        pd.DataFrame(st.session_state.timeline),
    )

def hero(title, subtitle):
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )

def metric_card(label, value):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div></div>',
        unsafe_allow_html=True,
    )

def info_card(label, value):
    st.markdown(
        f'<div class="info-card"><div class="info-label">{label}</div>'
        f'<div class="info-value">{value}</div></div>',
        unsafe_allow_html=True,
    )

def next_sample_id():
    nums = []
    for s in st.session_state.samples:
        try:
            nums.append(int(s["sample_id"].split("-")[1]))
        except Exception:
            pass
    return f"SMP-{max(nums, default=0) + 1:03d}"

def sample_selector(key):
    samples, _, _ = frames()
    labels = {f"{r.product_name} · {r.sample_id}": r.sample_id for r in samples.itertuples()}
    selection = st.selectbox("Select sample", list(labels.keys()), key=key)
    return samples[samples["sample_id"] == labels[selection]].iloc[0]

def availability_text(sample):
    available = sample["next_available"]
    if pd.isna(available):
        return "Availability not yet scheduled"
    if available <= today:
        if pd.notna(sample["next_booking"]):
            days = (sample["next_booking"] - today).days
            return f"Available now · next booking in {days} day(s)"
        return "Available now · no upcoming booking"
    days = (available - today).days
    return f"Available in {days} day(s) · {available.strftime('%d %b')}"

with st.sidebar:
    st.markdown("## ◈ NexaFlow")
    st.caption("Asset Tracking & Operational Visibility")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        [
            "Executive Dashboard",
            "Sample Search",
            "Sample Detail",
            "Sample Intake",
            "QR Action Hub",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Executive Demo · Streamlit MVP")

samples, bookings, timeline = frames()

if page == "Executive Dashboard":
    hero(
        "Executive Asset Dashboard",
        "A live view of where physical samples are, who has them, and when they will be available.",
    )

    available = int((samples["next_available"] <= today).fillna(False).sum())
    checked_out = int(samples["status"].isin(["Checked Out", "In Use"]).sum())
    overdue = int((samples["status"] == "Overdue").sum())
    damaged = int((samples["condition"] == "Damaged").sum())
    upcoming = int((bookings["start"] >= today).sum()) if not bookings.empty else 0

    cols = st.columns(6)
    for col, (label, value) in zip(
        cols,
        [
            ("Total Samples", len(samples)),
            ("Available Today", available),
            ("Checked Out", checked_out),
            ("Overdue", overdue),
            ("Damaged", damaged),
            ("Upcoming Reservations", upcoming),
        ],
    ):
        with col:
            metric_card(label, value)

    st.markdown("### Operational visibility")
    left, right = st.columns([1.2, 1])

    with left:
        location_counts = (
            samples.assign(asset_location=samples["holder_team"].replace({"Operations": "Warehouse"}))
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
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=20, b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("#### Recent activity")
        for item in st.session_state.activity[:5]:
            st.markdown(
                f'<div class="info-card" style="margin-bottom:.65rem;">'
                f'<div class="info-label">{item["time"]} · {item["type"]}</div>'
                f'<div class="info-value">{item["action"]}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("### Management attention")
    attention = samples[samples["status"].isin(["Overdue", "Damaged"])]
    st.dataframe(
        attention[["sample_id", "product_name", "status", "holder", "location", "condition"]],
        use_container_width=True,
        hide_index=True,
    )

elif page == "Sample Search":
    hero(
        "Find a Sample",
        "Search by product, sample ID, category, holder, or location. Availability is calculated from operational records.",
    )

    query = st.text_input("Search", placeholder="Try: Aerospeed, Marketing, Warehouse B, SMP-001...")
    filtered = samples.copy()

    if query:
        searchable = filtered.astype(str).agg(" ".join, axis=1).str.lower()
        filtered = filtered[searchable.str.contains(query.lower(), na=False)]

    status_filter = st.multiselect("Operational state", sorted(samples["status"].unique()))
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]

    st.caption(f"{len(filtered)} sample(s) found")

    for _, sample in filtered.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2.2, 1.3, 1.5, 1])
            with c1:
                st.markdown(f"### {sample['product_name']}")
                st.caption(f"{sample['sample_id']} · {sample['product_code']}")
                st.write(availability_text(sample))
            with c2:
                st.markdown("**Current holder**")
                st.write(sample["holder"])
                st.caption(sample["holder_team"])
            with c3:
                st.markdown("**Location**")
                st.write(sample["location"])
                st.caption(f"Condition: {sample['condition']}")
            with c4:
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

    left, right = st.columns([1.15, 2])
    with left:
        st.markdown("### ◈ Physical Asset")
        st.markdown(f"## {sample['product_name']}")
        st.caption(f"{sample['sample_id']} · {sample['product_code']}")
        st.markdown(f"<span class='status'>{sample['status']}</span>", unsafe_allow_html=True)
        st.write(sample["notes"])

    with right:
        r1 = st.columns(3)
        with r1[0]:
            info_card("Current holder", f"{sample['holder']} · {sample['holder_team']}")
        with r1[1]:
            info_card("Current location", sample["location"])
        with r1[2]:
            info_card("Availability", availability_text(sample))

        st.write("")
        r2 = st.columns(3)
        with r2[0]:
            next_booking = (
                f"{sample['next_booking'].strftime('%d %b')} · {sample['next_booking_team']}"
                if pd.notna(sample["next_booking"]) else "No upcoming booking"
            )
            info_card("Next booking", next_booking)
        with r2[1]:
            info_card("Condition", sample["condition"])
        with r2[2]:
            info_card(
                "Usage / inspection",
                f"{sample['usage_count']} uses · {sample['last_inspection'].strftime('%d %b')}",
            )

    tabs = st.tabs(["Booking Calendar", "Timeline", "Asset Record"])

    with tabs[0]:
        sample_bookings = bookings[bookings["sample_id"] == sample["sample_id"]].copy()
        calendar_days = []
        for offset in range(14):
            day = today + timedelta(days=offset)
            matches = sample_bookings[
                (sample_bookings["start"] <= day) & (sample_bookings["end"] >= day)
            ]
            if matches.empty:
                calendar_days.append({"Date": day.strftime("%a %d %b"), "State": "Available", "Holder": "Warehouse"})
            else:
                b = matches.iloc[0]
                calendar_days.append({"Date": day.strftime("%a %d %b"), "State": "Booked", "Holder": b["team"]})
        st.dataframe(pd.DataFrame(calendar_days), use_container_width=True, hide_index=True)

    with tabs[1]:
        sample_timeline = timeline[timeline["sample_id"] == sample["sample_id"]].sort_values("date", ascending=False)
        for _, event in sample_timeline.iterrows():
            st.markdown(
                f'<div class="timeline-item"><div class="timeline-date">{event["date"].strftime("%d %b %Y")}</div>'
                f'<div class="timeline-title">{event["event"]}</div>'
                f'<div class="small-muted">{event["detail"]}</div></div>',
                unsafe_allow_html=True,
            )

    with tabs[2]:
        record = pd.DataFrame(
            {
                "Field": ["Sample ID", "Product code", "Category", "Source", "Received", "Condition", "Location"],
                "Value": [
                    sample["sample_id"],
                    sample["product_code"],
                    sample["category"],
                    sample.get("source", "—"),
                    sample["received_date"].strftime("%d %b %Y"),
                    sample["condition"],
                    sample["location"],
                ],
            }
        )
        st.dataframe(record, use_container_width=True, hide_index=True)

elif page == "Sample Intake":
    hero(
        "Sample Intake",
        "Create the physical asset record at the moment a sample enters the business. This becomes the first event in its lifecycle.",
    )

    st.markdown("### New sample")
    st.caption("For the MVP, the form creates a live demo record for this Streamlit session.")

    with st.form("sample_intake_form", clear_on_submit=True):
        c1, c2 = st.columns(2)

        with c1:
            product_name = st.text_input("Product name *", placeholder="e.g. Kitpac Pro X-Large")
            product_code = st.text_input("Product code *", placeholder="e.g. 0250501-001")
            category = st.selectbox(
                "Category",
                ["Tent", "Shelter", "Furniture", "Sleeping", "Accessory", "Other"],
            )
            source = st.selectbox(
                "Source",
                ["Factory", "Supplier", "Customer Return", "Internal Transfer", "Other"],
            )
            received_date = st.date_input("Received date", value=today)

        with c2:
            condition = st.selectbox(
                "Condition on receipt",
                ["Excellent", "Good", "Fair", "Damaged"],
            )
            warehouse = st.selectbox(
                "Initial warehouse",
                ["Warehouse A", "Warehouse B", "Office", "Other"],
            )
            rack = st.text_input("Rack / area", placeholder="e.g. Rack 01")
            bin_location = st.text_input("Bin / position", placeholder="e.g. Bin 04")
            purpose = st.selectbox(
                "Primary sample purpose",
                [
                    "General sample",
                    "Marketing",
                    "Sales",
                    "Trade show",
                    "Photography",
                    "Product testing",
                    "Factory review",
                ],
            )

        notes = st.text_area(
            "Notes",
            placeholder="Revision, packaging details, defects, special handling, etc.",
        )

        submitted = st.form_submit_button("Create Asset Record", use_container_width=True)

    if submitted:
        if not product_name.strip() or not product_code.strip():
            st.error("Product name and product code are required.")
        else:
            sample_id = next_sample_id()
            location_parts = [warehouse]
            if rack.strip():
                location_parts.append(rack.strip())
            if bin_location.strip():
                location_parts.append(bin_location.strip())
            location = " · ".join(location_parts)

            new_sample = {
                "sample_id": sample_id,
                "product_name": product_name.strip(),
                "product_code": product_code.strip(),
                "category": category,
                "location": location,
                "holder": "Warehouse",
                "holder_team": "Operations",
                "condition": condition,
                "usage_count": 0,
                "last_inspection": received_date,
                "photo": "",
                "next_available": received_date,
                "next_booking": None,
                "next_booking_team": None,
                "status": "Available Today" if received_date <= today else "Incoming",
                "notes": notes.strip() or f"Created as {purpose.lower()}.",
                "source": source,
                "received_date": received_date,
            }

            st.session_state.samples.append(new_sample)
            st.session_state.timeline.append(
                {
                    "sample_id": sample_id,
                    "date": received_date,
                    "event": f"Received from {source}",
                    "detail": f"Asset created in NexaFlow. Initial location: {location}. Purpose: {purpose}.",
                }
            )
            st.session_state.activity.insert(
                0,
                {
                    "time": "Just now",
                    "action": f"{product_name.strip()} added as {sample_id}",
                    "type": "Intake",
                },
            )

            st.success(f"{sample_id} created successfully.")
            st.markdown("#### Asset lifecycle started")
            st.write(f"**{product_name.strip()}** is now tracked at **{location}**.")
            st.write("The intake event has also been added to its lifecycle timeline.")

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
    cols = st.columns(3)
    actions = [
        ("Check Out", "Assign the sample to a person or team."),
        ("Return Sample", "Record the return and confirm its location."),
        ("Move Location", "Update warehouse, rack, bin, or external location."),
        ("Report Damage", "Record condition and incident details."),
        ("Add Note", "Add an operational note to the asset."),
        ("View Timeline", "Review the asset's complete lifecycle."),
    ]

    for idx, (label, desc) in enumerate(actions):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"#### {label}")
                st.caption(desc)
                if st.button(label, key=f"action_{idx}", use_container_width=True):
                    st.success(f"Demo action selected: {label}")

    st.info(
        "Next sprint: make Check Out, Return, Move Location and Report Damage create real timeline events."
    )
