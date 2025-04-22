import React, { useState, useRef, useEffect } from 'react';

function renderTable(table) {
  if (!table || !table.columns || !table.rows) return null;
  return (
    <table style={{ margin: '10px auto', borderCollapse: 'collapse' }}>
      <thead>
        <tr>
          {table.columns.map((col, i) => (
            <th key={i} style={{ border: '1px solid #ccc', padding: '4px 8px' }}>{col}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {table.rows.map((row, i) => (
          <tr key={i}>
            {row.map((cell, j) => (
              <td key={j} style={{ border: '1px solid #ccc', padding: '4px 8px' }}>{cell}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function ChatBot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    setMessages([]);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function parseInput(raw) {
    const lines = raw.split('\n');
    let tables = [];
    let codeLines = [];
    for (let line of lines) {
      if (line.trim().toLowerCase().startsWith('tables:')) {
        tables = line.replace(/tables:/i, '').split(',').map(x => x.trim()).filter(Boolean).slice(0, 2);
      } else {
        codeLines.push(line);
      }
    }
    return { code: codeLines.join('\n').trim(), tables };
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!input.trim()) return;
    const { code, tables } = parseInput(input);
    setMessages(msgs => [...msgs, { role: 'user', content: input }]);
    setInput('');
    setLoading(true);
    try {
      const resp = await fetch('/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: code, tables })
      });
      if (!resp.ok) {
        const err = await resp.json();
        setMessages(msgs => [...msgs, { role: 'assistant', content: err.detail || 'Error from backend.' }]);
        setLoading(false);
        return;
      }
      const data = await resp.json();
      setMessages(msgs => [
        ...msgs,
        { role: 'assistant', content: data.answer || data.message || 'Job complete.', tables: data.tables }
      ]);
    } catch (err) {
      setMessages(msgs => [...msgs, { role: 'assistant', content: 'Error: ' + err.message }]);
    }
    setLoading(false);
  }

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', padding: 0 }}>
      <div style={{ fontSize: '1rem', fontWeight: 600, color: '#205080', opacity: 0.65, letterSpacing: 0.5, margin: '18px 0 8px 0', textAlign: 'left' }}>
        MCP SAS Viya Chatbot Demo
      </div>
      <div style={{
        background: 'linear-gradient(90deg, #e3f0ff 0%, #f7faff 100%)',
        border: '1px solid #b6d6ff',
        padding: 18,
        borderRadius: 9,
        marginBottom: 22
      }}>
        <div style={{ fontWeight: 600, marginBottom: 8, color: '#205080', fontSize: '1.07rem' }}>
          How to use this chatbot:
        </div>
        <ul style={{ margin: 0, paddingLeft: 22, color: '#205080', fontSize: '1.01rem' }}>
          <li>Enter your SAS code or math prompt in the chat box below.</li>
          <li>
            <b>To fetch tables, add a separate line at the end of your message:</b><br />
            <span style={{
              background: '#e6f3ff', padding: '2px 6px', borderRadius: 3,
              fontFamily: 'monospace', color: '#0a3d7c'
            }}>Tables: results1, results2</span><br />
            (You can list one or two table names, separated by commas. Table names must match your SAS code exactly.)
          </li>
        </ul>
        <div style={{
          marginTop: 16, padding: 10, background: '#fffbe7',
          border: '1px solid #ffe7a0', borderRadius: 7
        }}>
          <div style={{ fontWeight: 500, color: '#a07b00', marginBottom: 4 }}>Example 1 (Simple):</div>
          <pre style={{
            margin: 0, fontSize: '0.98rem', background: '#f8f8f8',
            padding: 8, borderRadius: 4
          }}>data work.results; x=2+3+5+7; run;
Tables: results</pre>
        </div>
        <div style={{
          marginTop: 12, padding: 10, background: '#fffbe7',
          border: '1px solid #ffe7a0', borderRadius: 7
        }}>
          <div style={{ fontWeight: 500, color: '#a07b00', marginBottom: 4 }}>Example 2 (SAS code + tables):</div>
          <pre style={{
            margin: 0, fontSize: '0.98rem', background: '#f8f8f8',
            padding: 8, borderRadius: 4, whiteSpace: 'pre-wrap'
          }}>data work.results1; length name $16; id=1; name='Alice'; salary=50000+5000; output;
id=2; name='Bob'; salary=.; output;
id=3; name='Charlie'; salary=60000*1.05; output; run;
proc means data=work.results1 n mean std min max; var salary; output out=work.results2; run;
Tables: results1, results2</pre>
        </div>
      </div>
      <div style={{ maxWidth: 600, margin: '0 auto', background: '#fff', borderRadius: 8, boxShadow: '0 2px 8px #0001', padding: 20 }}>
        <div style={{ minHeight: 200, maxHeight: 400, overflowY: 'auto', marginBottom: 10 }}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{ textAlign: msg.role === 'user' ? 'right' : 'left', margin: '8px 0' }}>
              <div style={{ display: 'inline-block', background: msg.role === 'user' ? '#e6f3ff' : '#f5f5f5', padding: '8px 12px', borderRadius: 6, maxWidth: '90%' }}>
                {msg.content}
                {msg.tables && Object.entries(msg.tables).map(([name, tbl]) => (
                  <div key={name}>
                    <div style={{ fontWeight: 'bold', margin: '8px 0 2px 0' }}>{name}</div>
                    {renderTable(tbl)}
                  </div>
                ))}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        <form onSubmit={handleSend} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type your SAS code or math prompt..."
              style={{ flex: 1, padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
              disabled={loading}
            />
            <button type="submit" className="button" disabled={loading || !input.trim()}>Send</button>
          </div>
        </form>
        {loading && <div style={{ marginTop: 8, color: '#888' }}>Thinking...</div>}
      </div>
    </div>
  );
}
