import streamlit as st
import streamlit.components.v1 as components

# ✅ Page config must be the first Streamlit command
st.set_page_config(page_title="📄 Gemini AI Assistant")

from langchain_community.chat_message_histories import ChatMessageHistory
from google.cloud import bigquery
import google.generativeai as genai
from google.api_core.exceptions import BadRequest

# GCP LLM Configurations using Google API key and google.generativeai
# --------------------
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "xx")
GOOGLE_PROJECT = st.secrets.get("GOOGLE_PROJECT", "xx")
GOOGLE_LOCATION = st.secrets.get("GOOGLE_LOCATION", "us-central1")
genai.configure(api_key=GOOGLE_API_KEY)

# BigQuery client setup
client = bigquery.Client()

model_name = "gemini-1.5-pro-002"

def inject_custom_css():
    st.markdown(
        """
        <style>
        .stApp { overflow: visible !important; }
        df-messenger {
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            z-index: 9999 !important;
            /* theme overrides */
            --df-messenger-font-color: #000;
            --df-messenger-font-family: 'Google Sans', sans-serif;
            --df-messenger-chat-background: #f3f6fc;
            --df-messenger-message-user-background: #d3e3fd;
            --df-messenger-message-bot-background: #ffffff;
            --df-messenger-chat-min-height: 430px;
            --df-messenger-chat-max-height: 80vh;
            --df-messenger-chat-min-width: 300px;
            --df-messenger-chat-max-width: 400px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
def render_dialogflow_messenger():
    html = """
    <link rel="stylesheet"
          href="https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/themes/df-messenger-default.css">
    <script src="https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/df-messenger.js"></script>
    <df-messenger
      project-id="analog-grin-455718-i4"
      agent-id="40243f29-c390-4320-88b3-af14a8a24a82"
      language-code="en"
      chat-title="project-assistant">
    </df-messenger>
    """
    components.html(html, height=600, width=400)



# ✅ Answer code questions from BigQuery
def get_reviews_from_bigquery():
    query = "SELECT code FROM `UserInput.user_input` LIMIT 100"
    try:
        query_job = client.query(query)
        results = query_job.result()
        return [row.code for row in results]
    except Exception as e:
        return [f"Error fetching reviews: {str(e)}"]

# Create prompt for Gemini
def create_prompt(reviews, question):
    reviews_text = "\n".join(reviews)
    return f"""
You are a helpful assistant analyzing code questions.

[REVIEWS START]
{reviews_text}
[REVIEWS END]

Answer the following question based only on the information above:

Question: {question}
"""

# App UI setup
inject_custom_css()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.chatMessageHistory = ChatMessageHistory()

# Sidebar toggle for assistant
show_chat_assistant = st.sidebar.checkbox("Show Chat Assistant", False)
st.sidebar.markdown("### Project Assistant")
st.sidebar.markdown("Check the box above to show the project assistant chat.")

if show_chat_assistant:
    st.subheader("Project Assistant Chat")
    st.write("Use the Chat Assistant to ask questions about the project.")
    st.sidebar.success("Assistant Chat Enabled")
    render_dialogflow_messenger()
else:
    st.subheader("Gemini AI Code Assistant")
    st.write("Ask questions about Code stored in BigQuery.")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask any question to assist you"):
        st.session_state.chatMessageHistory.add_message({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        try:
            reviews = get_reviews_from_bigquery()
            prompt = create_prompt(reviews, user_input)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            answer = response.text.strip()

            st.session_state.chatMessageHistory.add_message({"role": "assistant", "content": answer})
            st.session_state.messages.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)

        except Exception as e:
            with st.chat_message("assistant"):
                st.error("An error occurred while generating a response.")
                st.error(f"Details: {str(e)}")