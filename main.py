import os
import json
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import requests

# Load environment variables
load_dotenv()

# Constants
SYSTEM_PROMPT = """You are PortAgent, a professional freelancing assistant embedded in a developer's portfolio. 
Your role is to:
1. Greet visitors professionally
2. Understand their project requirements
3. Ask clarifying questions
4. Provide helpful responses
5. Help structure project briefs

Be concise, friendly, and professional. When the conversation reaches a point where a task can be defined, 
present a structured summary and ask for confirmation to save it.

If asked about capabilities, you can mention:
- Web Development (Frontend/Backend)
- Mobile App Development
- UI/UX Design
- API Integration
- Database Design
- And other technical services

Always ask for clarification if requirements are unclear."""

class PortAgent:
    def __init__(self):
        self.setup_services()
        
    def setup_services(self):
        """Initialize all required services with error handling."""
        try:
            # Google Services
            creds = None
            if os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS')):
                creds = service_account.Credentials.from_service_account_file(
                    os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
                    scopes=[
                        'https://www.googleapis.com/auth/drive',
                        'https://www.googleapis.com/auth/documents',
                        'https://www.googleapis.com/auth/spreadsheets'
                    ]
                )
            
            self.drive_service = build('drive', 'v3', credentials=creds)
            self.docs_service = build('docs', 'v1', credentials=creds)
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            
            # Initialize SendGrid
            self.sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
            
        except Exception as e:
            st.error(f"Error initializing services: {str(e)}")
            raise

    def query_openrouter(self, messages, model="openai/gpt-3.5-turbo"):
        """Query OpenRouter API with conversation history."""
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            # Format messages for OpenRouter
            formatted_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            formatted_messages.extend(messages)
            
            payload = {
                "model": model,
                "messages": formatted_messages
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except Exception as e:
            st.error(f"Error querying OpenRouter: {str(e)}")
            return "I apologize, but I encountered an error processing your request."

    def create_google_doc(self, title, content):
        """Create a Google Doc with the conversation history."""
        try:
            # Create document
            doc = self.docs_service.documents().create(body={"title": title}).execute()
            doc_id = doc['documentId']
            
            # Add content
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': content
                    }
                }
            ]
            self.docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            
            # Move to folder if specified
            folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
            if folder_id:
                self.drive_service.files().update(
                    fileId=doc_id,
                    addParents=folder_id,
                    fields='id, parents'
                ).execute()
            
            # Set permissions
            self.drive_service.permissions().create(
                fileId=doc_id,
                body={"role": "writer", "type": "anyone"},
                fields='id'
            ).execute()
            
            return f"https://docs.google.com/document/d/{doc_id}/edit"
            
        except Exception as e:
            st.error(f"Error creating Google Doc: {str(e)}")
            return None

    def log_to_sheet(self, client_data):
        """Log client interaction to Google Sheets."""
        try:
            values = [
                datetime.now().isoformat(),
                client_data.get('name', 'Unknown'),
                client_data.get('email', 'No email provided'),
                client_data.get('project_title', 'Untitled Project'),
                client_data.get('doc_link', 'No document')
            ]
            
            body = {
                'values': [values]
            }
            
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=os.getenv('GOOGLE_SHEET_ID'),
                range="Sheet1!A1",
                valueInputOption="RAW",
                body=body
            ).execute()
            
            return True
            
        except Exception as e:
            st.error(f"Error logging to Google Sheet: {str(e)}")
            return False

    def send_notification_email(self, client_data, doc_url):
        """Send email notification to the developer."""
        try:
            message = Mail(
                from_email=os.getenv('DEV_EMAIL'),
                to_emails=os.getenv('DEV_EMAIL'),
                subject=f"New Project Inquiry: {client_data.get('project_title', 'Untitled')}",
                html_content=f"""
                <h2>New Project Inquiry</h2>
                <p><strong>Client:</strong> {client_data.get('name', 'Unknown')}</p>
                <p><strong>Email:</strong> {client_data.get('email', 'No email provided')}</p>
                <p><strong>Project:</strong> {client_data.get('project_title', 'Untitled')}</p>
                <p><strong>Document:</strong> <a href='{doc_url}'>View Project Brief</a></p>
                <p><strong>Summary:</strong><br>{client_data.get('summary', 'No summary provided')}</p>
                """
            )
            
            response = self.sg.send(message)
            return response.status_code == 202
            
        except Exception as e:
            st.error(f"Error sending notification email: {str(e)}")
            return False

