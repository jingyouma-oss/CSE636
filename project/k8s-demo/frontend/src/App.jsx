import { useEffect, useState } from 'react'

export default function App() {
  const [items, setItems] = useState([])
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  async function load() {
    try {
      const res = await fetch('/api/items')
      const data = await res.json()
      setItems(data.items || [])
      setError('')
    } catch {
      setError('Could not reach the backend (is the API up?)')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function add(e) {
    e.preventDefault()
    if (!name.trim()) return
    await fetch('/api/items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name.trim() }),
    })
    setName('')
    load()
  }

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 480, margin: '2rem auto', padding: '0 1rem' }}>
      <h1>3-Tier Demo on Kubernetes</h1>
      <p>React (frontend) → FastAPI (backend) → Postgres (database)</p>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      <form onSubmit={add} style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New item"
          style={{ flex: 1, padding: '0.4rem' }}
        />
        <button type="submit">Add</button>
      </form>
      <ul>
        {items.map((i) => (
          <li key={i.id}>{i.name}</li>
        ))}
      </ul>
    </main>
  )
}
