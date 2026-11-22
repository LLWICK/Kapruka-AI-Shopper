
import uuid
import streamlit as st

from api import send_message
from components import render_response


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Kapruka AI Shopper",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .main-title {
        font-size: 2rem;
        font-weight: 750;
        margin-bottom: 0;
    }

    .subtitle {
        color: #888888;
        font-size: 0.95rem;
        margin-top: 5px;
    }

    .stChatMessage {
        border-radius: 12px;
    }

    div[data-testid="stChatInput"] {
        padding-bottom: 15px;
    }

    .status-text {
        color: #888888;
        font-size: 0.8rem;
    }

    .selected-product {
        padding: 12px;
        border-radius: 10px;
        background-color: rgba(128, 128, 128, 0.08);
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

def initialize_session():

    defaults = {
        "messages": [],
        "thread_id": str(uuid.uuid4()),
        "selected_product_id": None,
        "selected_product": None,
        "pending_prompt": None,
        "api_error": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


initialize_session()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def start_new_conversation():

    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4())

    st.session_state.selected_product_id = None
    st.session_state.selected_product = None

    st.session_state.pending_prompt = None
    st.session_state.api_error = None


def select_product(product: dict):

    product_id = product.get(
        "product_id",
        product.get("id")
    )

    if not product_id:
        st.error("This product does not have a valid product ID.")
        return

    st.session_state.selected_product_id = str(product_id)
    st.session_state.selected_product = product


def clear_product_selection():

    st.session_state.selected_product_id = None
    st.session_state.selected_product = None


def get_product_name(product: dict):

    return product.get(
        "name",
        product.get(
            "title",
            product.get("product_name", "Selected Product")
        )
    )


def get_product_price(product: dict):

    return product.get(
        "price",
        product.get(
            "displayed_price",
            product.get("selling_price", "Price unavailable")
        )
    )


def get_product_image(product: dict):

    return product.get(
        "image_url",
        product.get(
            "image",
            product.get("product_image")
        )
    )


# ============================================================
# PRODUCT CARD RENDERER
# ============================================================

def render_interactive_products(products):

    if not isinstance(products, list) or not products:
        return

    st.markdown("### 🛍️ Products found")

    total_results = st.session_state.get("total_results")

    if total_results is not None:
        st.caption(f"{total_results} product(s) found")

    for start in range(0, len(products), 2):

        cols = st.columns(2)

        for col, product in zip(cols, products[start:start + 2]):

            if not isinstance(product, dict):
                continue

            product_id = product.get(
                "product_id",
                product.get("id")
            )

            if not product_id:
                st.warning("Product ID unavailable for one result.")
                continue

            product_id = str(product_id)

            name = get_product_name(product)
            price = get_product_price(product)
            image = get_product_image(product)

            product_url = product.get(
                "product_url",
                product.get("url", product.get("link"))
            )

            selected = (
                st.session_state.selected_product_id == product_id
            )

            with col:

                with st.container(border=True):

                    if image:
                        st.image(
                            image,
                            use_container_width=True
                        )

                    st.markdown(f"**{name}**")

                    st.markdown(f"**Price: Rs. {price}**")

                    description = product.get(
                        "description",
                        product.get("short_description")
                    )

                    if description:
                        st.caption(str(description))

                    if product_url:
                        st.link_button(
                            "View on Kapruka",
                            product_url,
                            use_container_width=True
                        )

                    if selected:
                        st.success("Currently selected")

                    # ------------------------------------
                    # SELECT / VIEW DETAILS
                    # ------------------------------------

                    if st.button(
                        "🔍 Ask about this product",
                        key=f"details_{product_id}",
                        use_container_width=True
                    ):

                        select_product(product)

                        st.session_state.pending_prompt = (
                            f"Tell me more about {name}."
                        )

                        st.rerun()

                    # ------------------------------------
                    # ADD TO CART
                    # ------------------------------------

                    if st.button(
                        "🛒 Add to Cart",
                        key=f"cart_{product_id}",
                        type="primary",
                        use_container_width=True
                    ):

                        select_product(product)

                        st.session_state.pending_prompt = (
                            "Add this selected product to my cart."
                        )

                        st.rerun()


# ============================================================
# RESPONSE RENDERER
# ============================================================

def render_assistant_response(response: dict):

    if not isinstance(response, dict):
        st.write(response)
        return

    # Support direct and nested API responses.
    data = response.get("response", response)

    if not isinstance(data, dict):
        st.write(data)
        return

    # ------------------------------------
    # TEXT RESPONSE
    # ------------------------------------

    answer = data.get(
        "message",
        data.get(
            "answer",
            data.get("response", "")
        )
    )

    if answer:
        st.markdown(answer)

    # ------------------------------------
    # PRODUCT RESULTS
    # ------------------------------------

    products = data.get("products", [])

    if isinstance(products, list) and products:

        st.session_state.total_results = data.get(
            "total_results"
        )

        render_interactive_products(products)

    # ------------------------------------
    # PRODUCT DETAILS
    # ------------------------------------

    detail_output = data.get("detail_agent_output")

    if isinstance(detail_output, dict):

        detail_message = detail_output.get("message")

        if detail_message and detail_message != answer:
            st.markdown(detail_message)

    # ------------------------------------
    # PRODUCT COMPARISON
    # ------------------------------------

    comparison = data.get("comparison")

    if comparison:

        st.markdown("### ⚖️ Product Comparison")

        if isinstance(comparison, list):

            st.dataframe(
                comparison,
                use_container_width=True,
                hide_index=True
            )

        elif isinstance(comparison, dict):

            rows = comparison.get("rows")

            if isinstance(rows, list):

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.json(comparison)

    # ------------------------------------
    # CART
    # ------------------------------------

    cart = data.get("cart")

    if isinstance(cart, dict):

        st.markdown("### 🛒 Your Shopping Cart")

        items = cart.get("items", [])

        if items:

            st.dataframe(
                items,
                use_container_width=True,
                hide_index=True
            )

        item_count = cart.get("item_count", 0)
        subtotal = cart.get("subtotal", 0)
        currency = cart.get("currency", "LKR")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Items", item_count)

        with col2:
            st.metric("Subtotal", f"{currency} {subtotal:,.2f}")

    # ------------------------------------
    # CHECKOUT
    # ------------------------------------

    checkout = data.get("checkout")

    if isinstance(checkout, dict):

        st.markdown("### 💳 Checkout")

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

    # ------------------------------------
    # RECOMMENDATION
    # ------------------------------------

    recommendation = data.get("recommendation")

    if recommendation:
        st.markdown("### ⭐ Recommendation")
        st.write(recommendation)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🛍️ Kapruka AI Shopper")

    st.caption("Your intelligent shopping assistant")

    st.divider()

    if st.button(
        "＋ New Conversation",
        use_container_width=True
    ):

        start_new_conversation()
        st.rerun()

    st.divider()

    st.markdown("### 🛍️ Shopping Assistant")

    st.markdown("""
    - 🔍 Search products
    - 📦 Explore product details
    - ⚖️ Compare products
    - 🎁 Discover gift ideas
    - 🛒 Manage your cart
    - 💳 Checkout
    """)

    # ------------------------------------
    # SELECTED PRODUCT
    # ------------------------------------

    st.divider()

    st.markdown("### 📌 Currently Selected")

    selected_product = st.session_state.selected_product

    if selected_product:

        selected_name = get_product_name(selected_product)
        selected_price = get_product_price(selected_product)
        selected_image = get_product_image(selected_product)

        if selected_image:
            st.image(
                selected_image,
                use_container_width=True
            )

        st.markdown(f"**{selected_name}**")

        st.caption(f"Price: Rs. {selected_price}")

        st.caption(
            f"Product ID: {st.session_state.selected_product_id}"
        )

        if st.button(
            "Clear Selection",
            use_container_width=True
        ):

            clear_product_selection()
            st.rerun()

    else:

        st.caption("No product selected yet.")

    # ------------------------------------
    # CONVERSATION INFORMATION
    # ------------------------------------

    st.divider()

    st.markdown("### 💬 Conversation")

    st.caption(
        f"Session: {st.session_state.thread_id[:8]}..."
    )

    st.caption(
        f"Messages: {len(st.session_state.messages)}"
    )

    st.divider()

    st.markdown(
        '<p class="status-text">Powered by Kapruka AI</p>',
        unsafe_allow_html=True
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    '<p class="main-title">🛍️ Kapruka AI Shopper</p>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="subtitle">'
    'Find products, explore details, compare options, '
    'and shop through a conversational AI assistant.'
    '</p>',
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# WELCOME SCREEN
# ============================================================

if not st.session_state.messages:

    st.markdown("### Hello! What are you looking for today?")

    st.write(
        "I'm your Kapruka shopping assistant. "
        "Tell me what you need, and I'll help you find it."
    )

    suggestions = [
        "Find birthday cakes under Rs. 7,000",
        "Recommend a gift for my father",
        "Show me popular electronic gadgets",
        "Find flowers for a birthday",
    ]

    cols = st.columns(2)

    for index, suggestion in enumerate(suggestions):

        with cols[index % 2]:

            if st.button(
                suggestion,
                key=f"suggestion_{index}",
                use_container_width=True
            ):

                st.session_state.pending_prompt = suggestion
                st.rerun()


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["role"] == "user":

            st.markdown(message["content"])

        else:

            render_assistant_response(message["content"])


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Ask me to find a product, compare items, or get more details..."
)


# ============================================================
# HANDLE SUGGESTED / PRODUCT CARD PROMPTS
# ============================================================

if not prompt and st.session_state.pending_prompt:

    prompt = st.session_state.pending_prompt

    st.session_state.pending_prompt = None


# ============================================================
# PROCESS USER MESSAGE
# ============================================================

if prompt:

    # ------------------------------------
    # ADD USER MESSAGE TO HISTORY
    # ------------------------------------

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # ------------------------------------
    # CALL FASTAPI
    # ------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Kapruka AI is thinking..."):

            try:

                result = send_message(
                    query=prompt,
                    thread_id=st.session_state.thread_id,
                    selected_product_id=(
                        st.session_state.selected_product_id
                    )
                )

                st.session_state.api_error = None

                # Save assistant response.
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result
                })

                render_assistant_response(result)

            except Exception as exc:

                error_message = str(exc)

                st.session_state.api_error = error_message

                st.error(error_message)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": {
                        "message": (
                            "Sorry, I couldn't process your request. "
                            "Please try again."
                        )
                    }
                })

    st.rerun()
