
# =========================================================
# IMPORTS
# =========================================================

import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Support Operations Copilot",
    page_icon="🎧",
    layout="wide",
)


# =========================================================
# ENVIRONMENT CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

# Load local environment variables for development.
load_dotenv(BASE_DIR / ".env")

API_BASE_URL = os.getenv(
    "DJANGO_API_URL",
    "http://127.0.0.1:8000/api",
).strip().rstrip("/")

if not API_BASE_URL:
    raise RuntimeError(
        "DJANGO_API_URL must contain a valid API base URL."
    )

# =========================================================
# THEME AND CSS
# =========================================================


css_path = BASE_DIR / "style.css"

if css_path.exists():
    with open(css_path, encoding="utf-8") as css_file:
        st.markdown(
            f"<style>{css_file.read()}</style>",
            unsafe_allow_html=True,
        )

# Activate the permanent dark dashboard theme.
st.markdown(
    '<div id="night-theme-marker"></div>',
    unsafe_allow_html=True,
)
# =========================================================
# AUTHENTICATED API HELPER
# =========================================================

def api_request(method, endpoint, **kwargs):
    """Send requests using the logged-in user's token."""

    token = st.session_state.get("auth_token", "")

    if not token:
        raise RuntimeError("Please log in to continue.")

    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"

    headers = dict(kwargs.pop("headers", {}))
    headers["Authorization"] = f"Token {token}"

    timeout = kwargs.pop("timeout", 90)

    response = requests.request(
        method,
        url,
        headers=headers,
        timeout=timeout,
        **kwargs,
    )

    if response.status_code in (401, 403):
        raise RuntimeError(
            "Your session is no longer valid. Please log in again."
        )

    response.raise_for_status()
    return response


# =========================================================
# API FUNCTIONS
# =========================================================

def fetch_tickets():
    """Fetch tickets belonging to the authenticated user."""

    # Intentionally not cached: avoids sharing cached ticket
    # data between different Streamlit user sessions.
    response = api_request("GET", "tickets/")
    data = response.json()

    if isinstance(data, dict) and "results" in data:
        return data["results"]

    if isinstance(data, list):
        return data

    raise ValueError("Unexpected ticket API response format.")


def analyze_ticket_api(ticket_id):
    """Request AI analysis for a ticket."""

    response = api_request(
        "POST",
        f"tickets/{ticket_id}/analyze/",
    )

    return response.json()


def generate_customer_reply_api(ticket_id):
    """Generate a customer reply for a ticket."""

    response = api_request(
        "POST",
        f"tickets/{ticket_id}/generate-reply/",
    )

    return response.json()


def create_ticket_api(ticket_data):
    """Create a ticket for the authenticated user."""

    response = api_request(
        "POST",
        "tickets/",
        json=ticket_data,
        timeout=15,
    )

    return response.json()


def update_ticket_api(ticket_id, update_data):
    """Update an existing ticket."""

    response = api_request(
        "PATCH",
        f"tickets/{ticket_id}/",
        json=update_data,
        timeout=15,
    )

    return response.json()


# =========================================================
# API ERROR HANDLING
# =========================================================

def show_api_error(action, error):
    """Display API errors without exposing credentials."""

    if isinstance(error, RuntimeError):
        st.error(f"{action}: {error}")
        return

    response = getattr(error, "response", None)

    if response is not None:
        st.error(
            f"{action}. HTTP status: {response.status_code}."
        )

        try:
            error_data = response.json()

            if isinstance(error_data, dict):
                # Avoid displaying potentially sensitive server data.
                message = (
                    error_data.get("detail")
                    or error_data.get("error")
                    or "The request could not be completed."
                )
                st.write(message)
            else:
                st.write("The server returned an unexpected response.")

        except ValueError:
            st.write("The server returned an unreadable response.")

    else:
        st.error(
            f"{action}. Could not connect to the Django backend."
        )



# =========================================================
# LOGIN / REGISTRATION / LOGOUT
# =========================================================

