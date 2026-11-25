import { useEffect, useState } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000'
const REFRESH_MS = 5000
const COLORS = { Health: '#dc2626', 'Food Security': '#d97706', Education: '#2563eb' }

async function getJson(path) {
  const res = await fetch(`${API}${path}`)
  if (!res.ok) throw new Error(`${path} returned ${res.status}`)
  return res.json()
}

function Bars({ title, rows, selected, onSelect }) {
  const max = Math.max(1, ...rows.map((r) => r.count))
  return (
    <section className="card">
      <h2>{title}</h2>
      {rows.length === 0 && <p className="muted">No data yet</p>}
      {rows.map((r) => (
        <button
          key={r.name}
          className={`bar-row ${selected === r.name ? 'active' : ''}`}
          onClick={() => onSelect && onSelect(selected === r.name ? '' : r.name)}
        >
          <span className="bar-label">{r.name}</span>
          <span className="bar-track">
            <span
              className="bar-fill"
              style={{ width: `${(r.count / max) * 100}%`, background: COLORS[r.name] || '#4f46e5' }}
            />
          </span>
          <span className="bar-count">{r.count}</span>
        </button>
      ))}
    </section>
  )
}

function Days({ rows }) {
  const max = Math.max(1, ...rows.map((r) => r.count))
  return (
    <section className="card">
      <h2>Last 7 days</h2>
      {rows.length === 0 && <p className="muted">No data yet</p>}
      <div className="days">
        {rows.map((r) => (
          <div key={r.day} className="day">
            <span className="day-count">{r.count}</span>
            <span className="day-bar" style={{ height: `${(r.count / max) * 80 + 4}px` }} />
            <span className="day-label">{r.day.slice(5)}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

export default function App() {
  const [stats, setStats] = useState(null)
  const [concerns, setConcerns] = useState([])
  const [villages, setVillages] = useState([])
  const [category, setCategory] = useState('')
  const [village, setVillage] = useState('')
  const [flaggedOnly, setFlaggedOnly] = useState(false)
  const [error, setError] = useState('')
  const [updated, setUpdated] = useState(null)

  useEffect(() => {
    getJson('/api/villages').then((d) => setVillages(d.villages)).catch(() => {})
  }, [])

  useEffect(() => {
    let active = true
    const load = async () => {
      const params = new URLSearchParams({ limit: '50' })
      if (category) params.set('category', category)
      if (village) params.set('village', village)
      if (flaggedOnly) params.set('flagged', 'true')
      try {
        const [s, c] = await Promise.all([getJson('/api/stats'), getJson(`/api/concerns?${params}`)])
        if (active) {
          setStats(s)
          setConcerns(c.concerns)
          setError('')
          setUpdated(new Date())
        }
      } catch (e) {
        if (active) setError(`Cannot reach the backend (${e.message})`)
      }
    }
    load()
    const timer = setInterval(load, REFRESH_MS)
    return () => {
      active = false
      clearInterval(timer)
    }
  }, [category, village, flaggedOnly])

  const topCategory = stats?.by_category.reduce((a, b) => (b.count > (a?.count ?? 0) ? b : a), null)
  const topVillage = stats?.by_village[0]

  return (
    <main>
      <header>
        <div>
          <h1>Community Concerns Dashboard</h1>
          <p className="muted">Mathare Informal Settlement</p>
        </div>
        <p className="muted">
          {error ? '' : `Live, refreshed ${updated ? updated.toLocaleTimeString() : '...'}`}
        </p>
      </header>

      {error && <div className="error">{error}</div>}

      <div className="stats">
        <div className="stat"><span>{stats?.total ?? '-'}</span>Total concerns</div>
        <div className="stat"><span>{stats?.flagged ?? '-'}</span>Flagged for review</div>
        <div className="stat"><span>{topCategory?.count ? topCategory.name : '-'}</span>Top category</div>
        <div className="stat"><span>{topVillage ? topVillage.name : '-'}</span>Top village</div>
      </div>

      <div className="grid">
        <Bars title="By category" rows={stats?.by_category ?? []} selected={category} onSelect={setCategory} />
        <Bars title="By village" rows={stats?.by_village ?? []} selected={village} onSelect={setVillage} />
        <Days rows={stats?.by_day ?? []} />
      </div>

      <section className="card">
        <div className="filters">
          <h2>Concerns</h2>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            {(stats?.by_category ?? []).map((c) => <option key={c.name}>{c.name}</option>)}
          </select>
          <select value={village} onChange={(e) => setVillage(e.target.value)}>
            <option value="">All villages</option>
            {villages.map((v) => <option key={v}>{v}</option>)}
          </select>
          <label>
            <input type="checkbox" checked={flaggedOnly} onChange={(e) => setFlaggedOnly(e.target.checked)} />
            Flagged only
          </label>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Time</th><th>Concern</th><th>Category</th><th>Confidence</th><th>Village</th><th>Status</th></tr>
            </thead>
            <tbody>
              {concerns.length === 0 && (
                <tr><td colSpan="6" className="muted">No concerns match these filters</td></tr>
              )}
              {concerns.map((c) => (
                <tr key={c.id}>
                  <td>{new Date(c.submitted_at).toLocaleString()}</td>
                  <td>{c.text}</td>
                  <td><span className="pill" style={{ background: COLORS[c.category] || '#4f46e5' }}>{c.category}</span></td>
                  <td>{Math.round(c.confidence * 100)}%</td>
                  <td>{c.village || '-'}</td>
                  <td>{c.flagged ? <span className="flag">Review</span> : 'Routed'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  )
}
