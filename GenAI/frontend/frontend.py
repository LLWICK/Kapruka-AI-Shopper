
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Kapruka AI Shopper",
    page_icon="🛍️",
    layout="wide",
)

st.title("🛍️ Kapruka AI Shopper")
st.caption("Your AI shopping assistant, powered by LangGraph and MCP.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! 👋 Welcome to Kapruka AI Shopper. "
                "What are you looking for today? You can search for products, "
                "find gifts, or ask me to compare items."
            ),
            "products": [],
        }
    ]


def extract_products(data):
    """Support common API response formats."""
    products = data.get("products", data.get("searchItems", []))

    if isinstance(products, dict):
        products = products.get("products", products.get("searchItems", []))

    return products if isinstance(products, list) else []


def render_products(products):
    """Display product results as cards in the chat."""
    if not products:
        return

    st.markdown(f"**Found {len(products)} product(s):**")

    columns_per_row = 2

    for start in range(0, len(products), columns_per_row):
        columns = st.columns(columns_per_row)

        for column, product in zip(
            columns,
            products[start:start + columns_per_row],
        ):
            with column:
                with st.container(border=True):
                    name = product.get("name", "Unnamed product")
                    image_url = product.get("image_url")
                    price = product.get("price")
                    currency = product.get("currency", "LKR")
                    summary = product.get("summary", "")
                    product_url = product.get("product_url")
                    in_stock = product.get("in_stock")

                    if image_url:
                        st.image(image_url, use_container_width=True)

                    st.markdown(f"**{name}**")

                    if price is not None:
                        try:
                            formatted_price = f"{float(price):,.2f}"
                        except (ValueError, TypeError):
                            formatted_price = str(price)

                        st.markdown(f"### {currency} {formatted_price}")

                    if summary:
                        st.write(summary)

                    if in_stock is True:
                        st.success("In stock")
                    elif in_stock is False:
                        st.warning("Currently out of stock")

                    if product_url:
                        st.link_button(
                            "View on Kapruka ↗",
                            product_url,
                            use_container_width=True,
                        )


# Sidebar
with st.sidebar:
    st.header("🛍️ Kapruka AI Shopper")
    st.write("Your personal AI shopping assistant.")
    st.divider()
    st.caption("Backend: FastAPI")
    st.caption("Orchestration: LangGraph")
    st.caption("Tools: MCP")

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Conversation cleared! What would you like to shop for?",
                "products": [],
            }
        ]
        st.rerun()


# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("products"):
            render_products(message["products"])


# Chat input
if prompt := st.chat_input("Ask me to find a product or gift..."):
    # Display and store the user's message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # Query the FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Searching for products..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat",
                    json={"query": prompt},
                    timeout=120,
                )
                response.raise_for_status()
                data = response.json()

                products = extract_products(data)

                # Use the backend's message if available.
                if data.get("answer"):
                    answer = data["answer"]
                elif data.get("message"):
                    answer = data["message"]
                elif products:
                    answer = "Here are the products I found for you."
                else:
                    answer = (
                        "I couldn't find matching products. "
                        "Try a different search or more specific keywords."
                    )

                st.markdown(answer)

                if products:
                    render_products(products)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "products": products,
                    }
                )

            except requests.exceptions.ConnectionError:
                error_message = (
                    "I couldn't connect to the shopping service. "
                    "Please check that the FastAPI backend is running."
                )
                st.error(error_message)

                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message}
                )

            except requests.exceptions.Timeout:
                error_message = (
                    "The search is taking longer than expected. "
                    "Please try again."
                )
                st.error(error_message)

                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message}
                )

            except requests.exceptions.HTTPError as exc:
                error_message = f"The backend returned an error: {exc}"
                st.error(error_message)

                # Show details while developing.
                st.code(response.text)

                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message}
                )

            except (requests.exceptions.RequestException, ValueError) as exc:
                error_message = f"Something went wrong: {exc}"
                st.error(error_message)

                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message}
                )
