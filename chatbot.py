import streamlit as st
import requests
import os

# Get the FastAPI URL from environment variable
FASTAPI_URL = os.getenv('FASTAPI_URL', 'http://localhost:8000')

st.set_page_config(
    page_title="FIFA Laws Chatbot",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ FIFA Laws Chatbot")
st.markdown("""
Ask questions about FIFA laws and regulations. The chatbot will provide answers based on official FIFA documentation.
""")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources") and message["role"] == "assistant":
            with st.expander("View Sources"):
                for source in message["sources"]:
                    st.markdown(f"**{source['title']}**")
                    st.markdown(source['content'])
                    st.markdown(f"Relevance Score: {source['relevance_score']:.2f}")
                    st.markdown("---")

# Accept user input
if prompt := st.chat_input("Ask about FIFA laws..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        # Get bot response
        with st.spinner('Thinking...'):
            response = requests.post(
                f"{FASTAPI_URL}/api/chat",
                json={"question": prompt},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                assistant_response = data["answer"]
                sources = data.get("sources", [])
                
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    st.markdown(assistant_response)
                    if sources:
                        with st.expander("View Sources"):
                            for source in sources:
                                st.markdown(f"**{source['title']}**")
                                st.markdown(source['content'])
                                st.markdown(f"Relevance Score: {source['relevance_score']:.2f}")
                                st.markdown("---")
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_response,
                    "sources": sources
                })
            else:
                st.error(f"Error: Failed to get response from server. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Add a sidebar with additional information
with st.sidebar:
    st.markdown("### About")
    st.markdown("""
    This chatbot uses RAG (Retrieval-Augmented Generation) to provide accurate answers about FIFA laws and regulations.
    
    The responses are based on official FIFA documentation and include relevant source information for verification.
    """)