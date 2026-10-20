import { useEffect, useMemo, useState } from 'react'

const api = async (url, options) => {
  const isForm = options?.body instanceof FormData
  let response
  try {
    response = await fetch(url, {
      ...options,
      headers: { ...(isForm ? {} : { 'Content-Type': 'application/json' }), ...options?.headers },
    })
  } catch {
    throw new Error('Cannot reach the local API at 127.0.0.1:8000. Start the app with “npm run dev” from the frontend folder.')
  }
  let data
  try {
    data = await response.json()
  } catch {
    throw new Error('The local API returned an unreadable response. Check the API terminal for details.')
  }
  if (!response.ok) throw new Error(data.detail || 'Something went wrong.')
  return data
}

const formatUser = (value) => value?.split('\\').at(-1) || value

function App() {
  const [health, setHealth] = useState(null)
  const [selectedFiles, setSelectedFiles] = useState([])
  const [folderName, setFolderName] = useState('')
  const [data, setData] = useState(null)
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('All employees')
  const [busy, setBusy] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState({ percent: 0, stage: 'Preparing your files' })
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    let timer
    const check = async () => {
      try {
        const result = await api('/api/health')
        if (active) setHealth({ ...result, available: true })
      } catch {
        if (active) {
          setHealth({ ready: false, available: false })
          timer = window.setTimeout(check, 4000)
        }
      }
    }
    check()
    return () => { active = false; window.clearTimeout(timer) }
  }, [])

  useEffect(() => {
    if (!selected) return
    setDetail(null)
    api('/api/employee', { method: 'POST', body: JSON.stringify({ user: selected.user }) })
      .then(setDetail).catch((err) => setError(err.message))
  }, [selected])

  const employees = data?.employees || []
  const requiredFiles = ['logon.csv', 'device.csv', 'file.csv', 'email.csv', 'http.csv']
  const selectedNames = new Set(selectedFiles.map((file) => file.name.toLowerCase()))
  const missingFiles = requiredFiles.filter((name) => !selectedNames.has(name))
  const visibleEmployees = useMemo(() => employees.filter((person) => {
    const matchesQuery = `${person.user} ${person.name || ''}`.toLowerCase().includes(query.toLowerCase())
    const matchesFilter = filter === 'All employees' || person.status === filter.toUpperCase()
    return matchesQuery && matchesFilter
  }), [employees, filter, query])

  async function analyze(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setDetail(null)
    setSelected(null)
    setAnalysisProgress({ percent: 0, stage: 'Preparing your files' })
    let polling = true
    const pollProgress = async () => {
      while (polling) {
        try {
          const progress = await api('/api/progress')
          if (progress.active) {
            setAnalysisProgress({ percent: Math.max(15, progress.percent), stage: progress.stage })
          }
        } catch { /* The analysis request will report API errors. */ }
        await new Promise((resolve) => window.setTimeout(resolve, 400))
      }
    }
    const progressPolling = pollProgress()
    try {
      const form = new FormData()
      selectedFiles.forEach((file) => form.append('files', file, file.name))
      const result = await new Promise((resolve, reject) => {
        const request = new XMLHttpRequest()
        request.open('POST', '/api/analyze-upload')
        request.upload.onprogress = (progress) => {
          if (progress.lengthComputable) {
            setAnalysisProgress({
              percent: Math.round((progress.loaded / progress.total) * 15),
              stage: 'Uploading selected logs',
            })
          }
        }
        request.onload = () => {
          let body
          try { body = JSON.parse(request.responseText) } catch {
            reject(new Error('The local API returned an unreadable response. Check the API terminal for details.'))
            return
          }
          if (request.status < 200 || request.status >= 300) {
            reject(new Error(body.detail || 'Something went wrong.'))
            return
          }
          setAnalysisProgress({ percent: 100, stage: 'Analysis complete' })
          resolve(body)
        }
        request.onerror = () => reject(new Error('Cannot reach the local API at 127.0.0.1:8000. Start the app with “npm run dev” from the frontend folder.'))
        request.send(form)
      })
      setData(result)
      setFilter('All employees')
    } catch (err) { setError(err.message) }
    finally {
      polling = false
      await progressPolling
      setBusy(false)
    }
  }

  const flagged = employees.filter((person) => person.status === 'SUSPICIOUS').slice(0, 10)
  const otherEmployees = visibleEmployees.filter((person) => !flagged.includes(person))

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">◎</span><span>Forensio</span></div>
        <div className="workspace-label">WORKSPACE</div>
        <button className="nav-item active"><span className="nav-icon">▦</span>Overview</button>
        <div className="side-rule" />
        <div className="side-caption">ANALYSIS MODELS</div>
        <div className="model-nav"><i className="dot teal" />Isolation Forest</div>
        <div className="model-nav"><i className="dot blue" />Logistic Regression</div>
        <div className="model-nav"><i className="dot violet" />Decision Tree</div>
        <div className="model-nav"><i className="dot amber" />Random Forest</div>
        <div className="sidebar-bottom"><div className="privacy-icon">◇</div><div><b>Private by design</b><small>Activity data stays on this device.</small></div></div>
      </aside>

      <main className="main-content">
        <header className="topbar"><div className="crumb">Risk intelligence <span>/</span> Overview</div><div className="top-right"><span className="local-badge"><i /> Local analysis</span><div className="avatar">HR</div></div></header>
        <div className="page-wrap">
          <section className="page-heading"><div><div className="eyebrow">INSIDER RISK · REVIEW CONSOLE</div><h1>Investigation overview</h1><p>Bring unusual activity into focus. Every signal is a prompt for careful human review.</p></div><div className="date-chip">⌁ &nbsp; Model ensemble <span>·</span> 4 models</div></section>

          <form className="source-card" onSubmit={analyze}>
            <div className="source-icon">⌂</div><div className="source-copy"><b>Choose an activity data folder</b><span>Select the folder containing logon.csv, device.csv, file.csv, email.csv and http.csv.</span></div>
            <div className="source-controls"><label className="folder-picker"><span>▧ &nbsp; {folderName || 'Choose folder'}</span><input type="file" aria-label="Choose activity folder" webkitdirectory="" directory="" multiple onChange={(event) => { const files = Array.from(event.target.files || []); setSelectedFiles(files); setFolderName(files[0]?.webkitRelativePath?.split('/')[0] || '') }} /></label><button className="primary-button" disabled={busy || missingFiles.length > 0 || !health?.ready}>{busy ? <><span className="spinner" /> Analyzing…</> : <>Analyze folder <span>→</span></>}</button></div>
            {folderName && <div className="source-note">{missingFiles.length ? `Selected “${folderName}” · ${selectedFiles.length} files · missing ${missingFiles.join(', ')}` : `Selected “${folderName}” · ${selectedFiles.length} files · all required logs found. Files upload only to this local app.`}</div>}
            {!health?.ready && <div className="source-note warning">{health?.available ? health.message : health ? error || 'Local API is not reachable. Start the app with “npm run dev” from the frontend folder.' : 'Checking the local analysis service…'}</div>}
          </form>
          {busy && <section className="analysis-card" role="status" aria-live="polite">
            <div className="analysis-visual" aria-hidden="true">
              <div className="analysis-orbit orbit-a" /><div className="analysis-orbit orbit-b" />
              <div className="analysis-core"><span>◎</span></div>
              <i className="analysis-node node-a" /><i className="analysis-node node-b" />
              <i className="analysis-node node-c" /><i className="analysis-node node-d" />
            </div>
            <div className="analysis-copy">
              <div className="eyebrow">LIVE ANALYSIS · FOUR MODEL ENSEMBLE</div>
              <h2>Finding patterns in the activity</h2>
              <p>{analysisProgress.stage}. Your files are processed locally.</p>
              <div className="analysis-progress-heading"><span>Analysis progress</span><b>{analysisProgress.percent}%</b></div>
              <div className="analysis-progress-track" role="progressbar" aria-label="Analysis progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow={analysisProgress.percent}>
                <i style={{ width: `${analysisProgress.percent}%` }} />
              </div>
              <div className="analysis-stage-list"><span className={analysisProgress.percent >= 15 ? 'complete' : 'current'}>01 <b>Prepare</b></span><span className={analysisProgress.percent >= 65 ? 'complete' : analysisProgress.percent >= 15 ? 'current' : ''}>02 <b>Score</b></span><span className={analysisProgress.percent >= 90 ? 'complete' : analysisProgress.percent >= 65 ? 'current' : ''}>03 <b>Prioritize</b></span></div>
            </div>
          </section>}
          <details className="model-guide">
            <summary><span><b>How the model ensemble works</b><small>See how activity records become a review priority.</small></span><span className="guide-action">Explore the scoring flow <i>＋</i></span></summary>
            <div className="guide-content">
              <div className="flow-strip">
                <div className="flow-step"><small>01 · SOURCES</small><b>Five activity logs</b><span>Logon · device · file · email · web</span></div>
                <i className="flow-arrow">→</i>
                <div className="flow-step"><small>02 · PREPARE</small><b>Employee-day features</b><span>Counts, after-hours, USB, attachments</span></div>
                <i className="flow-arrow">→</i>
                <div className="flow-step"><small>03 · SCORE</small><b>Four model views</b><span>Same feature row, scored independently</span></div>
                <i className="flow-arrow">→</i>
                <div className="flow-step"><small>04 · PRIORITIZE</small><b>Percentile consensus</b><span>Ranked queue for human review</span></div>
              </div>
              <div className="guide-section-title"><b>What each model contributes</b><span>Different methods can surface different patterns.</span></div>
              <div className="model-explain-grid">
                <article className="model-explain indigo"><span>01</span><div><small>UNSUPERVISED ANOMALY</small><h3>Isolation Forest</h3><p>Finds employee-days that are isolated from common activity patterns. It does not use incident labels when learning what looks unusual.</p></div></article>
                <article className="model-explain sky"><span>02</span><div><small>SUPERVISED CLASSIFIER</small><h3>Logistic Regression</h3><p>Learns how activity features relate to labeled incidents and produces a risk score from that weighted relationship.</p></div></article>
                <article className="model-explain violet"><span>03</span><div><small>SUPERVISED CLASSIFIER</small><h3>Decision Tree</h3><p>Uses a sequence of learned feature thresholds to score activity. Its single tree is capped at depth 10.</p></div></article>
                <article className="model-explain amber"><span>04</span><div><small>SUPERVISED ENSEMBLE</small><h3>Random Forest</h3><p>Averages predictions from 200 decision trees trained with variation, giving a broader view than one tree alone.</p></div></article>
              </div>
              <div className="guide-rule"><span>How a review flag is assigned</span><p>For each employee-day, the four model scores become percentile ranks and are averaged. The employee list uses each person’s highest-risk day. An employee is prioritized if that consensus is in the top 5%, or at least two model ranks are in the top 10%. These are relative review thresholds, not probabilities or findings of misconduct.</p></div>
            </div>
          </details>
          {error && <div className="error-banner"><span>!</span>{error}<button onClick={() => setError('')} aria-label="Dismiss">×</button></div>}

          {data ? <>
            <section className="metrics-grid">
              <Metric label="EMPLOYEES ANALYZED" value={data.summary.employees.toLocaleString()} detail="Across all activity sources" icon="♙" tone="teal" />
              <Metric label="PRIORITIZED FOR REVIEW" value={data.summary.flagged.toLocaleString()} detail="Flagged by the review rule" icon="⌁" tone="orange" />
              <Metric label="ACTIVE DAYS" value={data.summary.activeDays.toLocaleString()} detail="Employee-day records covered" icon="▦" tone="blue" />
              <Metric label="MODELS IN AGREEMENT" value="4" detail="Independent scoring perspectives" icon="◉" tone="violet" />
            </section>

            <div className="section-heading"><div><div className="eyebrow">REVIEW QUEUE</div><h2>Employees prioritized for review</h2><p>Ranked by consensus across four models. A flag is not proof of wrongdoing.</p></div><span className="queue-count">{flagged.length} prioritized</span></div>
            {flagged.length ? <div className="flagged-grid">{flagged.map((person, i) => <button className={`flag-card ${selected?.user === person.user ? 'chosen' : ''}`} key={person.user} onClick={() => setSelected(person)}><span className="flag-top"><span className="rank-number">{String(i + 1).padStart(2, '0')}</span><span className="status-pill suspicious"><i /> Prioritize</span></span><b className="employee-name">{person.name || formatUser(person.user)}</b><span className="employee-id">{person.name ? formatUser(person.user) : 'Employee identifier'}</span><span className="reason">{person.why_flagged}</span><span className="flag-foot"><span>{person.model_agreement}/4 models aligned</span><span className="score">{(person.consensus_score * 100).toFixed(1)} <small>rank</small></span></span></button>)}</div> : <div className="empty-state">No employees crossed the review rule for this dataset.</div>}

            <section className="directory-card"><div className="directory-heading"><div><h2>Employee directory</h2><p>Explore the full set of ranked employees.</p></div><div className="directory-controls"><label className="search-box"><span>⌕</span><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search employees" /></label><select value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filter employee status"><option>All employees</option><option>Suspicious</option><option>Review</option></select></div></div><div className="table-scroll"><table><thead><tr><th>EMPLOYEE</th><th>STATUS</th><th>CONSENSUS RANK</th><th>MODEL AGREEMENT</th><th>ACTIVE DAYS</th><th></th></tr></thead><tbody>{otherEmployees.slice(0, 50).map((person) => <tr key={person.user} onClick={() => setSelected(person)} className={selected?.user === person.user ? 'selected-row' : ''}><td><b>{person.name || formatUser(person.user)}</b><small>{person.name ? formatUser(person.user) : 'Employee identifier'}</small></td><td><span className={`status-pill ${person.status.toLowerCase()}`}><i />{person.status === 'SUSPICIOUS' ? 'Prioritize' : 'Review'}</span></td><td><div className="table-score"><div><i style={{ width: `${Math.max(4, person.consensus_score * 100)}%` }} /></div><span>{(person.consensus_score * 100).toFixed(1)}</span></div></td><td>{person.model_agreement} / 4 models</td><td>{person.active_days}</td><td className="row-arrow">↗</td></tr>)}</tbody></table>{!otherEmployees.length && <div className="table-empty">No employees match these filters.</div>}{otherEmployees.length > 50 && <div className="table-foot">Showing 50 of {otherEmployees.length} employees. Search to narrow the list.</div>}</div></section>

            {selected && <section className="detail-card"><div className="detail-heading"><div><div className="eyebrow">EMPLOYEE PROFILE</div><h2>{detail?.name || formatUser(selected.user)}</h2><p>{detail?.name ? formatUser(selected.user) : 'Selected employee'} · {detail?.activeDays ?? selected.active_days} active days</p></div><button className="close-button" onClick={() => { setSelected(null); setDetail(null) }}>×</button></div>{detail ? <><div className="detail-reason"><span className="status-pill suspicious"><i />{detail.status === 'SUSPICIOUS' ? 'Prioritize' : 'Review'}</span><span>{detail.whyFlagged}</span></div><div className="detail-columns"><div><h3>Model score comparison <small>Relative rank · 0–100</small></h3><div className="score-list">{detail.scores.map((item) => <div className="score-row" key={item.model}><span>{item.model}</span><div className="bar-track"><i style={{ width: `${item.score}%` }} /></div><b>{item.score.toFixed(1)}</b></div>)}</div></div><div><h3>Highest-ranked activity days <small>Up to 20 days</small></h3><div className="activity-table"><table><thead><tr>{Object.keys(detail.activity[0] || {}).map((key) => <th key={key}>{key}</th>)}</tr></thead><tbody>{detail.activity.map((row, i) => <tr key={i}>{Object.values(row).map((value, j) => <td key={j}>{value ?? '—'}</td>)}</tr>)}</tbody></table></div></div></div></> : <div className="loading-detail"><span className="spinner dark" /> Loading employee profile…</div>}</section>}
          </> : <section className="welcome-card"><div className="welcome-art"><span>◉</span><i className="orbit orbit-one" /><i className="orbit orbit-two" /><i className="spark spark-one">✳</i><i className="spark spark-two">✦</i></div><div><div className="eyebrow">YOUR REVIEW SPACE</div><h2>Start with your activity data</h2><p>Choose the folder that contains your five activity logs. The four model ensemble will score employee-day patterns and create a ranked review queue.</p><div className="welcome-steps"><span><b>01</b> Select data folder</span><span><b>02</b> Score activity logs</span><span><b>03</b> Review signals</span></div></div></section>}

          <footer className="footer-note"><span>◈</span><p>Scores are relative ranks within the selected dataset, not probabilities. Confirm findings against original logs and other evidence before drawing conclusions.</p></footer>
        </div>
      </main>
    </div>
  )
}

function Metric({ label, value, detail, icon, tone }) {
  return <article className="metric-card"><div className="metric-top"><span>{label}</span><i className={`metric-icon ${tone}`}>{icon}</i></div><strong>{value}</strong><small>{detail}</small></article>
}

export default App