def login_user(username, password):
    """Authenticate a user with the Django API."""

    response = requests.post(
        f"{API_BASE_URL}/auth/login/",
        json={
            "username": username,
            "password": password,
        },
        timeout=20,
    )

    if response.status_code == 401:
        raise ValueError("Incorrect username or password.")

    if response.status_code == 403:
        try:
            message = response.json().get(
                "error",
                "This account cannot sign in.",
            )
        except ValueError:
            message = "This account cannot sign in."

        raise ValueError(message)

    response.raise_for_status()
    data = response.json()

    if not data.get("token"):
        raise RuntimeError(
            "The login response did not include an API token."
        )

    return data


def register_user(username, email, password):
    """Register a new user through the Django API."""

    response = requests.post(
        f"{API_BASE_URL}/auth/register/",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
        timeout=20,
    )

    if response.status_code in (200, 201):
        return response.json()

    try:
        error_data = response.json()
        message = (
            error_data.get("error")
            or error_data.get("detail")
            or "Registration failed."
        )
    except ValueError:
        message = "Registration failed."

    raise ValueError(str(message))


def logout_user():
    """Revoke the current user's token before clearing local state."""

    token = st.session_state.get("auth_token", "")

    if not token:
        st.session_state.clear()
        st.rerun()

    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/logout/",
            headers={"Authorization": f"Token {token}"},
            timeout=15,
        )
        response.raise_for_status()

    except requests.RequestException:
        st.error(
            "Could not contact Django to revoke your token. "
            "Your local session has not been cleared. "
            "Please try again."
        )
        return

    # Clear only this Streamlit session after successful logout.
    st.session_state.clear()
    st.rerun()


# =========================================================
# LOGIN / REGISTER SCREEN
# =========================================================

