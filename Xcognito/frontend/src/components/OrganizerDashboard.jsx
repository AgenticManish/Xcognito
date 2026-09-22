import React, { useState, useEffect } from 'react';
import {
  Users, CheckCircle2, AlertTriangle, ShieldAlert, Search,
  RefreshCw, Layers, ShieldCheck, X as XIcon, Eye, Info,
  Check, ChevronRight, BarChart2
} from 'lucide-react';

/* ─── Mini SVG sparkline ─── */
function Sparkline({ color = '#86BCBD', height = 26, points = [] }) {
  if (!points.length) return null;
  const w = 64, h = height;
  const min = Math.min(...points), max = Math.max(...points);
  const range = max - min || 1;
  const coords = points.map((v, i) => {
    const x = (i / (points.length - 1)) * w;
    const y = h - ((v - min) / range) * (h - 4) - 2;
    return `${x},${y}`;
  }).join(' ');
  return (
    <svg width={w} height={h} className="sparkline" style={{ overflow: 'visible' }}>
      <polyline points={coords} fill="none" stroke={color} strokeWidth="2.5"
        strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={coords.split(' ').pop()?.split(',')[0]} cy={coords.split(' ').pop()?.split(',')[1]}
        r="3.5" fill={color} stroke="#2D3748" strokeWidth="1" />
    </svg>
  );
}

