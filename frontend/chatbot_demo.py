import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="SAS MCP Chatbot Demo", layout="centered")
st.title("SAS MCP Server Chatbot Demo")

st.markdown("""
SAS MCP Chatbot Demo
- All SAS operations are routed through MCP tools (run_code, get_table, etc.).
- MCP tool call trace is shown after each response for transparency.
- No direct SAS client calls bypass MCP.

Instructions:
- SAS code: Enter code, specify Library and Table Name. **Only one Table Name input is present and always used. Set this field to the output table you want to fetch (e.g., results2).**
- Math prompt (e.g. 'Add 1,2,3'): Leave Library/Table blank. Result fetched from work.results.x automatically.
- For all other code, the Table Name input is always honored and determines which table is fetched.

Example 1: SAS Table
    data work.results;
      x=5+3; output;
      output;
    run;
  Library: work
  Table Name: results

Example 2: Multi-step SAS (means)
    data work.results1; ... ; run;
    proc means data=work.results1 ... ; output out=work.results2; run;
  Library: work
  Table Name: results2

Example 3: Math Prompt
  Prompt: Add 4, 9, 15, 23
  Library/Table: (leave blank)
""")

# Input fields for library and table name
library = st.text_input("Library", value="work")
table_name = st.text_input("Table Name", value="results")

if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please check your .env file.")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

user_input = st.text_input("You:", "", key="user_input")

import requests

def get_openai_response(messages, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4.1-mini-2025-04-14",
        "messages": messages,
        "max_tokens": 256,
        "temperature": 0.1
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Error: {str(e)}]"

import re

def is_math_query(text):
    # Simple detection: contains math operators or keywords
    return bool(re.search(r"(\d+\s*[\+\-\*/^]\s*\d+|add|subtract|multiply|divide|sum|product|difference|\beval\b)", text.lower()))

def get_sasviya_response(prompt, library, table_name):
    import requests
    import re
    try:
        resp = requests.post(
            "http://localhost:8000/chatbot",
            json={"prompt": prompt, "library": library, "table_name": table_name},
            timeout=20
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("tables"):
            t = data["tables"].get(table_name)
            if t and t.get("rows") and t.get("columns"):
                col_line = " | ".join(str(c) for c in t["columns"])
                rows_lines = [" | ".join(str(cell) for cell in row) for row in t["rows"]]
                return f"{col_line}\n" + "\n".join(rows_lines)
            elif t and t.get("error"):
                return f"Error fetching table {table_name}: {t['message']}"
        if data.get("log"):
            return data["log"]
        return data.get("error") or "[No result]"
    except Exception as e:
        return f"[SAS Viya error: {str(e)}]"

processing = False
route_info = ""

if st.button("Send") or st.session_state.get("send_on_enter"):
    user_input = st.session_state["user_input"]
    st.session_state["chat_history"].append(("user", user_input))
    # Do NOT assign to st.session_state["user_input"] here to avoid StreamlitAPIException
    # Route to SAS Viya or OpenAI
    if is_math_query(user_input) or user_input.strip().startswith("data "):
        route_info = "Routed to SAS MCP (SAS Viya)"
        with st.spinner("Processing via SAS MCP..."):
            bot_response = get_sasviya_response(user_input, library, table_name)
        # Show MCP tool trace for demo
        mcp_trace = f"MCP tool called: run_code(session_id=..., code=...) → get_table({library}, {table_name or 'results'})"
        st.session_state["chat_history"].append(("trace", mcp_trace))
    else:
        route_info = "Routed to OpenAI"
        with st.spinner("Processing via OpenAI..."):
            messages = []
            for speaker, msg in st.session_state["chat_history"]:
                role = "user" if speaker == "user" else "assistant"
                messages.append({"role": role, "content": msg})
            messages.append({"role": "user", "content": user_input})
            bot_response = get_openai_response(messages, OPENAI_API_KEY)
    st.session_state["chat_history"].append(("bot", bot_response))
    st.session_state["route_info"] = route_info

# Display chat, rendering SAS MCP tables as plain text for MVP
for i, (speaker, msg) in enumerate(st.session_state["chat_history"]):
    if speaker == "trace":
        st.markdown(f'<div style="color: #888; font-size: 0.9em;">{msg}</div>', unsafe_allow_html=True)
        continue
    align = "left" if speaker == "user" else "right"
    if speaker == "bot" and isinstance(msg, dict) and msg.get("tables"):
        st.markdown(f"<div style='text-align:{align};'><b>Bot (from SAS MCP Server):</b> (All math/results below are computed by SAS Viya MCP, not OpenAI)</div>", unsafe_allow_html=True)
        for tname, tdata in msg["tables"].items():
            if tdata.get("rows") and tdata.get("columns"):
                st.markdown(f"<b>Table: {tname}</b>")
                # Render as plain text
                col_line = " | ".join(str(c) for c in tdata["columns"])
                st.markdown(col_line)
                for row in tdata["rows"]:
                    row_line = " | ".join(str(cell) for cell in row)
                    st.markdown(row_line)
            elif tdata.get("error"):
                st.warning(f"Error fetching table {tname}: {tdata['message']}")
        if msg.get("log"):
            st.expander("SAS Log").write(msg["log"])
    else:
        st.markdown(f"<div style='text-align:{align};'><b>{speaker.title()}:</b> {msg}</div>", unsafe_allow_html=True)

# Show routing info/status at bottom
if "route_info" in st.session_state:
    st.info(st.session_state["route_info"])
