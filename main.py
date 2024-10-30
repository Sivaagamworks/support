import streamlit as st
from pymongo import MongoClient
import bcrypt
import datetime
import streamlit_authenticator as stauth

# MongoDB connection
client = MongoClient("mongodb+srv://support:ODoP9ciMjdJTRbqC@siva.gjvsd82.mongodb.net/?retryWrites=true&w=majority&appName=siva")
db = client["supportticket"]
tickets_collection = db["tickets"]
users_collection = db["users"]

# Utility functions
def create_ticket(client_name, client_email, issue_summary, description):
    ticket = {
        "client_name": client_name,
        "client_email": client_email,
        "issue_summary": issue_summary,
        "description": description,
        "status": "Open",
        "created_at": datetime.datetime.now(),
        "comments": []
    }
    tickets_collection.insert_one(ticket)
    st.success("Ticket submitted successfully!")

def authenticate_user(username, password):
    user = users_collection.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        return user
    return None

# Authentication setup for support team
def setup_authenticator():
    users = users_collection.find()
    usernames = [user["username"] for user in users]
    hashed_passwords = [user["password"] for user in users]
    names = ["Support User" for _ in users]  # Placeholder names
    authenticator = stauth.Authenticate(
        names,
        usernames,
        hashed_passwords,
        "support_auth",
        "secret_key",
    )
    return authenticator

# App sections
st.title("Support Ticket System")

# Client Section - No authentication
st.header("Submit a Support Ticket (Client)")
with st.form("ticket_form"):
    client_name = st.text_input("Name")
    client_email = st.text_input("Email")
    issue_summary = st.text_input("Issue Summary")
    description = st.text_area("Description")
    submitted = st.form_submit_button("Submit Ticket")

    if submitted:
        create_ticket(client_name, client_email, issue_summary, description)

# Receiver Section - Authenticated view with RBAC
st.header("Support Dashboard (Support Team)")

authenticator = setup_authenticator()
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.sidebar.write(f"Welcome, {name}!")

    user = users_collection.find_one({"username": username})
    if user["role"] == "admin" or user["role"] == "support":
        st.write("Ticket Dashboard")

        # Display tickets
        tickets = tickets_collection.find()
        for ticket in tickets:
            st.subheader(f"Issue Summary: {ticket['issue_summary']}")
            st.write(f"Description: {ticket['description']}")
            st.write(f"Status: {ticket['status']}")
            st.write(f"Submitted by: {ticket['client_name']} ({ticket['client_email']})")
            st.write("Comments:")
            for comment in ticket["comments"]:
                st.write(f"- {comment['by']}: {comment['comment']} ({comment['timestamp']})")

            # Update ticket status
            if st.button("Mark as Resolved", key=ticket["_id"]):
                tickets_collection.update_one(
                    {"_id": ticket["_id"]}, {"$set": {"status": "Resolved"}}
                )
                st.success("Ticket marked as resolved.")

else:
    st.error("Invalid credentials or unauthorized access.")

authenticator.logout("Logout", "sidebar")