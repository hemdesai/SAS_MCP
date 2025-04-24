import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="SAS MCP Chatbot Demo", layout="centered")
st.title("SAS MCP Chatbot Demo")

st.markdown("""
SAS MCP Chatbot Demo
- All SAS operations are routed through MCP tools (run_code, get_table, etc.).
- MCP tool call trace is shown after each response for transparency.
- No direct SAS client calls bypass MCP.
- Classification and routing are now handled by the MCP agent.
- Every prompt flows: classify → run → status → get_table.

Instructions:
- SAS code: Enter code, specify Library and Table Name. **Only one Table Name input is present and always used. Set this field to the output table you want to fetch (e.g., results2).**
- For all other code, the Table Name input is always honored and determines which table is fetched.

Example 1: SAS Table
    data work.results;
      x=5+3;
    run;
  Library: work
  Table Name: results

Example 2: Multi-step SAS (means)
    data work.results1; ... ; run;
    proc means data=work.results1 ... ; output out=work.results2; run;
  Library: work
  Table Name: results2
  
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

def get_sasviya_response(prompt, library, table_name):
    try:
        resp = requests.post(
            "http://localhost:8000/chatbot",
            json={"prompt": prompt, "library": library, "table_name": table_name},
            timeout=20
        )
        # parse JSON response even if HTTP status != 200
        return resp.json()
    except requests.exceptions.HTTPError as http_err:
        # return error payload if possible
        try:
            return http_err.response.json()
        except Exception:
            return {"error": f"HTTP error: {http_err}"}
    except Exception as err:
        return {"error": str(err)}

processing = False
route_info = ""

if st.button("Send"):
    user_input = st.session_state["user_input"]
    st.session_state["chat_history"].append(("user", user_input))
    with st.spinner("Processing via SAS MCP Agent..."):
        data = get_sasviya_response(user_input, library, table_name)
    flow = "classify → run → status → get_table"
    trace_msg = f"Prompt classified as sas by MCP; flow: {flow}"
    st.session_state["chat_history"].append(("trace", trace_msg))
    st.session_state["chat_history"].append(("bot", data))

# Display chat, rendering SAS MCP tables as plain text for MVP
for i, (speaker, msg) in enumerate(st.session_state["chat_history"]):
    if speaker == "trace":
        st.markdown(f'<div style="color: #888; font-size: 0.9em;">{msg}</div>', unsafe_allow_html=True)
        continue
    align = "left" if speaker == "user" else "right"
    if speaker == "bot":
        label = "Bot (from SAS MCP Server):"
        desc = "(All results computed by SAS Viya MCP.)"
        st.markdown(f"<div style='text-align:{align};'><b>{label}</b> {desc}</div>", unsafe_allow_html=True)
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

# No external routing. All via MCP agent