def main():
    # Initialize the PortAgent
    port_agent = PortAgent()
    
    # Page config
    st.set_page_config(
        page_title="PortAgent - Your Freelancing Assistant",
        page_icon="🤖",
        layout="centered"
    )
    
    # Custom CSS for better UI
    st.markdown("""
    <style>
        .stTextInput > div > div > input {
            border-radius: 20px;
            padding: 10px 15px;
        }
        .stButton > button {
            border-radius: 20px;
            padding: 0.5rem 1rem;
            background-color: #4CAF50;
            color: white;
            border: none;
        }
        .stButton > button:hover {
            background-color: #45a049;
        }
        .assistant-message {
            background-color: #f0f2f6;
            border-radius: 15px;
            padding: 10px 15px;
            margin: 5px 0;
            max-width: 80%;
            align-self: flex-start;
        }
        .user-message {
            background-color: #4CAF50;
            color: white;
            border-radius: 15px;
            padding: 10px 15px;
            margin: 5px 0;
            max-width: 80%;
            align-self: flex-end;
            margin-left: auto;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", 
             "content": "Hello! I'm your PortAgent. How can I assist you with your project today?"}
        ]
    
    if 'show_consent' not in st.session_state:
        st.session_state.show_consent = False
    
    # Display chat messages
    st.title("PortAgent 🤖")
    st.caption("Your AI-powered freelancing assistant")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                st.markdown(f'<div class="assistant-message"><strong>PortAgent:</strong> {message["content"]}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="user-message"><strong>You:</strong> {message["content"]}</div>', 
                           unsafe_allow_html=True)
    
    # User input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type your message here...", key="user_input", 
                                 placeholder="Tell me about your project")
        col1, col2 = st.columns([1, 4])
        
        with col1:
            submit_button = st.form_submit_button("Send")
        
        with col2:
            if st.form_submit_button("Save Conversation"):
                st.session_state.show_consent = True
    
    # Consent modal
    if st.session_state.show_consent:
        with st.expander("Save Conversation", expanded=True):
            st.write("To save this conversation, please provide the following details:")
            
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Your Name")
            with col2:
                email = st.text_input("Your Email")
            
            project_title = st.text_input("Project Title")
            
            if st.button("Save & Notify Developer"):
                if not name or not email or not project_title:
                    st.warning("Please fill in all required fields.")
                else:
                    # Create a document with the conversation
                    conversation = "\n\n".join(
                        f"{'You' if msg['role'] == 'user' else 'PortAgent'}: {msg['content']}" 
                        for msg in st.session_state.messages
                    )
                    
                    doc_title = f"{project_title} - {name} - {datetime.now().strftime('%Y-%m-%d')}"
                    doc_url = port_agent.create_google_doc(doc_title, conversation)
                    
                    if doc_url:
                        # Log to sheet
                        client_data = {
                            'name': name,
                            'email': email,
                            'project_title': project_title,
                            'doc_link': doc_url,
                            'summary': f"Project discussed: {project_title}"
                        }
                        
                        port_agent.log_to_sheet(client_data)
                        port_agent.send_notification_email(client_data, doc_url)
                        
                        st.success("Conversation saved! The developer will be in touch with you soon.")
                        st.session_state.show_consent = False
                    else:
                        st.error("Failed to save the conversation. Please try again later.")
    
    # Handle form submission
    if submit_button and user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get assistant response
        with st.spinner("PortAgent is thinking..."):
            assistant_response = port_agent.query_openrouter(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        
        # Rerun to update the UI
        st.rerun()

if __name__ == "__main__":
    # Check for required environment variables
    required_vars = [
        'OPENROUTER_API_KEY',
        'GOOGLE_APPLICATION_CREDENTIALS',
        'GOOGLE_DRIVE_FOLDER_ID',
        'GOOGLE_SHEET_ID',
        'SENDGRID_API_KEY',
        'DEV_EMAIL'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars and not os.path.exists('.env'):
        st.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        st.info("Please create a .env file with the required variables. See .env.example for reference.")
    else:
        main()
