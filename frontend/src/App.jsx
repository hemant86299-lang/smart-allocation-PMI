import React, { useEffect, useMemo, useState } from 'react'
import {
  LayoutDashboard, Users, BriefcaseBusiness, Cpu, BarChart3,
  CheckCircle2, Clock3, Search, Play, RotateCcw, MapPin,
  Sparkles, Menu, X, Server, AlertCircle
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'

function App() {
  const [active, setActive] = useState('Dashboard')
  const [query, setQuery] = useState('')
  const [running, setRunning] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [candidates, setCandidates] = useState([])
  const [opportunities, setOpportunities] = useState([])
  const [results, setResults] = useState([])
  const [error, setError] = useState('')
  const [lastRun, setLastRun] = useState(null)
  const [decliningId, setDecliningId] = useState(null)
  const [declineMessage, setDeclineMessage] = useState('')
  const [explainingId, setExplainingId] = useState(null)
  const [explanationText, setExplanationText] = useState('')
  const [explanationOpen, setExplanationOpen] = useState(false)

  const loadData = async () => {
    try {
      setError('')
      const [c, o, r] = await Promise.all([
        fetch(`${API_BASE}/candidates`),
        fetch(`${API_BASE}/opportunities`),
        fetch(`${API_BASE}/results`),
      ])
      if (!c.ok || !o.ok || !r.ok) throw new Error('Backend is not ready. Start FastAPI first.')
      setCandidates(await c.json())
      setOpportunities(await o.json())
      setResults(await r.json())
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => { loadData() }, [])

  const runAllocation = async () => {
    setRunning(true)
    setError('')
    try {
      const response = await fetch(`${API_BASE}/allocation/run`, { method: 'POST' })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Allocation failed.')
      setResults(data.results || [])
      setLastRun(data)
      await loadData()
      setActive('Results')
    } catch (e) {
      setError(e.message)
    } finally {
      setRunning(false)
    }
  }

  const declineOffer = async (candidateId) => {
    setDecliningId(candidateId)
    setDeclineMessage('')
    setError('')
    try {
      const response = await fetch(`${API_BASE}/reallocation/decline/${candidateId}`, { method: 'POST' })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Reallocation failed.')
      setResults(data.results || [])
      setDeclineMessage(data.message || 'Reallocation complete.')
      await loadData()
    } catch (e) {
      setError(e.message)
    } finally {
      setDecliningId(null)
    }
  }

  const explainCandidate = async (candidateId) => {
    setExplainingId(candidateId)
    setError('')
    try {
      const response = await fetch(`${API_BASE}/explainability/candidate/${candidateId}`)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Explanation failed.')
      setExplanationText(data.explanation || 'No explanation returned.')
      setExplanationOpen(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setExplainingId(null)
    }
  }

  const filteredCandidates = useMemo(() => {
    const q = query.toLowerCase()
    return candidates.filter(c =>
      `${c.name} ${c.candidate_id} ${c.skills} ${c.location_pref}`.toLowerCase().includes(q)
    )
  }, [candidates, query])

  const candidateMap = useMemo(() => Object.fromEntries(candidates.map(c => [c.candidate_id, c])), [candidates])
  const opportunityMap = useMemo(() => Object.fromEntries(opportunities.map(o => [o.internship_id, o])), [opportunities])

  const enrichedResults = results.map(r => ({
    ...r,
    candidate: candidateMap[r.candidate_id],
    internship: opportunityMap[r.internship_id],
  }))

  const allocatedCount = results.length
  const pendingCount = Math.max(candidates.length - allocatedCount, 0)
  const avgScore = results.length
    ? Math.round(results.reduce((sum, r) => sum + Number(r.fit_score || 0), 0) / results.length)
    : 0
  const successRate = candidates.length ? Math.round((allocatedCount / candidates.length) * 100) : 0

  const nav = [
    ['Dashboard', LayoutDashboard], ['Candidates', Users], ['Opportunities', BriefcaseBusiness],
    ['Smart Allocation', Cpu], ['Results', CheckCircle2], ['Analytics', BarChart3],
  ]

  return (
    <div className="app-shell">
      {mobileOpen && <div className="backdrop" onClick={() => setMobileOpen(false)} />}
      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark"><Cpu size={22} /></div>
          <div><strong>SmartAlloc</strong><span>PM Internship Scheme</span></div>
          <button className="close-btn" onClick={() => setMobileOpen(false)}><X size={20}/></button>
        </div>
        <div className="demo-pill"><span /> Python Engine Connected</div>
        <nav>{nav.map(([label, Icon]) => (
          <button key={label} className={active === label ? 'nav-item active' : 'nav-item'}
            onClick={() => { setActive(label); setMobileOpen(false) }}>
            <Icon size={19}/><span>{label}</span>
          </button>
        ))}</nav>
        <div className="sidebar-foot">AI-Based Smart Allocation<br/><small>React + FastAPI + Python</small></div>
      </aside>

      <main className="main">
        <header className="topbar">
          <button className="menu-btn" onClick={() => setMobileOpen(true)}><Menu/></button>
          <div><h1>{active}</h1><p>Smart internship allocation dashboard</p></div>
          <div className="top-actions">
            <div className="search"><Search size={17}/><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search candidates..."/></div>
            <div className="avatar">SA</div>
          </div>
        </header>

        {error && <div className="content"><div className="panel" style={{color:'#b91c1c',background:'#fef2f2'}}><AlertCircle size={16}/> {error}</div></div>}

        {active === 'Dashboard' && <section className="content">
          <div className="hero"><div><span className="eyebrow">PM INTERNSHIP ALLOCATION</span><h2>Smarter matching. Better opportunities.</h2><p>The React dashboard is connected to the real Python allocation engine through FastAPI. Results are read directly from the engine's generated CSV outputs.</p></div><button className="primary" onClick={() => setActive('Smart Allocation')}><Cpu size={18}/> Open Allocation Engine</button></div>
          <div className="stats">
            <Stat label="Total Candidates" value={candidates.length} Icon={Users}/>
            <Stat label="Internship Opportunities" value={opportunities.length} Icon={BriefcaseBusiness}/>
            <Stat label="Allocated" value={allocatedCount} Icon={CheckCircle2}/>
            <Stat label="Pending" value={pendingCount} Icon={Clock3}/>
            <Stat label="Avg. Fit Score" value={`${avgScore}%`} Icon={Sparkles}/>
          </div>
          <div className="grid-2">
            <div className="panel"><div className="panel-head"><div><h3>Allocation Overview</h3><p>Current Python-engine allocation status</p></div></div><div className="overview"><div className="donut" style={{background:`conic-gradient(#2563eb 0 ${successRate}%,#dbeafe ${successRate}% 100%)`}}><strong>{successRate}%</strong><span>Allocated</span></div><div className="legend"><div><i className="dot allocated"/> Allocated <b>{allocatedCount}</b></div><div><i className="dot pending"/> Pending <b>{pendingCount}</b></div></div></div></div>
            <div className="panel"><div className="panel-head"><div><h3>Engine Status</h3><p>Live backend connection</p></div></div><div style={{padding:'30px 10px',display:'grid',gap:14}}><div><Server size={18}/> FastAPI backend: <strong>Connected</strong></div><div>Python optimizer: <strong>Available</strong></div><div>Latest run: <strong>{lastRun ? 'Just now' : 'Existing CSV results'}</strong></div></div></div>
          </div>
          <CandidateTable rows={filteredCandidates.slice(0, 8)} />
        </section>}

        {active === 'Candidates' && <section className="content"><div className="section-title"><div><h2>Candidate Pool</h2><p>Loaded from the Python engine's candidate dataset.</p></div><div className="count-badge">{filteredCandidates.length} shown</div></div><CandidateTable rows={filteredCandidates} /></section>}

        {active === 'Opportunities' && <section className="content"><div className="section-title"><div><h2>Internship Opportunities</h2><p>Loaded from the Python engine's internship dataset.</p></div></div><div className="cards-grid">{opportunities.map(o=><div className="op-card" key={o.internship_id}><div className="company-logo">{o.internship_id.slice(0,1)}</div><div><h3>{o.title}</h3><strong>{o.internship_id}</strong></div><div className="op-meta"><span><MapPin size={15}/> {o.location}</span><span><Users size={15}/> {o.capacity} seats</span></div><div className="tags">{String(o.required_skills).split(', ').map(s=><em key={s}>{s}</em>)}</div>{o.reserved_category && <div className="tags"><em>Reserved: {o.reserved_category}</em></div>}</div>)}</div></section>}

        {active === 'Smart Allocation' && <section className="content"><div className="allocation-hero"><div className="engine-icon"><Cpu size={32}/></div><span className="eyebrow">LIVE PYTHON ALLOCATION ENGINE</span><h2>Run Smart Allocation</h2><p>This button executes the existing Python pipeline: data generation → eligibility → fuzzy scoring → acceptance prediction → OR-Tools optimization.</p><button className="primary big" onClick={runAllocation} disabled={running}>{running ? <><span className="spinner"/> Running Python engine...</> : <><Play size={19}/> Run Smart Allocation</>}</button>{running && <div className="processing"><span>Generating candidate and internship data</span><span>Applying eligibility rules</span><span>Computing fuzzy fit scores</span><span>Predicting acceptance probabilities</span><span>Running OR-Tools optimization</span></div>}</div></section>}

        {active === 'Results' && <section className="content"><div className="section-title"><div><h2>Allocation Results</h2><p>Results returned by the Python optimizer through FastAPI.</p></div><button className="secondary" onClick={() => setActive('Smart Allocation')}><RotateCcw size={16}/> Run Again</button></div>{declineMessage && <div className="panel" style={{color:'#065f46',background:'#ecfdf5',marginBottom:16}}>{declineMessage}</div>}<div className="stats compact"><Stat label="Successful Allocations" value={allocatedCount} Icon={CheckCircle2}/><Stat label="Average Fit Score" value={`${avgScore}%`} Icon={Sparkles}/><Stat label="Pending" value={pendingCount} Icon={Clock3}/></div><AllocationTable rows={enrichedResults} onDecline={declineOffer} decliningId={decliningId} onExplain={explainCandidate} explainingId={explainingId} /></section>}

        {active === 'Analytics' && <section className="content"><div className="section-title"><div><h2>Analytics</h2><p>Calculated from the current engine output.</p></div></div><div className="analytics-grid"><Metric title="Allocation Success" value={`${successRate}%`} fill={successRate}/><Metric title="Average Fit Score" value={`${avgScore}%`} fill={avgScore}/><Metric title="Candidates" value={candidates.length} fill={100}/><Metric title="Opportunities" value={opportunities.length} fill={100}/></div><div className="panel"><h3>Current Engine Summary</h3><div style={{paddingTop:18,lineHeight:2,fontSize:13}}><div>Eligible/scored pairs are generated by the Python pipeline.</div><div>Final assignments are solved globally using OR-Tools CP-SAT.</div><div>Acceptance probability comes from the trained logistic regression model.</div></div></div></section>}
      </main>

      {explanationOpen && (
        <div className="backdrop" onClick={() => setExplanationOpen(false)} style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div onClick={e => e.stopPropagation()} style={{
            background: '#fff', borderRadius: 12, padding: 24,
            maxWidth: 720, maxHeight: '80vh', overflow: 'auto', width: '90%',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 style={{ margin: 0 }}>Explanation</h3>
              <button className="secondary" onClick={() => setExplanationOpen(false)}>Close</button>
            </div>
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, fontFamily: 'monospace', lineHeight: 1.5 }}>
              {explanationText}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

function Stat({label,value,Icon}){ return <div className="stat"><div className="stat-icon"><Icon size={19}/></div><div><span>{label}</span><strong>{value}</strong></div></div> }
function CandidateTable({ rows }) { return <div className="panel table-panel"><div className="panel-head"><div><h3>Candidate Records</h3><p>Candidate data returned by FastAPI</p></div></div><div className="table-wrap"><table><thead><tr><th>Candidate</th><th>Category</th><th>Skills</th><th>Location</th><th>Qualification</th></tr></thead><tbody>{rows.map(c=><tr key={c.candidate_id}><td><strong>{c.name}</strong><small>{c.candidate_id}</small></td><td>{c.category}</td><td>{c.skills}</td><td>{c.location_pref}</td><td><span className="score">{c.qualification_score}</span></td></tr>)}</tbody></table></div></div> }
function AllocationTable({ rows, onDecline, decliningId, onExplain, explainingId }) { return <div className="panel table-panel"><div className="table-wrap"><table><thead><tr><th>Candidate</th><th>Internship</th><th>Location</th><th>Fit Score</th><th>Acceptance</th><th>Status</th><th>Actions</th></tr></thead><tbody>{rows.map((a,i)=><tr key={`${a.candidate_id}-${a.internship_id}-${i}`}><td><strong>{a.candidate?.name || a.candidate_id}</strong><small>{a.candidate_id}</small></td><td>{a.internship?.title || a.internship_id}</td><td>{a.internship?.location || '-'}</td><td><span className="score">{Number(a.fit_score || 0).toFixed(2)}%</span></td><td>{(Number(a.accept_probability || 0) * 100).toFixed(1)}%</td><td><span className="status allocated">Allocated</span></td><td style={{display:'flex',gap:8}}><button className="secondary" disabled={explainingId === a.candidate_id} onClick={() => onExplain(a.candidate_id)}>{explainingId === a.candidate_id ? '...' : 'Explain'}</button><button className="secondary" disabled={decliningId === a.candidate_id} onClick={() => onDecline(a.candidate_id)}>{decliningId === a.candidate_id ? 'Processing...' : 'Decline'}</button></td></tr>)}</tbody></table></div></div> }
function Metric({title,value,fill}){const safe=Math.max(0,Math.min(100,Number(fill)||0));return <div className="metric"><div><span>{title}</span><strong>{value}</strong></div><div className="metric-ring" style={{'--fill':`${safe * 3.6}deg`}}><b>{Math.round(safe)}</b></div><div className="bar"><i style={{width:`${safe}%`}}/></div></div>}

export default App
