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

# Initialize session state
if "products" not in st.session_state:
    st.session_state.products = []
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# Sidebar
with st.sidebar:
    st.header("About")
    st.write(
        "Describe what you want to buy. "
        "The AI assistant will search for matching products."
    )
    st.caption("Backend: FastAPI")
    st.caption("Agent orchestration: LangGraph")
    st.caption("Product tools: MCP")

# Search form
with st.form("product_search", clear_on_submit=False):
    query = st.text_input(
        "What are you looking for?",
        placeholder="e.g. smartwatch, birthday gift, chocolates...",
    )
    submitted = st.form_submit_button(
        "🔎 Search Products",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if not query.strip():
        st.warning("Please enter a product or describe what you need.")
    else:
        with st.spinner("Searching Kapruka products..."):
            try:
                response = requests.post(
                    f"{API_URL}/search",
                    json={"query": query.strip()},
                    timeout=120,
                )
                response.raise_for_status()
                data = response.json()

                # Adjust this mapping if your API uses another field name.
                products = data.get("products", data.get("searchItems", []))

                if isinstance(products, dict):
                    products = products.get("products", [])

                st.session_state.products = products or []
                st.session_state.last_query = query.strip()

                if not st.session_state.products:
                    st.info(data.get("message", "No matching products were found."))

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to the backend. "
                    "Make sure FastAPI is running at http://127.0.0.1:8000."
                )
            except requests.exceptions.Timeout:
                st.error("The search took too long. Please try again.")
            except requests.exceptions.HTTPError as exc:
                st.error(f"Backend returned an error: {exc}")
                st.code(response.text)
            except (requests.exceptions.RequestException, ValueError) as exc:
                st.error(f"Could not complete the search: {exc}")

# Results
products = st.session_state.products

if products:
    st.subheader(f"Results for: {st.session_state.last_query}")
    st.write(f"Found {len(products)} product(s).")

    columns_per_row = 3

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
                    else:
                        st.caption("No product image available")

                    st.markdown(f"**{name}**")

                    if price is not None:
                        try:
                            formatted_price = f"{float(price):,.2f}"
                        except (ValueError, TypeError):
                            formatted_price = str(price)

                        st.markdown(f"### {currency} {formatted_price}")

                    if summary:
                        st.write(summary)

                    if in_stock is not None:
                        if in_stock:
                            st.success("In stock")
                        else:
                            st.warning("Currently out of stock")

                    if product_url:
                        st.link_button(
                            "View on Kapruka ↗",
                            product_url,
                            use_container_width=True,
                        )

elif not submitted:
    st.info("Enter a product name above to start shopping.")

st.divider()
st.caption("Kapruka AI Shopper · Built with Streamlit, FastAPI, LangGraph and MCP")