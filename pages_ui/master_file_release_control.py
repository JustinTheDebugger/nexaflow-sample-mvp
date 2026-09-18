import streamlit as st


def render_master_file_release_control_page():
    """Render the static Master File Release Control concept page."""

    # ------------------------------------------------------------------
    # Page header
    # ------------------------------------------------------------------
    st.title("Master Files")
    st.caption(
        "Release Control · See what master files need work, approval, "
        "or release to factory."
    )

    # ------------------------------------------------------------------
    # Static demo data
    # ------------------------------------------------------------------
    summary = {
        "Master Required": 12,
        "In Progress": 7,
        "Ready to Release": 8,
        "Factory Current": 126,
    }

    records = [
        {
            "product_name": "Evo TS V2",
            "product_code": "0207004-004",
            "file_type": "Swing Tag",
            "revision": "Rev 03",
            "master_status": "Approved",
            "factory": "Friend",
            "factory_revision": "Rev 02",
            "last_release": "PO1615 · 17 Jul 2026",
            "action": "Release Next PO",
            "action_type": "release",
        },
        {
            "product_name": "Aerospeed 4",
            "product_code": "0247304-001",
            "file_type": "Instruction Manual",
            "revision": "—",
            "master_status": "Not Started",
            "factory": "Friend",
            "factory_revision": "None",
            "last_release": "Never released",
            "action": "Master Required",
            "action_type": "required",
        },
        {
            "product_name": "Megadome",
            "product_code": "0206601-001",
            "file_type": "Carton Artwork",
            "revision": "Rev 02",
            "master_status": "Awaiting Approval",
            "factory": "Friend",
            "factory_revision": "Rev 01",
            "last_release": "PO1588 · 21 May 2026",
            "action": "Awaiting Approval",
            "action_type": "approval",
        },
        {
            "product_name": "Aerospeed 6",
            "product_code": "0247306-001",
            "file_type": "Shipping Sticker",
            "revision": "Rev 04",
            "master_status": "Approved",
            "factory": "Friend",
            "factory_revision": "Rev 04",
            "last_release": "PO1634 · 28 Aug 2026",
            "action": "Factory Current",
            "action_type": "current",
        },
    ]

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    st.markdown(
        """
        <style>
        .mf-summary-card {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 16px 18px;
            background: white;
            min-height: 95px;
        }

        .mf-summary-number {
            font-size: 26px;
            font-weight: 700;
            color: #111827;
            line-height: 1.1;
        }

        .mf-summary-label {
            margin-top: 7px;
            font-size: 13px;
            color: #6b7280;
        }

        .mf-card {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 18px 20px;
            margin-bottom: 14px;
            background: white;
        }

        .mf-product-name {
            font-size: 18px;
            font-weight: 700;
            color: #111827;
        }

        .mf-product-code {
            font-size: 12px;
            color: #6b7280;
            margin-top: 2px;
        }

        .mf-file-type {
            font-size: 14px;
            font-weight: 600;
            color: #374151;
            margin-top: 12px;
            margin-bottom: 14px;
        }

        .mf-label {
            font-size: 11px;
            text-transform: uppercase;
            color: #9ca3af;
            font-weight: 600;
            letter-spacing: 0.04em;
        }

        .mf-value {
            font-size: 14px;
            color: #111827;
            font-weight: 500;
            margin-top: 2px;
        }

        .mf-badge {
            display: inline-block;
            padding: 4px 9px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 700;
        }

        .mf-release {
            background: #dbeafe;
            color: #1d4ed8;
        }

        .mf-required {
            background: #fee2e2;
            color: #b91c1c;
        }

        .mf-approval {
            background: #fef3c7;
            color: #92400e;
        }

        .mf-current {
            background: #dcfce7;
            color: #166534;
        }

        .mf-section-title {
            font-size: 15px;
            font-weight: 700;
            color: #111827;
            margin-top: 12px;
            margin-bottom: 4px;
        }

        .mf-section-caption {
            font-size: 13px;
            color: #6b7280;
            margin-bottom: 18px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # Summary cards
    # ------------------------------------------------------------------
    cols = st.columns(4)

    for col, (label, value) in zip(cols, summary.items()):
        with col:
            st.markdown(
                f"""
                <div class="mf-summary-card">
                    <div class="mf-summary-number">{value}</div>
                    <div class="mf-summary-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    filter_col, factory_col = st.columns([2, 1])

    with filter_col:
        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Master Required",
                "In Progress",
                "Awaiting Approval",
                "Ready to Release",
                "Factory Current",
            ],
        )

    with factory_col:
        st.selectbox(
            "Factory",
            ["All Factories", "Friend"],
        )

    st.divider()

    # ------------------------------------------------------------------
    # Attention section
    # ------------------------------------------------------------------
    st.markdown(
        """
        <div class="mf-section-title">Attention Required</div>
        <div class="mf-section-caption">
            Master files where an action is currently required.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Simple static filtering for demo
    filtered_records = records

    if status_filter == "Master Required":
        filtered_records = [
            r for r in records if r["action_type"] == "required"
        ]
    elif status_filter == "Awaiting Approval":
        filtered_records = [
            r for r in records if r["action_type"] == "approval"
        ]
    elif status_filter == "Ready to Release":
        filtered_records = [
            r for r in records if r["action_type"] == "release"
        ]
    elif status_filter == "Factory Current":
        filtered_records = [
            r for r in records if r["action_type"] == "current"
        ]

    # ------------------------------------------------------------------
    # Master file cards
    # ------------------------------------------------------------------
    for record in filtered_records:

        # Create bordered card
        with st.container(border=True):

            # Product name and action badge
            title_col, status_col = st.columns([4, 1])

            with title_col:
                st.markdown(f"### {record['product_name']}")
                st.caption(record["product_code"])

            with status_col:
                action_type = record["action_type"]

                if action_type == "release":
                    st.info(record["action"])
                elif action_type == "required":
                    st.error(record["action"])
                elif action_type == "approval":
                    st.warning(record["action"])
                elif action_type == "current":
                    st.success(record["action"])

            # File type
            st.markdown(f"**{record['file_type']}**")

            # Main information
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.caption("LATEST MASTER")
                st.write(record["revision"])

            with col2:
                st.caption("MASTER STATUS")
                st.write(record["master_status"])

            with col3:
                st.caption("FACTORY")
                st.write(record["factory"])

            with col4:
                st.caption("FACTORY HAS")
                st.write(record["factory_revision"])

            st.divider()

            # Release information
            release_col, action_col = st.columns([3, 1])

            with release_col:
                st.caption("LAST RELEASED")
                st.write(record["last_release"])

            with action_col:
                if record["action_type"] == "release":
                    st.button(
                        "View Release",
                        key=f"release_{record['product_code']}_{record['file_type']}",
                        use_container_width=True,
                    )