
from pathlib import Path
import os

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

BASE_DIR = Path(__file__).parent

load_dotenv(BASE_DIR / ".env")

API_BASE_URL = os.getenv(
    "DJANGO_API_URL",
    "http://127.0.0.1:8000/api",
).strip().rstrip("/")

API_TOKEN = os.getenv("DJANGO_API_TOKEN", "").strip()


API_HEADERS = (
    {"Authorization": f"Token {API_TOKEN}"}
    if API_TOKEN
    else {}
)


# =========================================================
# THEME STATE AND CSS
# =========================================================

if "night_mode" not in st.session_state:
    st.session_state["night_mode"] = False

css_path = BASE_DIR / "style.css"

with open(css_path, encoding="utf-8") as css_file:
    st.markdown(
        f"<style>{css_file.read()}</style>",
        unsafe_allow_html=True,
    )

if st.session_state["night_mode"]:
    st.markdown(
        '<span id="night-theme-marker"></span>',
        unsafe_allow_html=True,
    )


# =========================================================
# AUTHENTICATED API HELPER
# =========================================================

def api_request(method, endpoint, **kwargs):
    """Send an authenticated request to the Django REST API."""

    if not API_TOKEN:
        raise RuntimeError(
            "DJANGO_API_TOKEN is missing from the root .env file."
        )

    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"

    headers = dict(kwargs.pop("headers", {}))
    headers.update(API_HEADERS)

    # Remove timeout from kwargs to avoid passing it twice.
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
            "Authentication failed. Check the API token "
            "and Django permissions."
        )

    response.raise_for_status()
    return response


# =========================================================
# API FUNCTIONS
# =========================================================

@st.cache_data(ttl=10)
def fetch_tickets():
    response = api_request("GET", "tickets/")
    data = response.json()

    if isinstance(data, dict) and "results" in data:
        return data["results"]

    if isinstance(data, list):
        return data

    raise ValueError("Unexpected ticket API response format.")


def analyze_ticket_api(ticket_id):
    response = api_request(
        "POST",
        f"tickets/{ticket_id}/analyze/",
    )
    return response.json()


def generate_customer_reply_api(ticket_id):
    response = api_request(
        "POST",
        f"tickets/{ticket_id}/generate-reply/",
    )
    return response.json()


def create_ticket_api(ticket_data):
    response = api_request(
        "POST",
        "tickets/",
        json=ticket_data,
        timeout=15,
    )
    return response.json()


def update_ticket_api(ticket_id, update_data):
    response = api_request(
        "PATCH",
        f"tickets/{ticket_id}/",
        json=update_data,
        timeout=15,
    )
    return response.json()


def show_api_error(action, error):
    """Display API errors without revealing credentials."""

    if isinstance(error, RuntimeError):
        st.error(f"{action}: {error}")
        return

    response = getattr(error, "response", None)

    if response is not None:
        st.error(
            f"{action}. HTTP status: {response.status_code}."
        )

        try:
            st.write(response.json())
        except ValueError:
            st.write("The server returned an unreadable response.")
    else:
        st.error(f"{action}. Could not connect to Django.")


# =========================================================
# HEADER AND THEME SWITCH
# =========================================================

header_left, header_right = st.columns([5, 1])

with header_left:
    st.title("🎧 Support Operations Copilot")
    st.caption(
        "Customer support workspace · AI-assisted operations"
    )

with header_right:
    st.toggle(
        "Night mode",
        key="night_mode",
        help="Switch between light and night themes.",
    )

# Render the marker after the toggle so the CSS can detect it.
if st.session_state["night_mode"]:
    st.markdown(
        '<span id="night-theme-marker"></span>',
        unsafe_allow_html=True,
    )

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


if api_connected:
    st.success("Backend connected · Authenticated")
else:
    st.warning("Backend unavailable or authentication failed")


# =========================================================
# OPERATIONS OVERVIEW
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

st.subheader("Operations overview")

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric("Total tickets", total_tickets)
metric2.metric("Open tickets", open_tickets)
metric3.metric("In progress", in_progress_tickets)
metric4.metric("Urgent", urgent_tickets)

st.divider()


# =========================================================
# RECENT SUPPORT TICKETS
# =========================================================

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

                status_label = (
                    ticket.get("status", "N/A")
                    .replace("_", " ")
                    .title()
                )

                st.caption(
                    f"Category: {ticket.get('category', 'N/A')} · "
                    f"Priority: {ticket.get('priority', 'N/A')} · "
                    f"Status: {status_label}"
                )

            with right:
                st.caption("CUSTOMER")
                st.write(ticket.get("customer_name", "Unknown"))
                st.caption(ticket.get("customer_email", ""))

else:
    st.info("No tickets found. Create a support ticket below.")


# =========================================================
# TICKET MANAGEMENT
# =========================================================

st.divider()
st.subheader("Ticket management")

