import streamlit as st
import os
import openai
import json
from google.cloud import dialogflow_v2 as dialogflow
import os
from google.cloud import dialogflow_v2 as dialogflow
from google.oauth2 import service_account
import time
from openai import OpenAI


# Set the path to your service account key file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "dialogflow-key.json"

class AdvancedChatbot:
    def __init__(self, openai_api_key=None):
        if openai_api_key is None:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        else:
            openai.api_key = openai_api_key
        self.conversation_history = []
    
    def get_dialogflow_response(text_input, session_id="123456"):

    # Set your Google Cloud service account key path
        credentials = service_account.Credentials.from_service_account_file(
            "dialogflow-key.json"
        )

        project_id = "customersupportbot-suoj"
        session_client = dialogflow.SessionsClient(credentials=credentials)
        session = session_client.session_path(project_id, session_id)
        text_input = dialogflow.TextInput(text=prompt, language_code="en-US")
        query_input = dialogflow.QueryInput(text=text_input)


        response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )

        return response.query_result.fulfillment_text
        

    def get_openai_response_with_retry(text, max_retries=3):
        client = OpenAI(openai.api_key)
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": text}],
                    max_tokens=150
                )
                return response.choices[0].message.content
            except openai.RateLimitError:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return "I'm currently experiencing high demand. Please try again in a moment."
            except Exception as e:
                return f"Error: {str(e)}"
        
    def get_response(self, user_input):
        """Get response using ChatGPT API with context"""
        
        system_prompt = """
        You are a helpful customer support chatbot for an e-commerce company.
        You can help with:
        - Order tracking and delivery questions
        - Payment and billing issues
        - Returns and refunds
        - Technical support
        - Store information
        
        Be friendly, helpful, and professional. If you can't help with something,
        direct users to human support at 1-800-SUPPORT.
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            bot_response = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            # Keep only last 10 exchanges to manage token limits
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return bot_response
            
        except Exception as e:
            return f"I'm sorry, I'm having technical difficulties. Please try again or contact support at 1-800-SUPPORT. Error: {str(e)}"

# Usage example
chatbot = AdvancedChatbot(openai.api_key)
response = chatbot.get_response("Where is my order?")
print(response)
# Page config
st.set_page_config(
    page_title="Customer Support Chatbot",
    page_icon="🤖",
    layout="wide",
    
)

# Sidebar
st.sidebar.title("🤖 Chatbot Demo")
st.sidebar.info("This chatbot can help with orders, payments, returns, and more!")

# Main title
st.title("Customer Support Chatbot")
st.write("Ask me anything about your orders, payments, or general questions!")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add welcome message
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hello! 👋 I'm your customer support assistant. How can I help you today?"
    })

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get bot response (you'll need to implement this function)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = AdvancedChatbot.get_dialogflow_response(prompt)
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})


# Sidebar features
with st.sidebar:
    st.subheader("Quick Actions")
    if st.button("🛍️ Track Order"):
        st.session_state.messages.append({"role": "user", "content": "Track my order"})
        st.rerun()
    
    if st.button("💳 Payment Help"):
        st.session_state.messages.append({"role": "user", "content": "I have a payment issue"})
        st.rerun()
    
    if st.button("🔄 Return Item"):
        st.session_state.messages.append({"role": "user", "content": "I want to return an item"})
        st.rerun()
    
    st.subheader("Contact Info")
    st.info("📞 1-800-SUPPORT\n💬 Live Chat Available\n📧 support@company.com")