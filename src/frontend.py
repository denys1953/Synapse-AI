import streamlit as st
import httpx
from typing import List, Dict, Any
from pathlib import Path
import json
import os

BASE_URL = "http://fastapi:8000"  # Correct URL inside Docker network
# BASE_URL = "http://localhost:8001"  # Only for local testing

st.set_page_config(page_title="SynapseAI", layout="wide")

# Session state defaults (canonical keys)
if "auth_token" not in st.session_state:
    # migrate from older key `token` if present
    st.session_state.auth_token = st.session_state.get("token")
if "messages" not in st.session_state:
    st.session_state.messages = st.session_state.get("chat_history") or []
if "current_notebook_id" not in st.session_state:
    st.session_state.current_notebook_id = st.session_state.get("notebook_id")
if "last_loaded_id" not in st.session_state:
    st.session_state.last_loaded_id = None
if "notebooks" not in st.session_state:
    st.session_state.notebooks = []


def safe_rerun():
    try:
        # try experimental API first
        st.experimental_rerun()
    except Exception:
        try:
            # fallback to stable rerun
            st.rerun()
        except Exception:
            # if neither available, no-op
            pass


# Token persistence (store token in a file inside container user's home)
TOKEN_FILE = os.environ.get("SYNAPSE_TOKEN_FILE") or str(Path.home() / ".synapseai_token")


def save_token(token: str) -> None:
    try:
        Path(TOKEN_FILE).write_text(json.dumps({"access_token": token}))
    except Exception:
        pass


def load_token_from_file() -> str | None:
    try:
        p = Path(TOKEN_FILE)
        if p.exists():
            data = json.loads(p.read_text())
            return data.get("access_token")
    except Exception:
        return None
    return None


def delete_token_file() -> None:
    try:
        p = Path(TOKEN_FILE)
        if p.exists():
            p.unlink()
    except Exception:
        pass


def auth_headers() -> Dict[str, str]:
    if st.session_state.auth_token:
        return {"Authorization": f"Bearer {st.session_state.auth_token}"}
    return {}


# --- API client helpers ---
def api_get_notebooks() -> List[Dict[str, Any]]:
    try:
        resp = httpx.get(f"{BASE_URL}/notebooks/", headers=auth_headers(), timeout=15)
        if resp.status_code == 200:
            return resp.json() or []
        st.error(f"Notebooks error: {resp.status_code}")
    except Exception as e:
        st.error(f"Connection error (list): {e}")
    return []


def api_get_sources(notebook_id: int) -> List[Dict[str, Any]]:
    try:
        resp = httpx.get(f"{BASE_URL}/notebooks/{notebook_id}/sources", headers=auth_headers(), timeout=15)
        if resp.status_code == 200:
            return resp.json() or []
    except Exception:
        pass
    return []


def api_get_chat_history(notebook_id: int) -> List[Dict[str, Any]]:
    try:
        resp = httpx.get(f"{BASE_URL}/notebooks/{notebook_id}/chat_history", headers=auth_headers(), timeout=15)
        if resp.status_code == 200:
            # Backend usually returns newest first, we want chronological
            history = resp.json() or []
            return history[::-1]
    except Exception:
        pass
    return []


def api_create_notebook(title: str) -> Dict[str, Any]:
    try:
        resp = httpx.post(
            f"{BASE_URL}/notebooks/add",
            headers=auth_headers(),
            params={"title": title},
            timeout=15,
        )
        if resp.status_code in (200, 201):
            return resp.json() or {}
        st.error(f"Create error: {resp.status_code}")
    except Exception as e:
        st.error(f"Connection error (create): {e}")
    return {}