if tickets:
    management_options = {
        (
            f"#{ticket.get('id')} · "
            f"{ticket.get('subject', 'Untitled ticket')}"
        ): ticket
        for ticket in tickets
    }

    selected_management_label = st.selectbox(
        "Select a ticket to update",
        options=list(management_options.keys()),
        key="management_ticket_selector",
    )

    selected_ticket = management_options[
        selected_management_label
    ]

    management_ticket_id = selected_ticket["id"]

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

    current_status = selected_ticket.get("status", "open")
    current_priority = selected_ticket.get("priority", "medium")

    with st.form("update_ticket_form"):
        new_status = st.selectbox(
            "Status",
            options=status_options,
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
            options=priority_options,
            index=(
                priority_options.index(current_priority)
                if current_priority in priority_options
                else 1
            ),
            format_func=str.title,
        )

        update_submitted = st.form_submit_button(
            "Save changes",
            type="primary",
        )

        if update_submitted:
            try:
                update_ticket_api(
                    management_ticket_id,
                    {
                        "status": new_status,
                        "priority": new_priority,
                    },
                )

                fetch_tickets.clear()
                st.success(
                    f"Ticket #{management_ticket_id} updated."
                )
                st.rerun()

            except (
                RuntimeError,
                requests.RequestException,
            ) as error:
                show_api_error("Could not update ticket", error)

else:
    st.info("Create a ticket before managing tickets.")


# =========================================================
# CREATE SUPPORT TICKET
# =========================================================

st.divider()
st.subheader("Create support ticket")

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
        height=130,
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

                fetch_tickets.clear()

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
            ) as error:
                show_api_error("Could not create ticket", error)


# =========================================================
# AI TICKET ANALYSIS
# =========================================================

st.divider()
st.subheader("AI ticket analysis")

if tickets:
    analysis_options = {
        (
            f"#{ticket.get('id')} · "
            f"{ticket.get('subject', 'Untitled ticket')}"
        ): ticket.get("id")
        for ticket in tickets
    }

    selected_analysis_label = st.selectbox(
        "Select a ticket to analyze",
        options=list(analysis_options.keys()),
        key="analysis_ticket_selector",
    )

    selected_analysis_id = analysis_options[
        selected_analysis_label
    ]

    if st.button(
        "Analyze ticket",
        type="primary",
        key="analyze_ticket_button",
    ):
        try:
            with st.spinner(
                "Analyzing ticket with AI and knowledge base..."
            ):
                analysis = analyze_ticket_api(
                    selected_analysis_id
                )

            st.session_state["latest_analysis"] = analysis
            st.session_state["latest_analysis_ticket_id"] = (
                selected_analysis_id
            )

        except (
            RuntimeError,
            requests.RequestException,
        ) as error:
            show_api_error("Ticket analysis failed", error)

    analysis = st.session_state.get("latest_analysis")
    analysis_id = st.session_state.get(
        "latest_analysis_ticket_id"
    )

    if analysis and analysis_id == selected_analysis_id:
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

        st.markdown("**Summary**")
        st.write(analysis.get("summary", "No summary available."))

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

else:
    st.info("Create a ticket before running AI analysis.")


# =========================================================
# AI CUSTOMER REPLY GENERATOR
# =========================================================

st.divider()
st.subheader("AI customer reply generator")

st.caption(
    "Generate a suggested customer response using ticket details "
    "and relevant knowledge-base guidance."
)

if tickets:
    reply_options = {
        (
            f"#{ticket.get('id')} · "
            f"{ticket.get('subject', 'Untitled ticket')}"
        ): ticket.get("id")
        for ticket in tickets
    }

    selected_reply_label = st.selectbox(
        "Choose a ticket for the reply",
        options=list(reply_options.keys()),
        key="reply_ticket_selector",
    )

    selected_reply_id = reply_options[selected_reply_label]

    if st.button(
        "Generate customer reply",
        type="primary",
        key="generate_customer_reply_button",
    ):
        try:
            with st.spinner("Drafting customer reply..."):
                reply_data = generate_customer_reply_api(
                    selected_reply_id
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
                    selected_reply_id
                )

        except (
            RuntimeError,
            requests.RequestException,
        ) as error:
            show_api_error("Reply generation failed", error)

    draft = st.session_state.get("customer_reply_draft")
    draft_ticket_id = st.session_state.get(
        "customer_reply_ticket_id"
    )

    if draft and draft_ticket_id == selected_reply_id:
        st.markdown("### Review customer reply")

        st.info(
            "Review and edit this draft before using it. "
            "It has not been sent to the customer."
        )

        edited_reply = st.text_area(
            "Draft response",
            value=draft,
            height=220,
            key=f"edited_reply_{selected_reply_id}",
        )

        st.download_button(
            "Download reply as text",
            data=edited_reply,
            file_name=(
                f"customer_reply_ticket_{selected_reply_id}.txt"
            ),
            mime="text/plain",
            key="download_customer_reply",
        )

else:
    st.info("Create a ticket before generating a customer reply.")


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Support Operations Copilot · "
    "Django REST Framework · Groq · ChromaDB"
)
