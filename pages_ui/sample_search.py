import pandas as pd
import streamlit as st

from repositories.sample_repository import get_samples
from utils.qr import build_sample_qr
from utils.tag import (
    build_warehouse_tag,
    build_warehouse_tag_bundle,
)


def render_sample_search(hero):
    hero(
        "Sample Listing",
        (
            "Find physical samples, review their current "
            "location, condition, type and operational state."
        ),
    )

    # ---------------------------------------------------------
    # Load samples from NeonDB
    # ---------------------------------------------------------

    try:
        samples = get_samples()

    except Exception as exc:
        st.error(
            f"Could not load samples: {exc}"
        )
        return

    if not samples:
        st.info(
            "No samples have been created yet."
        )
        return

    df = pd.DataFrame(samples)

    # ---------------------------------------------------------
    # Search and filters
    # ---------------------------------------------------------

    search_col, type_col, location_col = st.columns(
        [2, 1, 1]
    )

    with search_col:
        query = st.text_input(
            "Search Samples",
            placeholder=(
                "Search sample name, ID, category..."
            ),
            key="sample_search_query",
        )

    with type_col:
        type_options = sorted(
            df["sample_type_name"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_type = st.selectbox(
            "Sample Type",
            [
                "All Sample Types",
                *type_options,
            ],
            key="sample_search_type",
        )

    with location_col:
        location_options = sorted(
            df["current_location_name"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_location = st.selectbox(
            "Location",
            [
                "All Locations",
                *location_options,
            ],
            key="sample_search_location",
        )

    # ---------------------------------------------------------
    # Apply filters
    # ---------------------------------------------------------

    filtered = df.copy()

    if query.strip():
        search_text = (
            filtered[
                [
                    "sample_id",
                    "sample_name",
                    "category_code",
                    "category_name",
                    "sample_type_name",
                    "current_location_code",
                    "current_location_name",
                ]
            ]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
            .str.lower()
        )

        filtered = filtered[
            search_text.str.contains(
                query.strip().lower(),
                regex=False,
            )
        ]

    if selected_type != "All Sample Types":
        filtered = filtered[
            filtered["sample_type_name"]
            == selected_type
        ]

    if selected_location != "All Locations":
        filtered = filtered[
            filtered["current_location_name"]
            == selected_location
        ]

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    st.caption(
        f"{len(filtered)} of "
        f"{len(df)} sample(s)"
    )

    # Stop here if no matching samples.
    if filtered.empty:
        st.info(
            "No samples match the current search."
        )
        return

    st.markdown("---")

    # ---------------------------------------------------------
    # Bulk warehouse-tag printing
    # ---------------------------------------------------------

    st.markdown("### Print Warehouse Tags")

    selection_mode = st.radio(
        "Print",
        [
            "Select Samples",
            "All Filtered Samples",
        ],
        horizontal=True,
        key="tag_print_mode",
    )

    selection_options = {
        (
            f"{row['sample_id']} · "
            f"{row['sample_name']} "
            f"({row['current_location_code']})"
        ): row["sample_id"]
        for _, row in filtered.iterrows()
    }

    if selection_mode == "All Filtered Samples":
        selected_sample_ids = (
            filtered["sample_id"]
            .tolist()
        )

        st.caption(
            f"{len(selected_sample_ids)} "
            f"filtered sample(s) will be printed."
        )

    else:
        selected_labels = st.multiselect(
            "Select samples to print",
            options=list(
                selection_options.keys()
            ),
            placeholder=(
                "Select one or more samples..."
            ),
            key="bulk_tag_selection",
        )

        selected_sample_ids = [
            selection_options[label]
            for label in selected_labels
        ]

    # ---------------------------------------------------------
    # Build bulk PDF
    # ---------------------------------------------------------

    if selected_sample_ids:
        selected_rows = filtered[
            filtered["sample_id"].isin(
                selected_sample_ids
            )
        ]

        bulk_samples = []

        for _, sample in selected_rows.iterrows():

            qr_bytes, _ = build_sample_qr(
                sample["sample_id"]
            )

            location_name = (
                sample["current_location_name"]
                if pd.notna(
                    sample["current_location_name"]
                )
                else "No Location"
            )

            bulk_samples.append(
                {
                    "sample_id": sample[
                        "sample_id"
                    ],
                    "sample_name": sample[
                        "sample_name"
                    ],
                    "location_name": location_name,
                    "qr_bytes": qr_bytes,
                }
            )

        bulk_pdf = build_warehouse_tag_bundle(
            bulk_samples
        )

        st.download_button(
            (
                f"Download "
                f"{len(bulk_samples)} "
                f"Warehouse Tag"
                f"{'s' if len(bulk_samples) != 1 else ''}"
            ),
            data=bulk_pdf,
            file_name="zempire_sample_tags.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            key="download_bulk_tags",
        )

    st.markdown("---")

    # ---------------------------------------------------------
    # Sample listing
    # ---------------------------------------------------------

    for _, sample in filtered.iterrows():

        location_code = (
            sample["current_location_code"]
            if pd.notna(
                sample["current_location_code"]
            )
            else ""
        )

        location_name = (
            sample["current_location_name"]
            if pd.notna(
                sample["current_location_name"]
            )
            else "No Location"
        )

        # Sample name already excludes location.
        # Add current location code once for display.
        display_name = sample["sample_name"]

        if location_code:
            display_name += (
                f" ({location_code})"
            )

        # -----------------------------------------------------
        # Generate individual printable assets
        # -----------------------------------------------------

        qr_bytes, _ = build_sample_qr(
            sample["sample_id"]
        )

        warehouse_tag = build_warehouse_tag(
            sample_id=sample["sample_id"],
            sample_name=sample["sample_name"],
            location_name=location_name,
            qr_bytes=qr_bytes,
        )

        # -----------------------------------------------------
        # Sample card
        # -----------------------------------------------------

        with st.container(border=True):

            col1, col2, col3, col4, col5 = (
                st.columns(
                    [2.5, 1.2, 1.4, 1.2, 1.3]
                )
            )

            # -------------------------------------------------
            # Identity
            # -------------------------------------------------

            with col1:
                st.markdown(
                    f"### {display_name}"
                )

                st.caption(
                    sample["sample_id"]
                )

                if pd.notna(
                    sample["category_name"]
                ):
                    st.write(
                        sample["category_name"]
                    )

            # -------------------------------------------------
            # Sample type
            # -------------------------------------------------

            with col2:
                st.caption("Sample Type")

                st.write(
                    sample["sample_type_name"]
                )

                if not sample["is_bookable"]:
                    st.caption(
                        "Not bookable"
                    )

                elif sample[
                    "requires_approval"
                ]:
                    st.caption(
                        "Approval required"
                    )

                else:
                    st.caption(
                        "Bookable"
                    )

            # -------------------------------------------------
            # Current location / holder
            # -------------------------------------------------

            with col3:
                st.caption("Current Location")

                st.write(
                    location_name
                )

                if (
                    pd.notna(
                        sample["current_holder"]
                    )
                    and sample[
                        "current_holder"
                    ]
                ):
                    st.caption("Holder")

                    st.write(
                        sample[
                            "current_holder"
                        ]
                    )

            # -------------------------------------------------
            # Asset state / condition
            # -------------------------------------------------

            with col4:
                st.caption("Asset State")

                st.write(
                    sample["asset_state"]
                )

                st.caption("Condition")

                st.write(
                    sample["condition"]
                )

            # -------------------------------------------------
            # Actions Section
            # -------------------------------------------------

            with col5:
                st.caption("Actions")

                if st.button(
                    "View Sample",
                    use_container_width=True,
                    type="primary",
                    key=f"view_{sample['id']}",
                ):
                    st.session_state[
                        "selected_sample_record_id"
                    ] = str(sample["id"])

                    st.session_state[
                        "next_page"
                    ] = "Sample Detail"

                    st.rerun()

                st.download_button(
                    "QR Code",
                    data=qr_bytes,
                    file_name=(
                        f"{sample['sample_id']}"
                        f"_qr.png"
                    ),
                    mime="image/png",
                    use_container_width=True,
                    type="primary",
                    key=(
                        f"qr_{sample['id']}"
                    ),
                )

                st.download_button(
                    "Warehouse Tag",
                    data=warehouse_tag,
                    file_name=(
                        f"{sample['sample_id']}"
                        f"_tag.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True,
                    type="secondary",
                    key=(
                        f"tag_{sample['id']}"
                    ),
                )