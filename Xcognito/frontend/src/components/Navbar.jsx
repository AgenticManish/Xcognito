import React from 'react';
import { Shield, LayoutDashboard, UserCheck, Settings, Cpu, Zap } from 'lucide-react';

const TABS = [
  { key: 'participant', label: 'Participant Portal', icon: UserCheck },
  { key: 'organizer',   label: 'Operator Command', icon: LayoutDashboard },
  { key: 'rules',       label: 'Hackathon Rules',  icon: Settings },
];

export default function Navbar({ activeTab, setActiveTab, onSelectPreset, presets, systemHealth }) {
  const isActive = (key) => activeTab === key;
  const engineName = systemHealth?.engines?.aws_textract === 'ACTIVE' ? 'AWS Textract' : 'Local AI';

  return (
    <header
      style={{
        margin: '16px 24px 8px 24px',
        padding: '12px 20px',
        background: '#FFFFFF',
        border: '2px solid var(--color-border-dark)',
        borderRadius: '4px',
        boxShadow: 'var(--shadow-md)',
        position: 'sticky',
        top: '12px',
        zIndex: 50,
      }}
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        flexWrap: 'wrap',
      }}>

        {/* ── Brand ── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '4px',
            background: 'var(--color-teal)',
            border: '2px solid var(--color-border-dark)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-sm)',
            flexShrink: 0,
          }}>
            <Shield size={20} color="#2D3748" strokeWidth={2.5} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{
                fontSize: '1.05rem',
                fontWeight: 900,
                letterSpacing: '-0.02em',
                fontFamily: 'var(--font-sans)',
                color: 'var(--color-text-primary)',
                textTransform: 'uppercase',
              }}>
                Hackingly
              </span>
              <span className="badge badge-teal" style={{ fontSize: '0.65rem', padding: '2px 8px' }}>
                ID-SHIELD
              </span>
              <span style={{
                fontSize: '0.65rem',
                color: 'var(--color-text-secondary)',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                background: 'var(--color-bg)',
                border: '1px solid var(--color-border-neutral)',
                borderRadius: '2px',
                padding: '1px 5px',
              }}>
                v1.2
              </span>
            </div>
            <p style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', fontWeight: 600, marginTop: '1px' }}>
              AI Identity & Eligibility Verification
            </p>
          </div>
        </div>

        {/* ── Tab Switcher ── */}
        <nav style={{
          display: 'flex',
          background: 'var(--color-bg)',
          padding: '4px',
          borderRadius: '4px',
          border: '2px solid var(--color-border-dark)',
          gap: '4px',
        }}>
          {TABS.map(({ key, label, icon: Icon }) => {
            const active = isActive(key);
            return (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 14px',
                  borderRadius: '2px',
                  border: active ? '2px solid var(--color-border-dark)' : '2px solid transparent',
                  background: active ? 'var(--color-teal)' : 'transparent',
                  color: 'var(--color-text-primary)',
                  fontFamily: 'var(--font-sans)',
                  fontWeight: active ? 800 : 600,
                  fontSize: '0.8rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.03em',
                  cursor: 'pointer',
                  boxShadow: active ? 'var(--shadow-sm)' : 'none',
                  transition: 'background-color 150ms ease, transform 150ms ease',
                  whiteSpace: 'nowrap',
                }}
              >
                <Icon size={15} strokeWidth={active ? 2.5 : 2} color="var(--color-text-primary)" />
                {label}
              </button>
            );
          })}
        </nav>

        {/* ── Right: Telemetry & Presets ── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
          {/* Engine Status Chip */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: '#FFFFFF',
            border: '2px solid var(--color-border-dark)',
            padding: '6px 12px',
            borderRadius: '4px',
            boxShadow: 'var(--shadow-sm)',
            fontSize: '0.75rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}>
            <div className="status-dot approved" />
            <Cpu size={14} color="var(--color-text-primary)" />
            <span style={{ color: 'var(--color-text-secondary)' }}>OCR:</span>
            <strong style={{ color: 'var(--color-text-primary)' }}>{engineName}</strong>
          </div>

          {/* Quick Demo Scenario Selector */}
          {presets && presets.length > 0 && (
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <Zap size={14} color="var(--color-text-primary)" style={{ position: 'absolute', left: '10px', pointerEvents: 'none', zIndex: 1 }} />
              <select
                onChange={(e) => {
                  if (e.target.value) { onSelectPreset(e.target.value); e.target.value = ''; }
                }}
                defaultValue=""
                className="form-select"
                style={{
                  padding: '7px 32px 7px 28px',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  border: '2px solid var(--color-border-dark)',
                  background: '#FFFFFF',
                  borderRadius: '4px',
                  boxShadow: 'var(--shadow-sm)',
                  minWidth: '200px',
                  cursor: 'pointer',
                  color: 'var(--color-text-primary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.03em',
                }}
              >
                <option value="" disabled>Demo Scenarios...</option>
                {presets.map(p => (
                  <option key={p.key} value={p.key}>{p.title} ({p.expected_decision})</option>
                ))}
              </select>
            </div>
          )}
        </div>

      </div>
    </header>
  );
}
