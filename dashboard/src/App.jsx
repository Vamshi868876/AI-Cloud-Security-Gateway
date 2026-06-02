import { useState, useEffect, useRef } from 'react'
import { Shield, ShieldAlert, Activity, Server, AlertTriangle, Lock } from 'lucide-react'
import './index.css'

function App() {
  const [events, setEvents] = useState([])
  const [blockedIps, setBlockedIps] = useState(new Set())
  const [isConnected, setIsConnected] = useState(false)
  
  const ws = useRef(null)

  useEffect(() => {
    // Connect to FastAPI WebSocket
    ws.current = new WebSocket('ws://127.0.0.1:8000/ws/dashboard')

    ws.current.onopen = () => setIsConnected(true)
    ws.current.onclose = () => setIsConnected(false)

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.status === 'BLOCKED_WAF') {
        setBlockedIps(prev => new Set([...prev, data.ip]))
      }
      
      setEvents(prev => {
        const newEvents = [data, ...prev]
        return newEvents.slice(0, 100) // Keep last 100 events
      })
      
      if (data.action === 'BLOCKED_BY_AI') {
        setBlockedIps(prev => new Set([...prev, data.ip]))
      }
    }

    return () => {
      ws.current?.close()
    }
  }, [])

  const aiBlocks = events.filter(e => e.action === 'BLOCKED_BY_AI').length
  const wafBlocks = events.filter(e => e.status === 'BLOCKED_WAF').length
  const isUnderAttack = (aiBlocks + wafBlocks) > 0 && events.length > 0 && events[0].action === 'BLOCKED_BY_AI'

  return (
    <div className="dashboard-container">
      <div className="header">
        <div className="header-title">
          <Shield size={28} color="#3b82f6" />
          <h1>Cloud Security API Gateway</h1>
        </div>
        <div className={`status-badge ${isUnderAttack ? 'alert' : ''}`}>
          {isUnderAttack ? <ShieldAlert size={16} /> : <Activity size={16} />}
          {isUnderAttack ? 'ACTIVE ATTACK DETECTED' : 'SYSTEM SECURE'}
        </div>
      </div>

      <div className="content">
        <div className="main-panel">
          <div className="stat-grid">
            <div className="stat-box">
              <div className="stat-label">AI Anomalies Prevented</div>
              <div className="stat-value" style={{ color: 'var(--accent-red)' }}>{aiBlocks}</div>
            </div>
            <div className="stat-box">
              <div className="stat-label">WAF IP Blocks (Rate Limit)</div>
              <div className="stat-value" style={{ color: '#f59e0b' }}>{wafBlocks}</div>
            </div>
          </div>
          
          <div className="panel-header">
            <Server size={14} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
            Live API Traffic Stream
          </div>
          
          <div className="event-list">
            {events.map((ev, idx) => {
              if (ev.status === 'BLOCKED_WAF') {
                return (
                  <div key={idx} className="event-card waf">
                    <div className="event-details">
                      <div className="event-ip"><Lock size={14} color="#f59e0b" style={{display:'inline'}}/> {ev.ip}</div>
                      <div className="event-meta">WAF Auto-Reject: {ev.reason}</div>
                    </div>
                  </div>
                )
              }
              
              const isFraud = ev.action === 'BLOCKED_BY_AI'
              return (
                <div key={idx} className={`event-card ${isFraud ? 'alert' : ''}`}>
                  <div className="event-details">
                    <div className="event-ip">
                      {isFraud && <AlertTriangle size={14} color="#ef4444" style={{display:'inline', marginRight:'4px'}}/>}
                      {ev.ip}
                    </div>
                    <div className="event-meta">
                      <span>User: {ev.user_id}</span>
                      <span>Amount: ${ev.amount}</span>
                      <span>Rate: {ev.req_rate} req/min</span>
                    </div>
                  </div>
                  <div className={`risk-score ${isFraud ? 'high' : 'low'}`}>
                    {ev.risk_score}% Risk
                  </div>
                </div>
              )
            })}
            
            {events.length === 0 && (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                Waiting for API traffic...
              </div>
            )}
          </div>
        </div>
        
        <div className="side-panel">
          <div className="panel-header">
            <Lock size={14} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
            Blacklisted IPs (Redis)
          </div>
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {Array.from(blockedIps).map((ip, idx) => (
              <div key={idx} className="blocked-ip-item">
                <span className="ip">{ip}</span>
                <span className="reason">ML Anomaly</span>
              </div>
            ))}
            {blockedIps.size === 0 && (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                No IPs currently blacklisted.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
