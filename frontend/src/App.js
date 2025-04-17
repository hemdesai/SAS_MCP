import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [code, setCode] = useState('');
  const [runResp, setRunResp] = useState(null);
  const [status, setStatus] = useState(null);
  const [sessionId, setSessionId] = useState('');
  const [library, setLibrary] = useState('work');
  const [tableName, setTableName] = useState('');
  const [tableData, setTableData] = useState(null);
  const [results, setResults] = useState(null);
  const [polling, setPolling] = useState(false);

  const handleRun = async () => {
    setRunResp(null);
    setStatus(null);
    setTableData(null);
    setResults(null);
    const resp = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });
    if (!resp.ok) {
      const err = await resp.json();
      alert(err.detail || 'Error');
      return;
    }
    const data = await resp.json();
    setRunResp(data);
    setSessionId(data.session_id);
    setPolling(true);
  };

  useEffect(() => {
    let timer;
    if (polling && runResp) {
      timer = setInterval(async () => {
        const q = `job_id=${runResp.job_id}&session_id=${runResp.session_id}`;
        const resp = await fetch(`/api/status?${q}`);
        if (resp.ok) {
          const st = await resp.json();
          setStatus(st);
          if (st.state === 'completed' || st.state === 'failed') {
            setPolling(false);
            clearInterval(timer);
            // auto-fetch when job finishes
            handleFetchResults();
          }
        }
      }, 2000);
    }
    return () => clearInterval(timer);
  }, [polling, runResp]);

  useEffect(() => {
    // fetch results once job is no longer running (completed or error)
    if (status && status.state !== 'running') {
      handleFetchResults();
    }
  }, [status]);

  const handleFetchTable = async () => {
    const query = `session_id=${sessionId}&library=${library}&table_name=${tableName}`;
    const resp = await fetch(`/api/table?${query}`);
    if (!resp.ok) {
      const err = await resp.json();
      alert(err.detail || 'Error fetching table');
      return;
    }
    const data = await resp.json();
    setTableData(data);
  };

  const handleFetchResults = async () => {
    const q = `job_id=${runResp.job_id}&session_id=${runResp.session_id}`;
    const resp = await fetch(`/api/results?${q}`);
    if (!resp.ok) {
      const err = await resp.json();
      alert(err.detail || 'Error fetching results');
      return;
    }
    const data = await resp.json();
    setResults(data);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>MCP SAS Viya Demo</h1>
      </header>
      <main>
        <section>
          <h2>Run SAS Code</h2>
          <textarea value={code} onChange={e => setCode(e.target.value)} rows="10" />
          <br />
          <button className="button" onClick={handleRun}>Run</button>
        </section>
        {runResp && (
          <section>
            <h2>Job Info</h2>
            <p>Session ID: {runResp.session_id}</p>
            <p>Job ID: {runResp.job_id}</p>
          </section>
        )}
        {status && (
          <section>
            <h2>Status</h2>
            <p>State: {status.state}</p>
            <p>Message: {status.message}</p>
            // allow manual fetch once job finishes or errors
            <button className="button" onClick={handleFetchResults}>Fetch Results</button>
          </section>
        )}
        {status && status.state === 'completed' && (
          <section>
            <h2>Fetch Table</h2>
            <input type="text" value={library} onChange={e => setLibrary(e.target.value)} placeholder="Library" />
            <input type="text" value={tableName} onChange={e => setTableName(e.target.value)} placeholder="Table Name" />
            <button className="button" onClick={handleFetchTable}>Fetch</button>
          </section>
        )}
        {tableData && (
          <section>
            <h2>Table Data</h2>
            <pre>{JSON.stringify(tableData, null, 2)}</pre>
          </section>
        )}
        {results && (
          <section>
            <h2>Results</h2>
            <pre>{JSON.stringify(results, null, 2)}</pre>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
