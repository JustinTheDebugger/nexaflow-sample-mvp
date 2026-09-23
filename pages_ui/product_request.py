from datetime import date, timedelta

import streamlit as st

from repositories.sample_repository import (
    create_sample_request,
    get_active_products,
    get_sample_request_detail,
)

from services.email_service import (
    send_product_request_notification,
)


# ------------------------------------------------------------------
# Form reset
# ------------------------------------------------------------------

def _reset_product_request_form():
    """
    Clear Product Request form state after
    successful submission.
    """

    keys_to_clear = [
        "product_request_items",
        "product_request_from",
        "product_request_until",
        "product_request_product_picker",
        "product_request_requested_by",
        "product_request_purpose",
    ]

    # Quantity widgets are generated dynamically,
    # so remove those as well.
    quantity_keys = [
        key
        for key in st.session_state.keys()
        if key.startswith(
            "product_request_qty_"
        )
    ]

    keys_to_clear.extend(
        quantity_keys
    )

    for key in keys_to_clear:
        st.session_state.pop(
            key,
            None,
        )


# ------------------------------------------------------------------
# Product Request page
# ------------------------------------------------------------------

def render_product_request_page(hero):
    """
    Create a Product Request containing one or more products.

    Product codes are handled internally. Users select
    products by name and can request different quantities.
    """

    hero(
        "Request Product Samples",
        (
            "Request one or more products when suitable "
            "samples are not available."
        ),
    )

    # --------------------------------------------------------------
    # Previous submission result
    # --------------------------------------------------------------

    success = st.session_state.pop(
        "product_request_success",
        None,
    )

    if success:

        st.success(
            (
                f"{success['request_number']} submitted "
                "successfully."
            )
        )

        st.caption(
            (
                f"{success['item_count']} product(s) · "
                f"{success['request_status']}"
            )
        )

        if success.get(
            "email_sent"
        ):
            st.caption(
                "Admin notification sent."
            )

        else:
            st.warning(
                (
                    "The request was saved successfully, "
                    "but the admin email notification "
                    "could not be sent."
                )
            )

    # --------------------------------------------------------------
    # Session state
    # --------------------------------------------------------------

    if (
        "product_request_items"
        not in st.session_state
    ):
        st.session_state[
            "product_request_items"
        ] = []

    requested_items = st.session_state[
        "product_request_items"
    ]

    # --------------------------------------------------------------
    # Load products
    # --------------------------------------------------------------

    products = get_active_products()

    if not products:
        st.warning(
            "No active products are available."
        )
        return

    # --------------------------------------------------------------
    # Request dates
    # --------------------------------------------------------------

    st.markdown(
        "### Required Dates"
    )

    date_col1, date_col2 = st.columns(
        2
    )

    with date_col1:

        required_from = st.date_input(
            "Required From",
            value=date.today(),
            key="product_request_from",
        )

    with date_col2:

        required_until = st.date_input(
            "Required Until",
            value=(
                date.today()
                + timedelta(days=1)
            ),
            key="product_request_until",
        )

    if required_until < required_from:

        st.error(
            "Required Until cannot be before "
            "Required From."
        )

    st.divider()

    # --------------------------------------------------------------
    # Product picker
    # --------------------------------------------------------------

    st.markdown(
        "### Add Products"
    )

    st.caption(
        "Search by product name. Product codes are "
        "shown only as a reference."
    )

    product_options = {
        (
            f"{product['product_name']} "
            f"— {product['product_code']}"
        ): product
        for product in products
    }

    selected_label = st.selectbox(
        "Product",
        options=list(
            product_options.keys()
        ),
        index=None,
        placeholder=(
            "Search product by name..."
        ),
        key=(
            "product_request_product_picker"
        ),
    )

    add_col, _ = st.columns(
        [1, 3]
    )

    with add_col:

        add_product = st.button(
            "Add Product",
            width="stretch",
            type="secondary",
        )

    if add_product:

        if not selected_label:

            st.warning(
                "Select a product first."
            )

        else:

            selected_product = (
                product_options[
                    selected_label
                ]
            )

            product_code = (
                selected_product[
                    "product_code"
                ]
            )

            already_added = any(
                item["product_code"]
                == product_code
                for item
                in requested_items
            )

            if already_added:

                st.warning(
                    "This product is already "
                    "in the request."
                )

            else:

                requested_items.append(
                    {
                        "product_code": (
                            product_code
                        ),
                        "product_name": (
                            selected_product[
                                "product_name"
                            ]
                        ),
                        "quantity_required": 1,
                    }
                )

                st.session_state[
                    "product_request_items"
                ] = requested_items

                st.rerun()

    st.divider()

    # --------------------------------------------------------------
    # Requested products
    # --------------------------------------------------------------

    item_count = len(
        requested_items
    )

    st.markdown(
        (
            "### Requested Products "
            f"({item_count})"
        )
    )

    if not requested_items:

        st.info(
            "No products have been added yet."
        )

    else:

        items_to_remove = []

        for index, item in enumerate(
            requested_items
        ):

            with st.container(
                border=True
            ):

                (
                    info_col,
                    qty_col,
                    remove_col,
                ) = st.columns(
                    [5, 2, 1.5]
                )

                with info_col:

                    st.markdown(
                        (
                            f"**{item['product_name']}**"
                        )
                    )

                    st.caption(
                        item["product_code"]
                    )

                with qty_col:

                    quantity = st.number_input(
                        "Quantity",
                        min_value=1,
                        value=int(
                            item[
                                "quantity_required"
                            ]
                        ),
                        step=1,
                        key=(
                            "product_request_qty_"
                            f"{item['product_code']}"
                        ),
                    )

                    item[
                        "quantity_required"
                    ] = int(
                        quantity
                    )

                with remove_col:

                    st.write("")

                    if st.button(
                        "Remove",
                        key=(
                            "remove_product_request_"
                            f"{item['product_code']}"
                        ),
                        width="stretch",
                    ):

                        items_to_remove.append(
                            index
                        )

        if items_to_remove:

            for index in reversed(
                items_to_remove
            ):
                requested_items.pop(
                    index
                )

            st.session_state[
                "product_request_items"
            ] = requested_items

            st.rerun()

    # --------------------------------------------------------------
    # Request details
    # --------------------------------------------------------------

    st.divider()

    st.markdown(
        "### Request Details"
    )

    requested_by = st.text_input(
        "Requested By",
        placeholder="Your name",
        key=(
            "product_request_requested_by"
        ),
    )

    st.caption(
        "This field will come from the signed-in "
        "user profile when authentication is added."
    )

    purpose = st.text_area(
        "Purpose",
        placeholder=(
            "e.g. Products required for October "
            "sales presentation"
        ),
        height=100,
        key="product_request_purpose",
    )

    # --------------------------------------------------------------
    # Submit
    # --------------------------------------------------------------

    st.write("")

    submitted = st.button(
        "Submit Product Request",
        type="primary",
        width="stretch",
        disabled=(
            not requested_items
            or required_until
            < required_from
        ),
    )

    if submitted:

        # ----------------------------------------------------------
        # Validate
        # ----------------------------------------------------------

        if not requested_by.strip():

            st.error(
                "Requested By is required."
            )
            return

        if not purpose.strip():

            st.error(
                "Purpose is required."
            )
            return

        try:

            # ------------------------------------------------------
            # Create Product Request
            # ------------------------------------------------------

            request = create_sample_request(
                items=requested_items,
                required_from=required_from,
                required_until=required_until,
                requested_by=(
                    requested_by.strip()
                ),
                purpose=purpose.strip(),
            )

            # ------------------------------------------------------
            # Send admin notification
            #
            # Email failure must NOT undo the PR.
            # ------------------------------------------------------

            email_sent = False

            try:

                request_detail = (
                    get_sample_request_detail(
                        request["id"]
                    )
                )

                if not request_detail:
                    raise RuntimeError(
                        (
                            "Product Request detail "
                            "could not be loaded."
                        )
                    )

                send_product_request_notification(
                    request_detail
                )

                email_sent = True

            except Exception as email_error:

                print(
                    (
                        "Product Request email "
                        "failed:"
                    ),
                    email_error,
                )

            # ------------------------------------------------------
            # Save success details before clearing form
            # ------------------------------------------------------

            success_data = {
                "request_number": (
                    request[
                        "request_number"
                    ]
                ),
                "request_status": (
                    request[
                        "request_status"
                    ]
                ),
                "item_count": (
                    request[
                        "item_count"
                    ]
                ),
                "email_sent": (
                    email_sent
                ),
            }

            # ------------------------------------------------------
            # Clear form
            # ------------------------------------------------------

            _reset_product_request_form()

            st.session_state[
                "product_request_success"
            ] = success_data

            st.rerun()

        except Exception as exc:

            st.error(
                (
                    "Could not create Product "
                    f"Request: {exc}"
                )
            )