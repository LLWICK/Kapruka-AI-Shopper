
import streamlit as st


def get_value(data, *keys, default=None):
    """Get the first available field from a dictionary."""
    if not isinstance(data, dict):
        return default

    for key in keys:
        value = data.get(key)

        if value is not None and value != "":
            return value

    return default


def render_products(products):

    if not products:
        return

    st.markdown("### 🛍️ Products found")

    for start in range(0, len(products), 2):

        cols = st.columns(2)

        for col, product in zip(cols, products[start:start + 2]):

            product_id = str(product.get("product_id", ""))

            if not product_id:
                continue

            name = product.get(
                "name",
                product.get("title", "Product")
            )

            price = product.get(
                "price",
                product.get("displayed_price", "Price unavailable")
            )

            image = product.get(
                "image_url",
                product.get("image")
            )

            product_url = product.get(
                "product_url",
                product.get("url")
            )

            with col:

                with st.container(border=True):

                    if image:
                        st.image(
                            image,
                            use_container_width=True
                        )

                    st.markdown(f"**{name}**")
                    st.markdown(f"**Rs. {price}**")

                    if product_url:
                        st.link_button(
                            "View on Kapruka",
                            product_url,
                            use_container_width=True
                        )

                    selected_id = st.session_state.get(
                        "selected_product_id"
                    )

                    if selected_id == product_id:
                        st.success("Selected product")

                    # Product details action
                    if st.button(
                        "🔍 Ask about this product",
                        key=f"details_{product_id}",
                        use_container_width=True
                    ):

                        st.session_state.selected_product_id = product_id

                        st.session_state.pending_prompt = (
                            f"Tell me more about {name}."
                        )

                        st.rerun()

                    # Add to cart action
                    if st.button(
                        "🛒 Add to Cart",
                        key=f"cart_{product_id}",
                        use_container_width=True
                    ):

                        st.session_state.selected_product_id = product_id

                        st.session_state.pending_prompt = (
                            "Add this selected product to my cart."
                        )

                        st.rerun()


def render_cart(cart):
    if not cart:
        return

    st.markdown("### 🛒 Your Cart")

    if isinstance(cart, dict):
        items = cart.get("items", [])

        if items:
            st.dataframe(
                items,
                use_container_width=True,
                hide_index=True
            )

        item_count = cart.get("item_count")
        subtotal = cart.get("subtotal")
        currency = cart.get("currency", "LKR")

        if item_count is not None:
            st.metric("Items", item_count)

        if subtotal is not None:
            st.metric("Subtotal", f"{currency} {subtotal}")

    elif isinstance(cart, list):
        st.dataframe(
            cart,
            use_container_width=True,
            hide_index=True
        )


def render_checkout(checkout):
    if not checkout:
        return

    st.markdown("### 💳 Checkout")

    if isinstance(checkout, dict):
        status = checkout.get("status")

        if status:
            st.info(f"Checkout status: {status}")

        missing_fields = checkout.get("missing_fields", [])

        if missing_fields:
            st.warning(
                "Please provide: " + ", ".join(missing_fields)
            )

        checkout_url = checkout.get("checkout_url")

        if checkout_url:
            st.link_button(
                "Continue to Checkout",
                checkout_url
            )


def render_response(data):
    """
    Render the response returned by the FastAPI endpoint.
    Supports text, products, comparison, cart and checkout.
    """

    if not isinstance(data, dict):
        st.write(data)
        return

    # Support either a direct response or a nested response.
    result = data.get("response", data)

    if not isinstance(result, dict):
        st.write(result)
        return

    answer = get_value(
        result,
        "answer",
        "message",
        "response",
        default=""
    )

    if answer:
        st.markdown(answer)

    products = result.get("products", [])

    if isinstance(products, list) and products:
        total = result.get("total_results")

        if total is not None:
            st.caption(f"{total} product(s) found")

        render_products(products)

    comparison = result.get("comparison")
    render_comparison(comparison)

    cart = result.get("cart")
    render_cart(cart)

    checkout = result.get("checkout")
    render_checkout(checkout)

    # Display other agent-specific fields if needed.
    recommendation = result.get("recommendation")

    if recommendation:
        st.markdown("**Recommendation**")
        st.write(recommendation)
