# app.py
import streamlit as st
import json
import hashlib
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Network Anomaly Dashboard", layout="wide")

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as file:
        return json.load(file)

def save_users(users):
    with open(USERS_FILE, "w") as file:
        json.dump(users, file, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username, password):
    users = load_users()
    if username in users:
        hashed_pw = hash_password(password)
        return users[username]["password"] == hashed_pw, users[username]["role"]
    return False, None

def create_account(username, password, role):
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "password": hash_password(password),
        "role": role
    }
    save_users(users)
    return True

def login_page():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        valid, role = check_credentials(username, password)
        if valid:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_role = role
            st.session_state.page = "MainMenu"
            st.session_state.selected_menu = "Dashboard"
            st.rerun()
        else:
            st.error("Invalid credentials")
    if st.button("Go to Create Account"):
        st.session_state.page = "Signup"
        st.rerun()

def signup_page():
    st.title("📝 Create Account")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    role = st.selectbox("Select Role", ["Engineer", "Manager"])
    if st.button("Create Account"):
        success = create_account(username, password, role)
        if success:
            st.success("Account created successfully! Please login.")
            st.session_state.page = "Login"
            st.rerun()
        else:
            st.error("Username already exists. Try a different one.")
    if st.button("Go to Login"):
        st.session_state.page = "Login"
        st.rerun()

def main():
    # Initialize session state
    for key, default in {
        "logged_in": False,
        "username": "",
        "user_role": "",
        "page": "Login",
        "selected_menu": "Dashboard"
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    st.sidebar.title("Navigation")

    if st.session_state.logged_in:
        st.sidebar.write(f"👤 User: {st.session_state.username}")
        st.sidebar.write(f"🛡️ Role: {st.session_state.user_role}")

        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_role = ""
            st.session_state.page = "Login"
            st.session_state.selected_menu = "Dashboard"
            st.rerun()

        # Role-based menu
        if st.session_state.user_role == "Engineer":
            menu_options = ["Dashboard", "Model Page"]
        elif st.session_state.user_role == "Manager":
            menu_options = ["Dashboard"]

        selected = st.sidebar.radio("📂 Go to Page", menu_options, index=menu_options.index(st.session_state.selected_menu))
        st.session_state.selected_menu = selected

        # Conditional page rendering
        if selected == "Dashboard":
            from dashboard import show_dashboard
            show_dashboard()
        elif selected == "Model Page":
            from model_page import show_model_page
            show_model_page()

    else:
        if st.session_state.page == "Login":
            login_page()
        elif st.session_state.page == "Signup":
            signup_page()

if __name__ == "__main__":
    main()