/* ─── Metric card ─── */
function MetricCard({ label, value, sub, icon: Icon, color = 'teal', sparkPoints }) {
  const colorMap = {
    teal:  { border: 'var(--color-teal)', spark: '#86BCBD', iconColor: '#2D3748' },
    green: { border: 'var(--color-sage)', spark: '#A4CE8B', iconColor: '#2D3748' },
    amber: { border: 'var(--color-yellow)', spark: '#F7E49B', iconColor: '#2D3748' },
    red:   { border: 'var(--color-rust)', spark: '#BA5A5A', iconColor: '#2D3748' },
  };
  const c = colorMap[color] || colorMap.teal;

  return (
    <div
      className={`card metric-card ${color}`}
      style={{
        padding: '20px 22px',
        cursor: 'default',
        borderLeft: `6px solid ${c.border}`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div>
          <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, letterSpacing: '0.06em', marginBottom: '6px' }}>
            {label}
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)', lineHeight: 1 }}>
            {value}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
          <div style={{
            background: c.border,
            border: '2px solid var(--color-border-dark)',
            padding: '7px',
            borderRadius: '4px',
            color: '#2D3748',
            boxShadow: 'var(--shadow-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Icon size={18} strokeWidth={2.5} />
          </div>
          <Sparkline color={c.spark} points={sparkPoints || [2, 4, 3, 6, 5, 8, 7]} />
        </div>
      </div>
      {sub && <div style={{ fontSize: '0.76rem', color: 'var(--color-text-secondary)', marginTop: '4px', fontWeight: 600 }}>{sub}</div>}
    </div>
  );
}

/* ─── Side Drawer ─── */
function ForensicsDrawer({ reg, onClose, onDecision, submitting }) {
  const [view, setView] = useState('original');
  const [notes, setNotes] = useState('');

  const badgeClass = reg.decision === 'APPROVED' ? 'badge-approved'
    : reg.decision === 'MANUAL_REVIEW' ? 'badge-review' : 'badge-rejected';

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <div className="drawer-panel">

        {/* Header */}
        <div className="drawer-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <h3 style={{ fontSize: '1.15rem', color: 'var(--color-text-primary)' }}>
                {reg.applicant?.name}
              </h3>
              <span className={`badge ${badgeClass}`}>{reg.decision}</span>
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
              {reg.registration_id} &nbsp;·&nbsp; {new Date(reg.timestamp).toLocaleString()}
            </div>
          </div>
          <button onClick={onClose} className="btn btn-secondary" style={{ padding: '6px 10px' }}>
            <XIcon size={18} strokeWidth={2.5} />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="drawer-body">

          {/* Sybil / collision alert */}
          {reg.duplicate_check?.has_duplicate && (
            <div style={{
              background: reg.duplicate_check?.duplicate_type === 'SYBIL_ID_REUSE'
                ? 'var(--color-rust)' : 'var(--color-yellow)',
              border: '2px solid var(--color-border-dark)',
              color: reg.duplicate_check?.duplicate_type === 'SYBIL_ID_REUSE' ? '#FFFFFF' : '#2D3748',
              padding: '14px 16px',
              borderRadius: '4px',
              marginBottom: '20px',
              boxShadow: 'var(--shadow-sm)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 800, textTransform: 'uppercase', marginBottom: '4px', fontSize: '0.8rem' }}>
                <ShieldAlert size={16} strokeWidth={2.5} />
                CROSS-REGISTRATION COLLISION DETECTED
              </div>
              <div style={{ fontSize: '0.82rem', fontWeight: 600 }}>{reg.duplicate_check?.message}</div>
            </div>
          )}

          {/* Key Metrics grid */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '20px',
          }}>
            <div style={{ background: '#FFFFFF', padding: '14px', borderRadius: '4px', border: '2px solid var(--color-border-dark)', boxShadow: 'var(--shadow-sm)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, marginBottom: '4px' }}>Confidence</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 900, color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
                {reg.confidence_score}%
              </div>
            </div>
            <div style={{ background: '#FFFFFF', padding: '14px', borderRadius: '4px', border: '2px solid var(--color-border-dark)', boxShadow: 'var(--shadow-sm)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, marginBottom: '4px' }}>Tamper Score</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 900, color: reg.forensics?.tamper_score > 50 ? 'var(--color-rust)' : 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
                {reg.forensics?.tamper_score}%
              </div>
            </div>
            <div style={{ background: '#FFFFFF', padding: '14px', borderRadius: '4px', border: '2px solid var(--color-border-dark)', boxShadow: 'var(--shadow-sm)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, marginBottom: '4px' }}>Face Match</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 900, color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
                {reg.face_verification?.similarity_score !== null ? `${reg.face_verification?.similarity_score}%` : 'N/A'}
              </div>
            </div>
          </div>

          {/* Document imaging */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, letterSpacing: '0.05em' }}>
                Document Forensics Imaging
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button onClick={() => setView('original')}
                  className={`btn ${view === 'original' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
                  Original ID
                </button>
                <button onClick={() => setView('ela')}
                  className={`btn ${view === 'ela' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
                  <Layers size={12} strokeWidth={2.5} /> ELA Heatmap
                </button>
              </div>
            </div>
            <div style={{ background: '#FFFFFF', borderRadius: '4px', overflow: 'hidden', maxHeight: '280px', border: '2px solid var(--color-border-dark)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '12px' }}>
              {view === 'original' ? (
                <img src={reg.images?.id_card_preview} alt="Original ID" style={{ maxWidth: '100%', maxHeight: '256px', objectFit: 'contain', border: '1px solid var(--color-border-neutral)' }} />
              ) : (
                <div style={{ position: 'relative', width: '100%', textAlign: 'center' }}>
                  <img src={reg.forensics?.ela_heatmap_url} alt="ELA Heatmap" style={{ maxWidth: '100%', maxHeight: '256px', objectFit: 'contain', border: '1px solid var(--color-border-neutral)' }} />
                  <div style={{ position: 'absolute', bottom: '8px', right: '8px', background: '#FFFFFF', border: '2px solid var(--color-border-dark)', padding: '2px 8px', borderRadius: '2px', fontSize: '0.7rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>
                    High disparity = Altered Pixels
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Face comparison */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '20px' }}>
            <div style={{ background: '#FFFFFF', padding: '14px', borderRadius: '4px', border: '2px solid var(--color-border-dark)', boxShadow: 'var(--shadow-sm)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, marginBottom: '8px' }}>ID Portrait</div>
              {reg.face_verification?.id_face_crop_url
                ? <img src={reg.face_verification.id_face_crop_url} alt="ID Portrait" style={{ width: '80px', height: '80px', borderRadius: '4px', objectFit: 'cover', border: '2px solid var(--color-border-dark)' }} />
                : <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.82rem', fontWeight: 600 }}>No face detected</div>}
            </div>
            <div style={{ background: '#FFFFFF', padding: '14px', borderRadius: '4px', border: '2px solid var(--color-border-dark)', boxShadow: 'var(--shadow-sm)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, marginBottom: '8px' }}>Live Selfie</div>
              {reg.face_verification?.selfie_face_crop_url
                ? <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <img src={reg.face_verification.selfie_face_crop_url} alt="Selfie" style={{ width: '80px', height: '80px', borderRadius: '4px', objectFit: 'cover', border: '2px solid var(--color-border-dark)' }} />
                    <div>
                      <div style={{ fontWeight: 900, color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)', fontSize: '1.2rem' }}>
                        {reg.face_verification?.similarity_score}%
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', fontWeight: 800, textTransform: 'uppercase' }}>similarity</div>
                    </div>
                  </div>
                : <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.82rem', fontWeight: 600 }}>Not provided</div>}
            </div>
          </div>

          {/* System audit trace */}
          <div style={{ marginBottom: '6px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, letterSpacing: '0.05em', marginBottom: '10px' }}>
              System Audit Decision Trace
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {reg.reasons?.map((r, i) => (
                <div key={i} style={{ fontSize: '0.82rem', padding: '8px 12px', background: 'var(--color-bg)', borderRadius: '4px', color: 'var(--color-text-primary)', border: '1px solid var(--color-border-neutral)', fontWeight: 600 }}>
                  {r}
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Action footer */}
        <div className="drawer-footer">
          <div style={{ marginBottom: '10px' }}>
            <input
              type="text"
              placeholder="Operator review rationale..."
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className="form-input"
              style={{ fontSize: '0.84rem' }}
            />
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button disabled={submitting} onClick={() => onDecision('APPROVED', notes)} className="btn btn-success" style={{ flex: 1, padding: '10px' }}>
              <CheckCircle2 size={16} strokeWidth={2.5} /> Approve
            </button>
            <button disabled={submitting} onClick={() => onDecision('MANUAL_REVIEW', notes)} className="btn" style={{ flex: 1, padding: '10px', background: 'var(--color-yellow)', color: '#2D3748' }}>
              <AlertTriangle size={16} strokeWidth={2.5} /> Triage
            </button>
            <button disabled={submitting} onClick={() => onDecision('REJECTED', notes)} className="btn btn-danger" style={{ flex: 1, padding: '10px' }}>
              <XIcon size={16} strokeWidth={2.5} /> Reject
            </button>
          </div>
        </div>

      </div>
    </>
  );
}

/* ─── Main Organizer Dashboard Component ─── */
export default function OrganizerDashboard() {
  const [registrations, setRegistrations] = useState([]);
  const [stats, setStats] = useState({ total_registrations: 0, approved: 0, approved_percent: 0, manual_review_queue: 0, rejected_fraud: 0 });
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [selectedReg, setSelectedReg] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchRegistrations = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/registrations');
      if (res.ok) {
        const data = await res.json();
        setRegistrations(data.registrations || []);
        setStats(data.stats || stats);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchRegistrations(); }, []);

  const handleDecision = async (action, notes) => {
    if (!selectedReg) return;
    setSubmitting(true);
    try {
      const res = await fetch(`/api/registrations/${selectedReg.registration_id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, reviewer_notes: notes })
      });
      if (res.ok) {
        const updated = await res.json();
        setSelectedReg(updated);
        fetchRegistrations();
      }
    } catch (e) { console.error(e); }
    finally { setSubmitting(false); }
  };

  const statusOrder = { ALL: 0, APPROVED: 1, MANUAL_REVIEW: 2, REJECTED: 3 };
  const filterCounts = Object.keys(statusOrder).reduce((acc, k) => {
    acc[k] = k === 'ALL' ? registrations.length : registrations.filter(r => r.decision === k).length;
    return acc;
  }, {});

  const filtered = registrations.filter(r => {
    const q = searchQuery.toLowerCase();
    const match = r.applicant?.name?.toLowerCase().includes(q) ||
                  r.applicant?.email?.toLowerCase().includes(q) ||
                  r.extracted_fields?.id_number?.toLowerCase().includes(q);
    return match && (filterStatus === 'ALL' || r.decision === filterStatus);
  });

  const totalSpark  = [2, 4, 5, 7, 6, 8, 10, 12, stats.total_registrations];
  const appSpark    = [1, 3, 4, 5, 4, 7, 8, 10, stats.approved];
  const reviewSpark = [0, 1, 0, 2, 1, 2, stats.manual_review_queue];
  const rejSpark    = [0, 0, 1, 0, 1, 1, stats.rejected_fraud];

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '16px 24px 60px 24px' }}>

      {/* ── Metric Cards ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '20px' }}>
        <MetricCard label="Total Applicants" value={stats.total_registrations}
          sub="Processed via ID-Shield pipeline" icon={Users} color="teal" sparkPoints={totalSpark} />
        <MetricCard label="Auto-Approved" value={`${stats.approved}`}
          sub={`${stats.approved_percent}% admittance rate`} icon={CheckCircle2} color="green" sparkPoints={appSpark} />
        <MetricCard label="Manual Review Queue" value={stats.manual_review_queue}
          sub="Zero false rejections triage" icon={AlertTriangle} color="amber" sparkPoints={reviewSpark} />
        <MetricCard label="Fraud / Sybil Blocked" value={stats.rejected_fraud}
          sub="Tampering & duplicate IDs stopped" icon={ShieldAlert} color="red" sparkPoints={rejSpark} />
      </div>

      {/* ── Search + Filter bar ── */}
      <div className="card" style={{ padding: '14px 18px', marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: '250px', maxWidth: '400px' }}>
          <Search size={16} color="var(--color-text-secondary)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
          <input
            type="text"
            placeholder="Filter applicant name, email, ID..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="form-input"
            style={{ paddingLeft: '38px', paddingRight: '40px', fontSize: '0.86rem' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ display: 'flex', gap: '4px', background: 'var(--color-bg)', padding: '4px', borderRadius: '4px', border: '2px solid var(--color-border-dark)' }}>
            {['ALL', 'APPROVED', 'MANUAL_REVIEW', 'REJECTED'].map(st => {
              const active = filterStatus === st;
              return (
                <button
                  key={st}
                  onClick={() => setFilterStatus(st)}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6px 12px',
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    borderRadius: '2px',
                    border: active ? '2px solid var(--color-border-dark)' : '2px solid transparent',
                    background: active ? 'var(--color-teal)' : 'transparent',
                    color: 'var(--color-text-primary)',
                    cursor: 'pointer',
                    boxShadow: active ? 'var(--shadow-sm)' : 'none',
                  }}
                >
                  {st.replace(/_/g, ' ')}
                  <span style={{
                    background: active ? '#FFFFFF' : 'var(--color-surface-muted)',
                    border: '1px solid var(--color-border-dark)',
                    padding: '0 5px',
                    borderRadius: '9999px',
                    fontSize: '0.68rem',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 800,
                  }}>
                    {filterCounts[st]}
                  </span>
                </button>
              );
            })}
          </div>
          <button onClick={fetchRegistrations} className="btn btn-secondary" style={{ padding: '8px 12px' }} title="Refresh">
            <RefreshCw size={14} strokeWidth={2.5} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      {/* ── Table ── */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Applicant</th>
              <th>ID Document</th>
              <th>Age &amp; Affiliation</th>
              <th>Forensics / Tamper</th>
              <th>Face Match</th>
              <th>Status &amp; Confidence</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [1, 2, 3].map(i => (
                <tr key={i}>
                  {[1,2,3,4,5,6,7].map(j => (
                    <td key={j} style={{ padding: '16px 18px' }}>
                      <div style={{ height: '14px', width: j === 1 ? '80%' : '60%', background: 'var(--color-surface-muted)', borderRadius: '2px' }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ padding: '48px 20px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                    <BarChart2 size={32} color="var(--color-text-secondary)" strokeWidth={2} />
                    <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>No registrations found matching the criteria.</span>
                  </div>
                </td>
              </tr>
            ) : (
              filtered.map((reg) => {
                const isApp = reg.decision === 'APPROVED';
                const isRev = reg.decision === 'MANUAL_REVIEW';
                const tamperHigh = reg.forensics?.tamper_score > 50;
                const tamperColor = tamperHigh ? 'var(--color-rust)' : 'var(--color-text-primary)';

                return (
                  <tr key={reg.registration_id} onClick={() => setSelectedReg(reg)}>
                    <td>
                      <div style={{ fontWeight: 800, color: 'var(--color-text-primary)', marginBottom: '2px' }}>{reg.applicant?.name}</div>
                      <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.76rem', fontWeight: 500 }}>{reg.applicant?.email}</div>
                    </td>
                    <td>
                      <span className="badge badge-teal" style={{ fontSize: '0.68rem', marginBottom: '4px' }}>
                        {reg.extracted_fields?.document_type?.replace(/_/g, ' ') || 'ID Card'}
                      </span>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--color-text-primary)', fontWeight: 700, marginTop: '2px' }}>
                        {reg.extracted_fields?.id_number || 'N/A'}
                      </div>
                    </td>
                    <td>
                      <div style={{ color: 'var(--color-text-primary)', fontWeight: 700 }}>
                        {reg.extracted_fields?.age ? `${reg.extracted_fields.age} yrs` : 'Unknown'}
                      </div>
                      <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.75rem', fontWeight: 500, maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {reg.extracted_fields?.institution || reg.applicant?.declared_college || 'Pending'}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 900, fontFamily: 'var(--font-mono)', color: tamperColor, fontSize: '0.92rem' }}>
                        {reg.forensics?.tamper_score}%
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>
                        {reg.forensics?.risk_level?.replace(/_/g, ' ')}
                      </div>
                    </td>
                    <td>
                      {reg.face_verification?.similarity_score !== null ? (
                        <div style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-text-primary)' }}>
                          {reg.face_verification?.similarity_score}% match
                        </div>
                      ) : (
                        <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.78rem' }}>—</span>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span className={`badge ${isApp ? 'badge-approved' : isRev ? 'badge-review' : 'badge-rejected'}`}>
                          {reg.decision?.replace(/_/g, ' ')}
                        </span>
                        <div style={{
                          height: '6px',
                          borderRadius: '2px',
                          background: 'var(--color-surface-muted)',
                          border: '1px solid var(--color-border-dark)',
                          overflow: 'hidden',
                        }}>
                          <div style={{
                            width: `${reg.confidence_score}%`,
                            height: '100%',
                            background: isApp ? 'var(--color-sage)' : isRev ? 'var(--color-yellow)' : 'var(--color-rust)',
                          }} />
                        </div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                          {reg.confidence_score}% conf.
                        </div>
                      </div>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        onClick={e => { e.stopPropagation(); setSelectedReg(reg); }}
                        className="btn btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '0.75rem', gap: '4px' }}
                      >
                        <Eye size={13} strokeWidth={2.5} /> Inspect <ChevronRight size={12} strokeWidth={2.5} />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* ── Side Drawer ── */}
      {selectedReg && (
        <ForensicsDrawer
          reg={selectedReg}
          onClose={() => setSelectedReg(null)}
          onDecision={handleDecision}
          submitting={submitting}
        />
      )}

    </div>
  );
}
