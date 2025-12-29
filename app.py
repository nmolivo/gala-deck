"""Gala Deck Chat - Streamlit UI"""
import logging
import sys
import streamlit as st
from anthropic import Anthropic

from src.config import APP_TITLE, CHAT_PLACEHOLDER, calculate_cost
from src.chat_handler import ChatHandler

# Page config
st.set_page_config(page_title="Gala Deck Chat", page_icon="💬")
st.title(APP_TITLE)

# Force logs to stdout (Streamlit's terminal)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Explicitly use stdout
    ],
    force=True  # Override any existing config
)

logger = logging.getLogger(__name__)
logger.info("🚀 App starting - you should see this!")

# Initialize Anthropic client
if "anthropic_client" not in st.session_state:
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("Please add ANTHROPIC_API_KEY to .streamlit/secrets.toml")
        st.stop()
    st.session_state.anthropic_client = Anthropic(api_key=api_key)

# Initialize chat handler
if "chat_handler" not in st.session_state:
    st.session_state.chat_handler = ChatHandler(
        st.session_state.anthropic_client)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize session totals (OPTIONAL - for tracking across requests)
if "total_usage" not in st.session_state:
    st.session_state.total_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_cost": 0.0,
        "request_count": 0,
    }

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Sidebar
with st.sidebar:
    st.header("🔧 MCP Test")

    if st.button("Test Connection"):
        with st.spinner("Testing MCP..."):
            test_messages = [
                {"role": "user", "content": "List all available routes"}
            ]
            result, _ = st.session_state.chat_handler.chat(
                test_messages)  # Note: unpack tuple
            st.write(result)

    # Session stats (OPTIONAL)
    st.divider()
    st.header("📊 Session Stats")
    st.metric("Requests", st.session_state.total_usage["request_count"])
    st.metric("Total Tokens",
              st.session_state.total_usage["input_tokens"] +
              st.session_state.total_usage["output_tokens"])
    st.metric("Total Cost",
              f"${st.session_state.total_usage['total_cost']:.4f}")

    if st.button("Reset Stats"):
        st.session_state.total_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_cost": 0.0,
            "request_count": 0,
        }
        st.rerun()

    if st.button("Test MCP Server"):
        import subprocess
        try:
            result = subprocess.run(
                ["node", "vapi-doc-coding-mcp/build/index.js", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            st.write("Node output:", result.stdout or result.stderr)
        except Exception as e:
            st.error(f"MCP server test failed: {e}")

# Chat input
if prompt := st.chat_input(CHAT_PLACEHOLDER):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response, usage = st.session_state.chat_handler.chat(
                st.session_state.messages)
            st.markdown(response)

            # Display usage stats for THIS request
            if usage:
                with st.expander("📊 Token Usage & Cost", expanded=False):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Input", usage.get("input_tokens", 0))
                    with col2:
                        st.metric("Output", usage.get("output_tokens", 0))
                    with col3:
                        total = usage.get("input_tokens", 0) + \
                            usage.get("output_tokens", 0)
                        st.metric("Total", total)
                    with col4:
                        cost = calculate_cost(usage)
                        st.metric("Cost", f"${cost:.4f}")

                    # Show cache stats if available
                    if usage.get("cache_read_input_tokens", 0) > 0:
                        st.info(
                            f"💾 Cache hits: {usage['cache_read_input_tokens']} tokens")
                    if usage.get("cache_creation_input_tokens", 0) > 0:
                        st.info(
                            f"💾 Cache writes: {usage['cache_creation_input_tokens']} tokens")

                # Update session totals (OPTIONAL)
                st.session_state.total_usage["input_tokens"] += usage.get(
                    "input_tokens", 0)
                st.session_state.total_usage["output_tokens"] += usage.get(
                    "output_tokens", 0)
                st.session_state.total_usage["total_cost"] += cost
                st.session_state.total_usage["request_count"] += 1

    # Add assistant message
    st.session_state.messages.append(
        {"role": "assistant", "content": response})
