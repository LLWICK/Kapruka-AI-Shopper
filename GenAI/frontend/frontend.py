
import uuid
import streamlit as st

from api import send_message
from components import render_response


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Kapruka AI Shopper",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

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
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "api_error" not in st.session_state:
    st.session_state.api_error = None


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.markdown("## 🛍️ Kapruka AI Shopper")

    st.caption("Your intelligent shopping assistant")

    st.divider()

    if st.button(
        "＋ New Conversation",
        use_container_width=True
    ):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.api_error = None
        st.rerun()

    st.divider()

    st.markdown("### What can I help you with?")

    st.markdown("""
    - 🔍 Find products
    - 📦 Get product information
    - ⚖️ Compare products
    - 🎁 Discover gift ideas
    - 🛒 Manage your shopping cart
    - 💳 Continue to checkout
    - 🚚 Track your orders
    """)

    st.divider()

    st.markdown("### Conversation")

    st.caption(
        f"Session: {st.session_state.thread_id[:8]}..."
    )

    st.caption(
        f"Messages: {len(st.session_state.messages)}"
    )

    st.markdown(
        '<p class="status-text">Powered by Kapruka AI</p>',
        unsafe_allow_html=True
    )


# --------------------------------------------------
# HEADER
# --------------------------------------------------

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


# --------------------------------------------------
# WELCOME SCREEN
# --------------------------------------------------

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


# --------------------------------------------------
# DISPLAY CONVERSATION HISTORY
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["role"] == "user":
            st.markdown(message["content"])

        else:
            render_response(message["content"])


# --------------------------------------------------
# CHAT INPUT
# --------------------------------------------------

prompt = st.chat_input(
    "Ask me to find a product, compare items, or get more details..."
)

# Support suggested prompts.
if not prompt and "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")


# --------------------------------------------------
# PROCESS USER MESSAGE
# --------------------------------------------------

if prompt:

    # Add user message to the UI history.
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Call FastAPI.
    with st.chat_message("assistant"):

        with st.spinner("Kapruka AI is thinking..."):

            try:
                result = send_message(
                    query=prompt,
                    thread_id=st.session_state.thread_id
                )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result
                })

                render_response(result)

            except Exception as exc:

                error_message = str(exc)

                st.error(error_message)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": {
                        "answer": (
                            "Sorry, I couldn't process your request. "
                            "Please try again."
                        )
                    }
                })

    st.rerun()