if not st.session_state.get("auth_token"):

    st.markdown(
        """
        <div class="login-wrap">
            <div class="login-card">
                <div class="eyebrow">SUPPORTPILOT AI</div>
                <h1 style="margin-top:12px;">Welcome.</h1>
                <p>
                    Manage support tickets, analyze customer issues,
                    and draft AI-assisted responses.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 1.3, 1])

    with center:
        login_tab, register_tab = st.tabs(
            ["Sign in", "Create account"]
        )

        # -------------------------------------------------
        # SIGN IN
        # -------------------------------------------------

        with login_tab:
            with st.form("login_form"):
                username = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    key="login_username",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password",
                )

                login_submitted = st.form_submit_button(
                    "Sign in",
                    type="primary",
                    use_container_width=True,
                )

                if login_submitted:
                    if not username.strip() or not password:
                        st.error(
                            "Enter both your username and password."
                        )
                    else:
                        try:
                            with st.spinner("Signing you in..."):
                                login_data = login_user(
                                    username.strip(),
                                    password,
                                )

                            st.session_state["auth_token"] = (
                                login_data["token"]
                            )
                            st.session_state["auth_username"] = (
                                login_data.get(
                                    "username",
                                    username.strip(),
                                )
                            )

                            st.rerun()

                        except ValueError as error:
                            st.error(str(error))

                        except requests.RequestException:
                            st.error(
                                "Could not connect to Django. "
                                "Check that the backend is running."
                            )

                        except RuntimeError as error:
                            st.error(str(error))

        # -------------------------------------------------
        # REGISTER
        # -------------------------------------------------

        with register_tab:
            with st.form("register_form"):
                new_username = st.text_input(
                    "Username",
                    placeholder="Choose a username",
                    key="register_username",
                )

                email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                    key="register_email",
                )

                new_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Create a strong password",
                    key="register_password",
                )

                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                    placeholder="Enter the password again",
                    key="register_confirm_password",
                )

                register_submitted = st.form_submit_button(
                    "Create account",
                    type="primary",
                    use_container_width=True,
                )

                if register_submitted:
                    if not all([
                        new_username.strip(),
                        email.strip(),
                        new_password,
                        confirm_password,
                    ]):
                        st.error("Please fill in every field.")

                    elif new_password != confirm_password:
                        st.error("The passwords do not match.")

                    else:
                        try:
                            with st.spinner(
                                "Creating your account..."
                            ):
                                register_user(
                                    new_username.strip(),
                                    email.strip(),
                                    new_password,
                                )

                            st.success(
                                "Account created! Switch to Sign in "
                                "and log in with your new credentials."
                            )

                        except ValueError as error:
                            st.error(str(error))

                        except requests.RequestException:
                            st.error(
                                "Could not connect to Django. "
                                "Check that the backend is running."
                            )

    st.stop()



# =========================================================
# DASHBOARD SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("## 🎧 SupportPilot AI")
    st.caption("Support operations workspace")
    st.divider()

    st.markdown("**SIGNED IN AS**")
    st.write(st.session_state.get("auth_username", "User"))

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Manage tickets",
            "Create ticket",
            "AI analysis",
            "Customer replies",
        ],
        key="dashboard_page",
    )

    st.divider()

    if st.button("Log out", use_container_width=True):
        logout_user()


# =========================================================
# DASHBOARD HEADER
# =========================================================

st.markdown(
    """
    <div class="hero-card">
        <div class="eyebrow">CUSTOMER OPERATIONS</div>
        <div class="hero-title">
            Your support command center.
        </div>
        <div class="hero-copy">
            Track incoming issues, manage ticket priorities,
            and use AI to accelerate customer support.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

header_left, header_right = st.columns([4, 1])

with header_left:
    st.title(page)

with header_right:
    st.caption("● Authenticated session")

st.divider()


# =========================================================
# FETCH TICKETS
# =========================================================

try:
    tickets = fetch_tickets()
    api_connected = True

except (
    RuntimeError,
    requests.RequestException,
    ValueError,
) as error:
    tickets = []
    api_connected = False
    show_api_error("Could not load tickets", error)


# =========================================================
# METRICS
# =========================================================

total_tickets = len(tickets)

open_tickets = sum(
    ticket.get("status") == "open"
    for ticket in tickets
)

in_progress_tickets = sum(
    ticket.get("status") == "in_progress"
    for ticket in tickets
)

urgent_tickets = sum(
    ticket.get("priority") == "urgent"
    for ticket in tickets
)



# =========================================================
# OVERVIEW
# =========================================================

if page == "Overview":

    if api_connected:
        st.success("Backend connected")
    else:
        st.warning("Backend unavailable")

    st.subheader("Operations overview")

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric("Total tickets", total_tickets)
    metric2.metric("Open tickets", open_tickets)
    metric3.metric("In progress", in_progress_tickets)
    metric4.metric("Urgent", urgent_tickets)

    st.divider()
    st.subheader("Recent support tickets")

    if tickets:
        sorted_tickets = sorted(
            tickets,
            key=lambda ticket: ticket.get("created_at", ""),
            reverse=True,
        )

        for ticket in sorted_tickets[:10]:
            with st.container(border=True):
                left, right = st.columns([4, 1])

                with left:
                    st.markdown(
                        f"**#{ticket.get('id')} · "
                        f"{ticket.get('subject', 'Untitled ticket')}**"
                    )

                    st.write(
                        ticket.get(
                            "description",
                            "No description provided.",
                        )
                    )

                    st.caption(
                        f"Status: "
                        f"{ticket.get('status', 'N/A').replace('_', ' ').title()} "
                        f"· Priority: "
                        f"{ticket.get('priority', 'N/A').title()} "
                        f"· Category: "
                        f"{ticket.get('category', 'N/A').title()}"
                    )

                with right:
                    st.caption("CUSTOMER")
                    st.write(ticket.get("customer_name", "Unknown"))
                    st.caption(ticket.get("customer_email", ""))

    else:
        st.info("No tickets found. Create your first support ticket.")



# =========================================================
# TICKET MANAGEMENT
# =========================================================

elif page == "Manage tickets":
    st.subheader("Update ticket status and priority")

    if not tickets:
        st.info("No tickets available to manage.")

    else:
        management_options = {
            (
                f"#{ticket.get('id')} · "
                f"{ticket.get('subject', 'Untitled ticket')}"
            ): ticket
            for ticket in tickets
        }

        selected_label = st.selectbox(
            "Select a ticket",
            options=list(management_options.keys()),
            key="management_ticket_selector",
        )

        selected_ticket = management_options[selected_label]
        ticket_id = selected_ticket["id"]

        status_options = [
            "open",
            "in_progress",
            "resolved",
            "closed",
        ]

        priority_options = [
            "low",
            "medium",
            "high",
            "urgent",
        ]

        with st.container(border=True):
            st.markdown(f"### Ticket #{ticket_id}")
            st.write(selected_ticket.get("description", ""))

            with st.form("update_ticket_form"):
                current_status = selected_ticket.get("status", "open")
                current_priority = selected_ticket.get(
                    "priority",
                    "medium",
                )

                new_status = st.selectbox(
                    "Status",
                    status_options,
                    index=(
                        status_options.index(current_status)
                        if current_status in status_options
                        else 0
                    ),
                    format_func=lambda value: value.replace(
                        "_", " "
                    ).title(),
                )

                new_priority = st.selectbox(
                    "Priority",
                    priority_options,
                    index=(
                        priority_options.index(current_priority)
                        if current_priority in priority_options
                        else 1
                    ),
                    format_func=str.title,
                )

                save_changes = st.form_submit_button(
                    "Save changes",
                    type="primary",
                )

                if save_changes:
                    try:
                        update_ticket_api(
                            ticket_id,
                            {
                                "status": new_status,
                                "priority": new_priority,
                            },
                        )

                        st.success(
                            f"Ticket #{ticket_id} updated successfully."
                        )
                        st.rerun()

                    except (
                        RuntimeError,
                        requests.RequestException,
                    ) as error:
                        show_api_error(
                            "Could not update ticket",
                            error,
                        )


# =========================================================
# CREATE SUPPORT TICKET
# =========================================================

elif page == "Create ticket":
    st.subheader("Create a support ticket")
    st.caption(
        "Capture the customer's issue so your team can investigate it."
    )

    with st.container(border=True):
        with st.form("create_ticket_form"):
            customer_name = st.text_input(
                "Customer name",
                placeholder="Enter customer name",
            )

            customer_email = st.text_input(
                "Customer email",
                placeholder="customer@example.com",
            )

            subject = st.text_input(
                "Subject",
                placeholder="Briefly describe the issue",
            )

            description = st.text_area(
                "Issue description",
                placeholder="Explain the customer's problem...",
                height=140,
            )

            col1, col2 = st.columns(2)

            with col1:
                category = st.selectbox(
                    "Category",
                    ["technical", "billing", "account", "general"],
                )

            with col2:
                priority = st.selectbox(
                    "Priority",
                    ["low", "medium", "high", "urgent"],
                )

            submitted = st.form_submit_button(
                "Create ticket",
                type="primary",
                use_container_width=True,
            )

            if submitted:
                if not all(
                    value.strip()
                    for value in [
                        customer_name,
                        customer_email,
                        subject,
                        description,
                    ]
                ):
                    st.error("Please complete all fields.")

                elif (
                    "@" not in customer_email
                    or "." not in customer_email.rsplit("@", 1)[-1]
                ):
                    st.error("Please enter a valid email address.")

                else:
                    ticket_data = {
                        "customer_name": customer_name.strip(),
                        "customer_email": customer_email.strip(),
                        "subject": subject.strip(),
                        "description": description.strip(),
                        "category": category,
                        "priority": priority,
                        "status": "open",
                    }

                    try:
                        created_ticket = create_ticket_api(ticket_data)

                        # Clear results that may refer to old ticket data.
                        for key in [
                            "latest_analysis",
                            "latest_analysis_ticket_id",
                            "customer_reply_draft",
                            "customer_reply_ticket_id",
                        ]:
                            st.session_state.pop(key, None)

                        st.success(
                            f"Ticket #{created_ticket['id']} created."
                        )
                        st.rerun()

                    except (
                        RuntimeError,
                        requests.RequestException,
                        ValueError,
                    ) as error:
                        show_api_error(
                            "Could not create ticket",
                            error,
                        )



# =========================================================
# AI TICKET ANALYSIS
# =========================================================

elif page == "AI analysis":
    st.subheader("AI ticket analysis")
    st.caption(
        "Use AI to summarize an issue and identify a recommended action."
    )

    if not tickets:
        st.info("Create a ticket before running AI analysis.")

    else:
        analysis_options = {
            (
                f"#{ticket.get('id')} · "
                f"{ticket.get('subject', 'Untitled ticket')}"
            ): ticket.get("id")
            for ticket in tickets
        }

        selected_label = st.selectbox(
            "Select a ticket to analyze",
            options=list(analysis_options.keys()),
            key="analysis_ticket_selector",
        )

        selected_id = analysis_options[selected_label]

        if st.button(
            "Analyze ticket",
            type="primary",
            key="analyze_ticket_button",
        ):
            try:
                with st.spinner(
                    "Analyzing ticket with AI and knowledge base..."
                ):
                    analysis = analyze_ticket_api(selected_id)

                st.session_state["latest_analysis"] = analysis
                st.session_state["latest_analysis_ticket_id"] = (
                    selected_id
                )

            except (
                RuntimeError,
                requests.RequestException,
                ValueError,
            ) as error:
                show_api_error("Ticket analysis failed", error)

        analysis = st.session_state.get("latest_analysis")
        analysis_id = st.session_state.get(
            "latest_analysis_ticket_id"
        )

        if analysis and analysis_id == selected_id:
            st.divider()
            st.markdown("### Analysis results")

            col1, col2 = st.columns(2)

            col1.metric(
                "Category",
                str(analysis.get("category", "N/A")).title(),
            )

            col2.metric(
                "Priority",
                str(analysis.get("priority", "N/A")).title(),
            )

            with st.container(border=True):
                st.markdown("**Summary**")
                st.write(
                    analysis.get("summary", "No summary available.")
                )

                st.markdown("**Customer issue**")
                st.write(
                    analysis.get(
                        "customer_issue",
                        "No issue description available.",
                    )
                )

                st.markdown("**Recommended action**")
                st.write(
                    analysis.get(
                        "recommended_action",
                        "No recommendation available.",
                    )
                )


# =========================================================
# AI CUSTOMER REPLY GENERATOR
# =========================================================

elif page == "Customer replies":
    st.subheader("AI customer reply generator")
    st.caption(
        "Generate a suggested response and review it before sending."
    )

    if not tickets:
        st.info("Create a ticket before generating a reply.")

    else:
        reply_options = {
            (
                f"#{ticket.get('id')} · "
                f"{ticket.get('subject', 'Untitled ticket')}"
            ): ticket.get("id")
            for ticket in tickets
        }

        selected_label = st.selectbox(
            "Choose a ticket",
            options=list(reply_options.keys()),
            key="reply_ticket_selector",
        )

        selected_id = reply_options[selected_label]

        if st.button(
            "Generate customer reply",
            type="primary",
            key="generate_customer_reply_button",
        ):
            try:
                with st.spinner("Drafting customer reply..."):
                    reply_data = generate_customer_reply_api(
                        selected_id
                    )

                if "customer_reply" not in reply_data:
                    st.error(
                        "The API response did not contain a customer reply."
                    )
                else:
                    st.session_state["customer_reply_draft"] = (
                        reply_data["customer_reply"]
                    )

                    st.session_state["customer_reply_ticket_id"] = (
                        selected_id
                    )

            except (
                RuntimeError,
                requests.RequestException,
                ValueError,
            ) as error:
                show_api_error("Reply generation failed", error)

        draft = st.session_state.get("customer_reply_draft")
        draft_ticket_id = st.session_state.get(
            "customer_reply_ticket_id"
        )

        if draft and draft_ticket_id == selected_id:
            st.divider()
            st.markdown("### Review customer reply")

            st.info(
                "This is a draft only. Review it before sending "
                "it to the customer."
            )

            edited_reply = st.text_area(
                "Draft response",
                value=draft,
                height=220,
                key=f"edited_reply_{selected_id}",
            )

            st.download_button(
                "Download reply as text",
                data=edited_reply,
                file_name=f"customer_reply_ticket_{selected_id}.txt",
                mime="text/plain",
                key="download_customer_reply",
            )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Support Operations Copilot · "
    "Django REST Framework · Groq · ChromaDB"
)
