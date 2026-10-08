"""Booking preparation, collection sheet and controlled checkout UI."""

import streamlit as st

from repositories.sample_repository import (
    checkout_booking,
    get_booking_preparation,
    mark_booking_item_cannot_supply,
    mark_booking_item_prepared,
    report_booking_item_missing,
    start_booking_preparation,
    submit_booking_preparation,
    undo_booking_item_prepared,
)
from services.email_service import send_missing_preparation_notification
from utils.booking_collection_pdf import generate_collection_sheet


def _location_text(item):
    code = item.get("location_code")
    name = item.get("location_name")
    if code and name:
        return f"{code} — {name}"
    return code or name or "No recorded location"


def render_booking_preparation_page(hero):
    booking_group_id = st.session_state.get("selected_preparation_booking_group_id")
    if not booking_group_id:
        st.error("No booking has been selected for preparation.")
        if st.button("Back to Bookings"):
            st.session_state.pop("workflow_page", None)
            st.rerun()
        return

    try:
        data = get_booking_preparation(booking_group_id)
    except Exception as exc:
        st.error(f"Could not load booking preparation: {exc}")
        return
    if not data:
        st.error("The selected booking could not be found.")
        return

    booking = data["booking"]
    items = data["items"]
    status = booking["booking_status"]
    hero(
        f"Prepare {booking['booking_number']}",
        "Locate booked samples, prepare available items and manage collection.",
    )

    notification = st.session_state.pop("preparation_notification", None)
    if notification:
        if notification.get("sent"):
            st.success("Admin was notified about the missing sample.")
        else:
            st.warning("Preparation saved, but the admin notification was not sent.")

    checkout_success = st.session_state.pop("checkout_success", None)
    if checkout_success:
        st.success(checkout_success)

    if st.button("← Back to Bookings", key="back_from_preparation"):
        st.session_state.pop("selected_preparation_booking_group_id", None)
        st.session_state.pop("workflow_page", None)
        st.rerun()

    col1, col2, col3 = st.columns(3)
    col1.metric("Requester", booking["booked_by"])
    col2.metric("Start Date", booking["start_date"].strftime("%d %b %Y"))
    col3.metric("End Date", booking["end_date"].strftime("%d %b %Y"))
    st.markdown(f"**Status:** {status}")
    st.divider()

    if status == "Reserved":
        st.info("Start preparation when you are ready to physically locate these samples.")
        if st.button("Start Preparing", type="primary", key="start_booking_preparation"):
            try:
                start_booking_preparation(booking_group_id)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        return

    prepared_count = sum(item["preparation_status"] == "Prepared" for item in items)
    replacement_count = sum(item["preparation_status"] == "Replaced" for item in items)
    missing_count = sum(item["preparation_status"] == "Missing" for item in items)
    outstanding_count = sum(item["preparation_status"] == "Not Prepared" for item in items)
    cannot_supply_count = sum(item["preparation_status"] == "Cannot Supply" for item in items)
    supplied_count = prepared_count + replacement_count
    not_supplied_count = missing_count + cannot_supply_count

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Prepared", supplied_count)
    metric2.metric("Missing", missing_count)
    metric3.metric("Still to Check", outstanding_count)
    st.divider()
    st.markdown("### Samples")

    for item in items:
        item_status = item["preparation_status"]
        item_id = item["booking_id"]
        with st.container(border=True):
            top_left, top_right = st.columns([4, 1])
            with top_left:
                st.markdown(f"**{item['sample_id']} — {item['sample_name']}**")
                st.caption(f"Current location: {_location_text(item)}")
            with top_right:
                st.markdown(f"**{item_status}**")

            if item_status == "Not Prepared" and status == "Preparing":
                sample_available = (
                    item["asset_state"] == "Active"
                    and item["condition"] == "Good"
                )
                if not sample_available:
                    st.error("This sample is not available for preparation.")
                    a, b = st.columns(2)
                    a.caption("Asset State")
                    a.write(item["asset_state"])
                    b.caption("Condition")
                    b.write(item["condition"])
                    st.warning(
                        "The sample was available when booked, but its condition "
                        "or lifecycle state has since changed."
                    )
                    if st.button("Cannot Supply", key=f"cannot_supply_{item_id}"):
                        st.session_state["cannot_supply_booking_id"] = item_id
                        st.rerun()
                    if st.session_state.get("cannot_supply_booking_id") == item_id:
                        with st.form(f"cannot_supply_form_{item_id}"):
                            reason = st.text_area(
                                "Reason *",
                                value=f"Sample is {item['asset_state']} / {item['condition']}.",
                            )
                            confirm = st.form_submit_button("Confirm Cannot Supply", type="primary")
                        if confirm:
                            if not reason.strip():
                                st.error("Please enter a reason.")
                            else:
                                try:
                                    mark_booking_item_cannot_supply(item_id, reason.strip())
                                    st.session_state.pop("cannot_supply_booking_id", None)
                                    st.rerun()
                                except Exception as exc:
                                    st.error(str(exc))
                else:
                    action_col1, action_col2 = st.columns(2)
                    with action_col1:
                        if st.button(
                            "Mark Prepared", type="primary", width="stretch",
                            key=f"prepare_item_{item_id}",
                        ):
                            try:
                                mark_booking_item_prepared(item_id)
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))
                    with action_col2:
                        if st.button(
                            "Report Missing", width="stretch",
                            key=f"report_missing_{item_id}",
                        ):
                            st.session_state["missing_booking_item_id"] = item_id
                            st.rerun()
                    if st.session_state.get("missing_booking_item_id") == item_id:
                        with st.form(f"missing_item_form_{item_id}"):
                            st.warning("Report this sample as missing from its expected location.")
                            missing_note = st.text_area(
                                "Missing note *",
                                placeholder="Example: Could not locate sample on the S1 shelf.",
                            )
                            confirm_missing = st.form_submit_button(
                                "Confirm Missing", type="primary"
                            )
                        if confirm_missing:
                            if not missing_note.strip():
                                st.error("Please enter a missing note.")
                            else:
                                try:
                                    report_booking_item_missing(item_id, missing_note.strip())
                                    st.session_state.pop("missing_booking_item_id", None)
                                    st.rerun()
                                except Exception as exc:
                                    st.error(str(exc))

            elif item_status == "Prepared":
                st.success("Prepared and moved to C1 — Collection / Dispatch Area.")
                if status == "Preparing":
                    if st.button("Undo Prepared", key=f"undo_prepared_{item_id}"):
                        try:
                            undo_booking_item_prepared(item_id)
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
            elif item_status == "Missing":
                st.warning("Not supplied — sample reported missing.")
                if item.get("missing_note"):
                    st.caption(f"Note: {item['missing_note']}")
            elif item_status == "Replaced":
                st.info("A replacement sample will be supplied.")
                if item.get("replacement_sample_id"):
                    st.write(
                        f"{item['replacement_sample_id']} — "
                        f"{item.get('replacement_sample_name') or ''}"
                    )
            elif item_status == "Cannot Supply":
                st.warning("Not supplied — sample unavailable.")
                st.caption(f"Reason: {item.get('missing_note') or 'Unavailable'}")

    # IMPORTANT: Each booking status is handled at the same indentation level.
    if status == "Preparing":
        st.divider()
        if outstanding_count:
            st.info(f"{outstanding_count} sample(s) still need to be processed.")
        else:
            if supplied_count == 0:
                st.info("0 items supplied. Finishing preparation will close this booking.")
            else:
                st.success(f"{supplied_count} item(s) prepared for collection.")
            if st.button(
                "Finish Preparation", type="primary", width="stretch",
                key="submit_booking_preparation",
            ):
                try:
                    result = submit_booking_preparation(booking_group_id)
                    st.session_state["preparation_result"] = result
                    if result["has_missing_items"]:
                        try:
                            notification = send_missing_preparation_notification(
                                booking_number=result["booking_number"],
                                booked_by=result["booked_by"],
                                missing_items=result["missing_items"],
                            )
                            st.session_state["preparation_notification"] = notification
                        except Exception as exc:
                            st.session_state["preparation_notification"] = {
                                "sent": False, "reason": str(exc)
                            }
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    if status == "Ready for Collection":
        st.divider()
        st.success("Preparation complete. Booking ready for collection.")
        st.write(f"**Supplied:** {supplied_count} of {len(items)} samples")
        if not_supplied_count:
            st.caption(f"Not supplied: {not_supplied_count} sample(s)")
        if supplied_count:
            st.caption("Prepared samples are located at C1 — Collection / Dispatch Area.")

        has_replacement = replacement_count > 0
        can_checkout = prepared_count > 0 and not has_replacement and outstanding_count == 0

        st.divider()
        st.markdown("### Collection Sheet")
        st.caption(
            "Download and print the Collection Sheet. "
            "The requester should verify and sign it when collecting samples."
        )
        if has_replacement:
            st.error("Replacement checkout is not yet implemented. Checkout is blocked.")
        elif prepared_count == 0:
            st.warning(
                "No samples are prepared for collection. This booking cannot be "
                "checked out. Please review its booking status with an administrator."
            )
        else:
            try:
                pdf_bytes = generate_collection_sheet(booking, items)
                st.download_button(
                    "Download Collection Sheet (PDF)",
                    data=pdf_bytes,
                    file_name=f"{booking['booking_number']}_collection_sheet.pdf",
                    mime="application/pdf",
                    width="stretch",
                    key=f"collection_pdf_{booking_group_id}",
                )
            except Exception as exc:
                st.error(f"Could not generate Collection Sheet: {exc}")

        st.divider()
        st.markdown("### Confirm Check Out")
        st.write(f"**Collected by:** {booking['booked_by']}")
        st.write(f"**Samples to issue:** {prepared_count}")
        st.caption("Confirm checkout only after the requester has verified the supplied samples.")
        confirm_checkout = st.checkbox(
            "I confirm the requester has collected the supplied samples.",
            key=f"confirm_checkout_{booking_group_id}",
            disabled=not can_checkout,
        )
        if st.button(
            "Confirm Check Out", type="primary", width="stretch",
            disabled=not can_checkout or not confirm_checkout,
            key=f"checkout_booking_{booking_group_id}",
        ):
            try:
                result = checkout_booking(booking_group_id)
                st.session_state["checkout_success"] = (
                    f"{result['booking_number']} checked out successfully. "
                    f"{result['checked_out_count']} sample(s) issued to {result['booked_by']}."
                )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if status == "Checked Out":
        st.success(f"This booking has been checked out to {booking['booked_by']}.")
        st.info("The supplied samples are assigned to the requester and are awaiting return.")

    if status == "Closed - Not Supplied":
        st.warning("This booking was closed because no samples could be supplied.")
