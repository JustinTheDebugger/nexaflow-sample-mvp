import pandas as pd
import streamlit as st

from repositories.sample_repository import (
    get_active_products,
    get_categories,
    get_sample_by_record_id,
    get_sample_events,
    get_sample_products,
    get_sample_types,
    link_sample_product,
    unlink_sample_product,
    update_sample_details,
)

from utils.qr import build_sample_qr
from utils.tag import build_warehouse_tag


def render_sample_detail(hero):

    if st.session_state.pop(
        "close_sample_edit",
        False,
    ):
        st.session_state[
            "sample_detail_edit_mode"
        ] = False

    sample_record_id = st.session_state.get(
        "selected_sample_record_id"
    )

    if not sample_record_id:
        hero(
            "Sample Detail",
            "Select a sample from Sample Listing to view its operational record.",
        )

        st.info(
            "No sample has been selected."
        )

        if st.button(
            "Back to Sample Listing",
            type="primary",
        ):
            st.session_state["next_page"] = (
                "Sample Search"
            )
            st.rerun()

        return

    try:
        sample = get_sample_by_record_id(
            sample_record_id
        )

        events = get_sample_events(
            sample_record_id
        )

    except Exception as exc:
        st.error(
            f"Could not load sample: {exc}"
        )
        return

    if not sample:
        st.error(
            "The selected sample could not be found."
        )
        return

    location_code = (
        sample["current_location_code"]
        or ""
    )

    location_name = (
        sample["current_location_name"]
        or "No Location"
    )

    display_name = sample["sample_name"]

    if location_code:
        display_name += (
            f" ({location_code})"
        )

    hero(
        display_name,
        (
            f"{sample['sample_id']} · "
            "Physical Sample Asset"
        ),
    )

    # ---------------------------------------------------------
    # Top actions
    # ---------------------------------------------------------

    action_col1, action_col2, action_col3, spacer = (
        st.columns([1, 1, 1, 3])
    )

    with action_col1:
        if st.button(
            "← Back",
            use_container_width=True,
        ):
            st.session_state["next_page"] = (
                "Sample Search"
            )
            st.rerun()

    qr_bytes, _ = build_sample_qr(
        sample["sample_id"]
    )

    warehouse_tag = build_warehouse_tag(
        sample_id=sample["sample_id"],
        sample_name=sample["sample_name"],
        location_name=location_name,
        qr_bytes=qr_bytes,
    )

    with action_col2:
        st.download_button(
            "Warehouse Tag",
            data=warehouse_tag,
            file_name=(
                f"{sample['sample_id']}"
                f"_tag.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
        )

    with action_col3:
        edit_mode = st.toggle(
            "Edit Details",
            key="sample_detail_edit_mode",
        )


    # ---------------------------------------------------------
    # Edit sample details
    # ---------------------------------------------------------

    if edit_mode:
        st.markdown("### Edit Sample Details")

        try:
            sample_types = get_sample_types()
            categories = get_categories()

        except Exception as exc:
            st.error(
                f"Could not load edit options: {exc}"
            )

        else:
            sample_type_options = {
                f"{item['code']} · {item['name']}": item
                for item in sample_types
            }

            category_options = {
                (
                    f"{item['category_code']} · "
                    f"{item['category_name']}"
                ): item
                for item in categories
            }

            # ---------------------------------------------
            # Find the existing option
            # ---------------------------------------------

            current_type_label = next(
                (
                    label
                    for label, item
                    in sample_type_options.items()
                    if item["id"]
                    == sample["sample_type_id"]
                ),
                None,
            )

            current_category_label = next(
                (
                    label
                    for label, item
                    in category_options.items()
                    if item["category_code"]
                    == sample["category_code"]
                ),
                None,
            )

            type_labels = list(
                sample_type_options.keys()
            )

            category_labels = list(
                category_options.keys()
            )

            type_index = (
                type_labels.index(
                    current_type_label
                )
                if current_type_label
                in type_labels
                else 0
            )

            category_index = (
                category_labels.index(
                    current_category_label
                )
                if current_category_label
                in category_labels
                else 0
            )

            with st.form(
                "edit_sample_details_form"
            ):
                edit_col1, edit_col2 = (
                    st.columns(2)
                )

                with edit_col1:
                    edited_sample_name = (
                        st.text_input(
                            "Sample Name *",
                            value=sample[
                                "sample_name"
                            ],
                        )
                    )

                    edited_type_label = (
                        st.selectbox(
                            "Sample Type *",
                            options=type_labels,
                            index=type_index,
                        )
                    )

                    edited_category_label = (
                        st.selectbox(
                            "Category *",
                            options=category_labels,
                            index=category_index,
                        )
                    )

                with edit_col2:
                    source_options = [
                        "Supplier",
                        "Customer Return",
                        "Internal Transfer",
                        "Other",
                    ]

                    current_source = (
                        sample["source"]
                        or "Supplier"
                    )

                    if (
                        current_source
                        not in source_options
                    ):
                        source_options.append(
                            current_source
                        )

                    source_index = (
                        source_options.index(
                            current_source
                        )
                    )

                    edited_source = (
                        st.selectbox(
                            "Source",
                            options=source_options,
                            index=source_index,
                        )
                    )

                    edited_notes = (
                        st.text_area(
                            "Notes",
                            value=(
                                sample["notes"]
                                or ""
                            ),
                            height=150,
                        )
                    )

                save_changes = (
                    st.form_submit_button(
                        "Save Changes",
                        type="primary",
                        use_container_width=True,
                    )
                )

            if save_changes:
                if not edited_sample_name.strip():
                    st.error(
                        "Sample Name is required."
                    )

                else:
                    selected_type = (
                        sample_type_options[
                            edited_type_label
                        ]
                    )

                    selected_category = (
                        category_options[
                            edited_category_label
                        ]
                    )

                    try:
                        update_sample_details(
                            sample_record_id=(
                                sample_record_id
                            ),
                            sample_name=(
                                edited_sample_name
                                .strip()
                            ),
                            sample_type_id=(
                                selected_type["id"]
                            ),
                            category_code=(
                                selected_category[
                                    "category_code"
                                ]
                            ),
                            source=edited_source,
                            notes=(
                                edited_notes.strip()
                            ),
                        )

                    except Exception as exc:
                        st.error(
                            f"Could not update "
                            f"sample: {exc}"
                        )

                    else:
                        st.success(
                            "Sample details updated."
                        )

                        st.session_state[
                            "close_sample_edit"
                        ] = True

                        st.rerun()

        st.markdown("---")


    # ---------------------------------------------------------
    # Operational summary
    # ---------------------------------------------------------

    st.markdown("### Operational Summary")

    row1 = st.columns(4)

    with row1[0]:
        st.caption("Sample ID")
        st.write(
            sample["sample_id"]
        )

    with row1[1]:
        st.caption("Sample Type")
        st.write(
            sample["sample_type_name"]
        )

    with row1[2]:
        st.caption("Asset State")
        st.write(
            sample["asset_state"]
        )

    with row1[3]:
        st.caption("Condition")
        st.write(
            sample["condition"]
        )

    row2 = st.columns(4)

    with row2[0]:
        st.caption("Current Location")
        st.write(
            location_name
        )

    with row2[1]:
        st.caption("Current Holder")

        holder = (
            sample["current_holder"]
            or "Storage"
        )

        st.write(holder)

    with row2[2]:
        st.caption("Category")

        if sample["category_name"]:
            st.write(
                sample["category_name"]
            )
        else:
            st.write("—")

    with row2[3]:
        st.caption("Source")
        st.write(
            sample["source"]
            or "—"
        )

    # ---------------------------------------------------------
    # Booking rules
    # ---------------------------------------------------------

    st.markdown("### Booking")

    booking_cols = st.columns(3)

    with booking_cols[0]:
        st.caption("Bookable")

        st.write(
            "Yes"
            if sample["is_bookable"]
            else "No"
        )

    with booking_cols[1]:
        st.caption("Approval")

        st.write(
            "Required"
            if sample["requires_approval"]
            else "Not Required"
        )

    with booking_cols[2]:
        st.caption("Current Availability")

        st.write(
            "Booking engine not connected yet"
        )

    # ---------------------------------------------------------
    # Record details
    # ---------------------------------------------------------

    tabs = st.tabs(
        [
            "Timeline",
            "Details",
            "Related Products",
            "Media",
        ]
    )

    # ---------------------------------------------------------
    # Timeline
    # ---------------------------------------------------------

    with tabs[0]:
        if not events:
            st.info(
                "No lifecycle events have been recorded."
            )

        else:
            for event in events:
                event_date = event[
                    "event_date"
                ]

                st.markdown(
                    f"**{event['title']}**"
                )

                st.caption(
                    event_date.strftime(
                        "%d %b %Y · %H:%M"
                    )
                )

                if event["details"]:
                    st.write(
                        event["details"]
                    )

                movement_parts = []

                if event[
                    "previous_location_name"
                ]:
                    movement_parts.append(
                        "From: "
                        + event[
                            "previous_location_name"
                        ]
                    )

                if event[
                    "new_location_name"
                ]:
                    movement_parts.append(
                        "To: "
                        + event[
                            "new_location_name"
                        ]
                    )

                if movement_parts:
                    st.caption(
                        " · ".join(
                            movement_parts
                        )
                    )

                st.markdown("---")

    # ---------------------------------------------------------
    # Details
    # ---------------------------------------------------------

    with tabs[1]:
        details = pd.DataFrame(
            {
                "Field": [
                    "Sample ID",
                    "Sample Name",
                    "Sample Type",
                    "Category",
                    "Origin Location",
                    "Current Location",
                    "Source",
                    "Received Date",
                    "Asset State",
                    "Condition",
                    "Current Holder",
                    "Current Holder Team",
                    "Usage Count",
                    "Last Inspection",
                    "Notes",
                ],
                "Value": [
                    sample["sample_id"],
                    sample["sample_name"],
                    sample["sample_type_name"],
                    (
                        sample["category_name"]
                        or "—"
                    ),
                    (
                        sample[
                            "origin_location_name"
                        ]
                        or "—"
                    ),
                    location_name,
                    sample["source"] or "—",
                    (
                        sample["received_date"]
                        .strftime("%d %b %Y")
                        if sample[
                            "received_date"
                        ]
                        else "—"
                    ),
                    sample["asset_state"],
                    sample["condition"],
                    (
                        sample[
                            "current_holder"
                        ]
                        or "—"
                    ),
                    (
                        sample[
                            "current_holder_team"
                        ]
                        or "—"
                    ),
                    sample["usage_count"],
                    (
                        sample[
                            "last_inspection_date"
                        ].strftime(
                            "%d %b %Y"
                        )
                        if sample[
                            "last_inspection_date"
                        ]
                        else "—"
                    ),
                    sample["notes"] or "—",
                ],
            }
        )

        st.dataframe(
            details,
            use_container_width=True,
            hide_index=True,
        )

    # ---------------------------------------------------------
    # Related products
    # ---------------------------------------------------------

    with tabs[2]:
        st.markdown("### Related Products")

        try:
            related_products = get_sample_products(
                sample_record_id
            )

        except Exception as exc:
            st.error(
                f"Could not load related products: {exc}"
            )
            related_products = []

        if related_products:
            for product in related_products:
                with st.container(border=True):
                    product_col, type_col, action_col = (
                        st.columns([2.5, 1.3, 1])
                    )

                    with product_col:
                        st.markdown(
                            f"**{product['product_code']}**"
                        )

                    with type_col:
                        st.caption("Relationship")
                        st.write(
                            product["relationship_type"]
                        )

                    with action_col:
                        if st.button(
                            "Unlink",
                            key=(
                                f"unlink_product_"
                                f"{product['id']}"
                            ),
                            use_container_width=True,
                        ):
                            try:
                                unlink_sample_product(
                                    sample_record_id=(
                                        sample_record_id
                                    ),
                                    product_code=(
                                        product[
                                            "product_code"
                                        ]
                                    ),
                                )

                            except Exception as exc:
                                st.error(
                                    f"Could not unlink "
                                    f"product: {exc}"
                                )

                            else:
                                st.rerun()

        else:
            st.info(
                "No products are linked to this sample yet."
            )

        
        try:
            related_products = get_sample_products(
                sample_record_id
            )

            if (
                product_scope
                == "Same Category"
                and sample["category_code"]
            ):
                active_products = (
                    get_active_products(
                        category_code=(
                            sample["category_code"]
                        )
                    )
                )

            else:
                active_products = (
                    get_active_products()
                )

        except Exception as exc:
            st.error(
                f"Could not load product "
                f"relationships: {exc}"
            )

            related_products = []
            active_products = []


        st.markdown("#### Link Product")

        with st.form(
            "link_product_form",
            clear_on_submit=True,
        ):
            product_code = st.text_input(
                "Product Code *",
                placeholder="e.g. 0247304-001",
            )

            relationship_type = st.selectbox(
                "Relationship",
                [
                    "Primary",
                    "Compatible",
                    "Accessory",
                    "Reference",
                ],
            )

            link_product_submit = (
                st.form_submit_button(
                    "Link Product",
                    type="primary",
                    use_container_width=True,
                )
            )

        if link_product_submit:
            if not product_code.strip():
                st.error(
                    "Product Code is required."
                )

            else:
                try:
                    link_sample_product(
                        sample_record_id=(
                            sample_record_id
                        ),
                        product_code=(
                            product_code.strip()
                        ),
                        relationship_type=(
                            relationship_type
                        ),
                    )

                except Exception as exc:
                    st.error(
                        f"Could not link product: {exc}"
                    )

                else:
                    st.success(
                        "Product linked successfully."
                    )
                    st.rerun()

    # ---------------------------------------------------------
    # Media
    # ---------------------------------------------------------

    with tabs[3]:
        st.info(
            "Sample and condition photos will be added "
            "when Supabase Storage is connected."
        )