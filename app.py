from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

from data import SAMPLES, BOOKINGS, TIMELINE, ACTIVITY
from styles import apply_styles

st.set_page_config(page_title="NexaFlow Asset Tracking", page_icon="◈", layout="wide")
apply_styles()

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
    return labels[selection]

def get_sample(sample_id):
    for sample in st.session_state.samples:
        if sample["sample_id"] == sample_id:
            return sample
    return None

def add_event(sample_id, event, detail):
    st.session_state.timeline.append(
        {"sample_id": sample_id, "date": today, "event": event, "detail": detail}
    )

def add_activity(action, activity_type):
    st.session_state.activity.insert(
        0, {"time": "Just now", "action": action, "type": activity_type}
    )

def availability_text(sample):
    available = sample["next_available"]
    if available is None or pd.isna(available):
        return "Availability not yet scheduled"
    if available <= today:
        next_booking = sample.get("next_booking")
        if next_booking is not None and not pd.isna(next_booking):
            days = (next_booking - today).days
            return f"Available now · next booking in {days} day(s)"
        return "Available now · no upcoming booking"
    days = (available - today).days
    return f"Available in {days} day(s) · {available.strftime('%d %b')}"

def location_from_parts(base, rack="", bin_location=""):
    parts = [base]
    if rack.strip():
        parts.append(rack.strip())
    if bin_location.strip():
        parts.append(bin_location.strip())
    return " · ".join(parts)

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
        for item in st.session_state.activity[:6]:
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

    sample_id = sample_selector("detail_selector")
    sample = get_sample(sample_id)

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
                if sample["next_booking"] else "No upcoming booking"
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
        timeline_now = pd.DataFrame(st.session_state.timeline)
        sample_timeline = timeline_now[timeline_now["sample_id"] == sample["sample_id"]].sort_values("date", ascending=False)
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

    with st.form("sample_intake_form", clear_on_submit=True):
        c1, c2 = st.columns(2)

        with c1:
            product_name = st.text_input("Product name *")
            product_code = st.text_input("Product code *")
            category = st.selectbox("Category", ["Tent", "Shelter", "Furniture", "Sleeping", "Accessory", "Other"])
            source = st.selectbox("Source", ["Factory", "Supplier", "Customer Return", "Internal Transfer", "Other"])
            received_date = st.date_input("Received date", value=today)

        with c2:
            condition = st.selectbox("Condition on receipt", ["Excellent", "Good", "Fair", "Damaged"])
            warehouse = st.selectbox("Initial warehouse", ["Warehouse A", "Warehouse B", "Office", "Other"])
            rack = st.text_input("Rack / area")
            bin_location = st.text_input("Bin / position")
            purpose = st.selectbox(
                "Primary sample purpose",
                ["General sample", "Marketing", "Sales", "Trade show", "Photography", "Product testing", "Factory review"],
            )

        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Create Asset Record", use_container_width=True)

    if submitted:
        if not product_name.strip() or not product_code.strip():
            st.error("Product name and product code are required.")
        else:
            sample_id = next_sample_id()
            location = location_from_parts(warehouse, rack, bin_location)

            st.session_state.samples.append(
                {
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
            )
            add_event(sample_id, f"Received from {source}", f"Asset created. Initial location: {location}. Purpose: {purpose}.")
            add_activity(f"{product_name.strip()} added as {sample_id}", "Intake")
            st.success(f"{sample_id} created successfully.")

elif page == "QR Action Hub":
    hero(
        "QR Action Hub",
        "Scan the sample tag and update the real operational state in seconds.",
    )

    sample_id = sample_selector("action_selector")
    sample = get_sample(sample_id)

    summary_cols = st.columns(4)
    with summary_cols[0]:
        info_card("Asset", f"{sample['product_name']} · {sample['sample_id']}")
    with summary_cols[1]:
        info_card("Current holder", f"{sample['holder']} · {sample['holder_team']}")
    with summary_cols[2]:
        info_card("Location", sample["location"])
    with summary_cols[3]:
        info_card("Condition", sample["condition"])

    st.write("")
    tabs = st.tabs(["Check Out", "Return", "Move Location", "Report Damage"])

    with tabs[0]:
        if sample["status"] in ["Checked Out", "In Use", "Overdue"]:
            st.warning(f"This sample is currently assigned to {sample['holder']}.")
        else:
            with st.form("checkout_form"):
                c1, c2 = st.columns(2)
                with c1:
                    holder = st.text_input("Checked out to *", placeholder="Person or team")
                    team = st.selectbox(
                        "Department / team",
                        ["Marketing", "Sales", "Trade Show", "Photography", "Product", "Factory", "Other"],
                    )
                    purpose = st.selectbox(
                        "Purpose",
                        ["Customer demonstration", "Trade show", "Marketing photos", "Product testing", "Factory review", "Repair", "Other"],
                    )
                with c2:
                    checkout_date = st.date_input("Checkout date", value=today)
                    expected_return = st.date_input("Expected return", value=today + timedelta(days=3))
                    external_location = st.text_input("Destination / location", placeholder="e.g. Auckland Showgrounds")

                note = st.text_area("Checkout notes")
                submit_checkout = st.form_submit_button("Confirm Check Out", use_container_width=True)

            if submit_checkout:
                if not holder.strip():
                    st.error("Please enter who is taking the sample.")
                elif expected_return < checkout_date:
                    st.error("Expected return date cannot be before checkout date.")
                else:
                    sample["holder"] = holder.strip()
                    sample["holder_team"] = team
                    sample["location"] = external_location.strip() or f"With {holder.strip()}"
                    sample["status"] = "Checked Out"
                    sample["next_available"] = expected_return + timedelta(days=1)
                    sample["usage_count"] += 1

                    detail = (
                        f"Checked out to {holder.strip()} ({team}) for {purpose}. "
                        f"Expected return: {expected_return.strftime('%d %b %Y')}."
                    )
                    if external_location.strip():
                        detail += f" Destination: {external_location.strip()}."
                    if note.strip():
                        detail += f" Note: {note.strip()}"

                    add_event(sample_id, "Checked Out", detail)
                    add_activity(f"{sample['product_name']} checked out to {holder.strip()}", "Checkout")
                    st.success("Sample checked out and timeline updated.")
                    st.rerun()

    with tabs[1]:
        if sample["status"] not in ["Checked Out", "In Use", "Overdue"]:
            st.info("This sample is not currently checked out.")
        else:
            with st.form("return_form"):
                c1, c2 = st.columns(2)
                with c1:
                    return_date = st.date_input("Return date", value=today)
                    warehouse = st.selectbox("Return location", ["Warehouse A", "Warehouse B", "Office", "Other"])
                    rack = st.text_input("Rack / area", key="return_rack")
                    bin_location = st.text_input("Bin / position", key="return_bin")
                with c2:
                    condition = st.selectbox("Condition on return", ["Excellent", "Good", "Fair", "Damaged"])
                    inspected = st.checkbox("Condition checked on return", value=True)
                    return_note = st.text_area("Return notes")

                submit_return = st.form_submit_button("Confirm Return", use_container_width=True)

            if submit_return:
                previous_holder = sample["holder"]
                location = location_from_parts(warehouse, rack, bin_location)
                sample["holder"] = "Warehouse"
                sample["holder_team"] = "Operations"
                sample["location"] = location
                sample["condition"] = condition
                sample["status"] = "Damaged" if condition == "Damaged" else "Available Today"
                sample["next_available"] = return_date
                if inspected:
                    sample["last_inspection"] = return_date

                detail = (
                    f"Returned by {previous_holder}. Location: {location}. "
                    f"Condition: {condition}."
                )
                if return_note.strip():
                    detail += f" Note: {return_note.strip()}"

                add_event(sample_id, "Returned", detail)
                add_activity(f"{sample['product_name']} returned to {location}", "Return")
                st.success("Sample returned and timeline updated.")
                st.rerun()

    with tabs[2]:
        with st.form("move_form"):
            c1, c2 = st.columns(2)
            with c1:
                destination_type = st.selectbox(
                    "Destination type",
                    ["Warehouse A", "Warehouse B", "Office", "Marketing", "Sales", "Trade Show", "Factory", "Other"],
                )
                rack = st.text_input("Rack / area", key="move_rack")
                bin_location = st.text_input("Bin / position", key="move_bin")
            with c2:
                responsible_party = st.text_input("Responsible person / team", value=sample["holder"])
                reason = st.selectbox(
                    "Reason for move",
                    ["Storage", "Internal transfer", "Trade show", "Photography", "Factory review", "Repair", "Other"],
                )
                move_note = st.text_area("Movement notes")

            submit_move = st.form_submit_button("Confirm Move", use_container_width=True)

        if submit_move:
            old_location = sample["location"]
            new_location = location_from_parts(destination_type, rack, bin_location)
            sample["location"] = new_location

            if destination_type in ["Warehouse A", "Warehouse B", "Office"]:
                sample["holder"] = "Warehouse"
                sample["holder_team"] = "Operations"
            elif responsible_party.strip():
                sample["holder"] = responsible_party.strip()
                sample["holder_team"] = destination_type

            detail = f"Moved from {old_location} to {new_location}. Reason: {reason}."
            if responsible_party.strip():
                detail += f" Responsible: {responsible_party.strip()}."
            if move_note.strip():
                detail += f" Note: {move_note.strip()}"

            add_event(sample_id, "Location Changed", detail)
            add_activity(f"{sample['product_name']} moved to {new_location}", "Movement")
            st.success("Location updated and timeline event created.")
            st.rerun()

    with tabs[3]:
        with st.form("damage_form"):
            c1, c2 = st.columns(2)
            with c1:
                severity = st.selectbox("Severity", ["Minor", "Moderate", "Major", "Unusable"])
                damage_type = st.selectbox(
                    "Damage type",
                    ["Wear and tear", "Factory defect", "Customer damage", "Transport damage", "Missing part", "Other"],
                )
                discovered_by = st.text_input("Reported by")
            with c2:
                remove_from_use = st.checkbox("Remove sample from use", value=True)
                inspection_date = st.date_input("Inspection date", value=today)
                damage_note = st.text_area("Damage description *")

            submit_damage = st.form_submit_button("Report Damage", use_container_width=True)

        if submit_damage:
            if not damage_note.strip():
                st.error("Please describe the damage.")
            else:
                sample["condition"] = "Damaged"
                sample["last_inspection"] = inspection_date
                if remove_from_use:
                    sample["status"] = "Damaged"
                    sample["next_available"] = today + timedelta(days=14)

                detail = (
                    f"{severity} {damage_type.lower()} reported. "
                    f"Description: {damage_note.strip()}."
                )
                if discovered_by.strip():
                    detail += f" Reported by {discovered_by.strip()}."
                if remove_from_use:
                    detail += " Sample removed from operational use."

                add_event(sample_id, "Damage Reported", detail)
                add_activity(f"Damage reported for {sample['product_name']}", "Damage")
                st.success("Damage recorded and timeline updated.")
                st.rerun()

    st.markdown("### Recent lifecycle events")
    timeline_now = pd.DataFrame(st.session_state.timeline)
    recent = (
        timeline_now[timeline_now["sample_id"] == sample_id]
        .sort_values("date", ascending=False)
        .head(5)
    )
    st.dataframe(recent[["date", "event", "detail"]], use_container_width=True, hide_index=True)