def api_login(username: str, password: str) -> Dict[str, Any]:
    try:
        resp = httpx.post(f"{BASE_URL}/auth/login", data={"username": username, "password": password}, timeout=15)
        if resp.status_code == 200:
            return resp.json() or ({} if resp.status_code != 200 else None) # type: ignore
        st.error(f"Login failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        st.error(f"Connection error (login): {e}. URL: {BASE_URL}")
    return {}


def api_register(username: str, password: str) -> Dict[str, Any]:
    try:
        resp = httpx.post(f"{BASE_URL}/auth/register", json={"email": username, "password": password}, timeout=15)
        if resp.status_code in (200, 201):
            return resp.json() or {}
        st.error(f"Register failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        st.error(f"Connection error (register): {e}")
    return {}


def login():
    # load token from file once
    if not st.session_state.auth_token:
        token = load_token_from_file()
        if token:
            st.session_state.auth_token = token
            load_notebooks()

    with st.sidebar:
        st.title("🔐 Authentication")
        
        if not st.session_state.auth_token:
            mode = st.radio("Action", ["Login", "Register"], index=0, key="_auth_mode")
            email = st.text_input("Email", key="_login_email")
            password = st.text_input("Password", type="password", key="_login_password")

            if mode == "Login":
                if st.button("Login"):
                    body = api_login(email, password)
                    token = body.get("access_token")
                    if token:
                        st.session_state.auth_token = token
                        save_token(token)
                        st.success("Logged in!")
                        load_notebooks()
                        safe_rerun()
                    else:
                        st.error("Login failed. Check credentials.")
            else:
                if st.button("Register"):
                    body = api_register(email, password)
                    token = body.get("access_token") if isinstance(body, dict) else None
                    if token:
                        st.session_state.auth_token = token
                        save_token(token)
                        st.success("Registered and logged in!")
                        load_notebooks()
                        safe_rerun()
                    elif body:
                        st.success("Registered — please log in.")
                    else:
                        st.error("Registration failed.")
        else:
            st.success("✅ Authenticated")
            if st.button("Logout"):
                for k in ("auth_token", "messages", "current_notebook_id", "notebooks"):
                    if k in st.session_state:
                        del st.session_state[k]
                delete_token_file()
                safe_rerun()
        
        st.markdown("---")


def load_notebooks():
    if not st.session_state.auth_token:
        return
    notebooks = api_get_notebooks()
    st.session_state.notebooks = notebooks or []


def upload_section(notebook_id: Any):
    st.subheader("📁 Upload Sources")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file and st.button("Upload"):
        if not st.session_state.auth_token:
            st.warning("Please log in first.")
            return
        if not notebook_id:
            st.warning("Please select a notebook.")
            return

        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        try:
            resp = httpx.post(
                f"{BASE_URL}/notebooks/source/{notebook_id}/upload",
                headers=auth_headers(),
                files=files,
                timeout=60,
            )
        except Exception as e:
            st.error(f"Upload failed: {e}")
            return

        if resp.status_code == 200:
            st.success("File indexed!")
        else:
            st.error(f"Upload failed: {resp.status_code} - {resp.text}")


def chat_interface(notebook_id: Any):
    col_chat, col_sources = st.columns([0.7, 0.3])

    with col_sources:
        st.subheader("📚 Sources")
        sources = api_get_sources(notebook_id)
        selected_source_ids = []
        if sources:
            source_options = {s["id"]: s["title"] for s in sources}
            st.info("Select sources to focus the search (leave empty for all):")
            selected_source_ids = st.multiselect(
                "Active sources",
                options=list(source_options.keys()),
                format_func=lambda x: source_options[x],
                key=f"source_sel_{notebook_id}"
            )
        else:
            st.write("No sources indexed yet.")

    with col_chat:
        st.divider()
        st.subheader("💬 Chat")

        # Container for chat history to keep it above the input
        chat_container = st.container()

        # New prompt at the bottom
        prompt = st.chat_input("Ask something about your docs...")

        with chat_container:
            # Display history
            for msg in st.session_state.messages:
                role = "user" if msg.get("role") in ("human", "user") else "assistant"
                with st.chat_message(role):
                    st.write(msg.get("content"))

            if prompt:
                st.session_state.messages.append({"role": "human", "content": prompt})
                with st.chat_message("user"):
                    st.write(prompt)

                if not st.session_state.auth_token:
                    st.warning("Please log in to ask questions.")
                else:
                    payload = {
                        "question": prompt, 
                        "mode": "mmr",
                        "source_ids": selected_source_ids if selected_source_ids else None
                    }
                    with st.spinner("Thinking..."):
                        try:
                            resp = httpx.post(
                                f"{BASE_URL}/notebooks/notebook/{notebook_id}/ask",
                                headers=auth_headers(),
                                json=payload,
                                timeout=60,
                            )
                            if resp.status_code == 200:
                                answer = resp.json().get("answer")
                                st.session_state.messages.append({"role": "ai", "content": answer})
                                safe_rerun()
                            else:
                                st.error(f"Ask failed: {resp.status_code} - {resp.text}")
                        except Exception as e:
                            st.error(f"Request failed: {e}")


def main():
    st.title("SynapseAI")

    login()  # sidebar login

    if not st.session_state.auth_token:
        st.info("Please log in or register from the sidebar to continue.")
        return

    # If logged in, ensure we have notebooks
    if not st.session_state.notebooks:
        load_notebooks()

    # Notebook selection + create
    with st.sidebar:
        st.subheader("🆕 Create New")
        new_title = st.text_input("Notebook title", key="_new_nb_title")
        if st.button("Create"):
            if not new_title:
                st.warning("Enter a title.")
            else:
                created = api_create_notebook(new_title)
                if created:
                    st.success(f"Notebook '{new_title}' created!")
                    load_notebooks()
                    nid = created.get("id")
                    if nid:
                        st.session_state.current_notebook_id = nid
                        # Find the matching notebook object in the new list to update the selectbox
                        for nb in st.session_state.notebooks:
                            if nb.get("id") == nid:
                                st.session_state._nb_select = nb
                                break
                    safe_rerun()
                else:
                    st.error("Failed to create notebook.")

        st.markdown("---")
        st.subheader("📓 Notebooks")
        if st.session_state.notebooks:
            selected = st.selectbox(
                "Select notebook",
                options=st.session_state.notebooks,
                format_func=lambda n: n.get("title") or str(n.get("id")),
                key="_nb_select",
            )
            if selected:
                st.session_state.current_notebook_id = selected.get("id")
        else:
            st.info("No notebooks available yet.")

    # Main actions
    notebook_id = st.session_state.current_notebook_id
    if notebook_id:
        # Check if we need to load history for this notebook
        if st.session_state.last_loaded_id != notebook_id:
            st.session_state.messages = api_get_chat_history(notebook_id)
            st.session_state.last_loaded_id = notebook_id
            
        upload_section(notebook_id)
        chat_interface(notebook_id)
    else:
        st.info("Select a notebook from the sidebar to start chatting.")


if __name__ == "__main__":
    # Ensure current_notebook_id is updated when selection changes
    if "_nb_select" in st.session_state and st.session_state._nb_select:
        st.session_state.current_notebook_id = st.session_state._nb_select.get("id")
    main()
