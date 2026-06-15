import streamlit as st
from database import login_user, register_user

def show_login_page():
    st.markdown("""
    <div style="max-width:420px;margin:60px auto 0 auto">
        <div style="text-align:center;margin-bottom:32px">
            <div style="font-size:48px">🎯</div>
            <h1 style="font-size:26px;font-weight:700;margin:8px 0 4px">Interview Coach AI</h1>
            <p style="color:#6b7280;font-size:14px">Practice. Improve. Get hired.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["Login", "Create account"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    user = login_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.success(f"Welcome back, {user['username']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        with tab_register:
            with st.form("register_form"):
                new_username = st.text_input("Username")
                new_email    = st.text_input("Email (optional)")
                new_password = st.text_input("Password", type="password")
                confirm_pw   = st.text_input("Confirm password", type="password")
                submitted2   = st.form_submit_button("Create account", use_container_width=True)

            if submitted2:
                if not new_username or not new_password:
                    st.error("Username and password are required.")
                elif new_password != confirm_pw:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(new_username, new_email, new_password)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

def logout():
    st.session_state.user = None
    st.rerun()