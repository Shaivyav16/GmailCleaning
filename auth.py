import streamlit as st
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.settings.basic'
]

def get_gmail_service():
    creds = None
    
    # 1. Check if we already have a token in the current session
    if 'google_creds' in st.session_state:
        creds = st.session_state.google_creds

    # 2. If not in session, check if it's in Streamlit Secrets (for your own account)
    elif "gmail_token" in st.secrets:
        token_info = json.loads(st.secrets["gmail_token"])
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    # 3. Handle Refreshing
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        st.session_state.google_creds = creds

    # 4. START THE WEB OAUTH FLOW (If no creds)
    if not creds or not creds.valid:
        # Load the client config from secrets
        client_config = st.secrets["google_oauth"]
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=client_config["web"]["redirect_uris"][0]
        )

        # Check if Google sent back an authorization code in the URL
        code = st.query_params.get("code")
        
        if not code:
            # Step A: Generate the login URL and show a button
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            st.info("To use this app, please authorize access to your Gmail.")
            st.link_button("🔗 Sign in with Google", auth_url, use_container_width=True)
            st.stop()
        else:
            # Step B: Exchange the code for a token
            try:
                flow.fetch_token(code=code)
                creds = flow.credentials
                st.session_state.google_creds = creds
                # Clear the URL parameters so the code doesn't stay in the address bar
                st.query_params.clear()
            except Exception as e:
                st.error(f"Auth Error: {e}")
                st.stop()

    return build('gmail', 'v1', credentials=creds)
