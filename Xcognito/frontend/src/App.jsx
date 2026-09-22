import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar.jsx';
import ParticipantPortal from './components/ParticipantPortal.jsx';
import OrganizerDashboard from './components/OrganizerDashboard.jsx';
import RulesConfigurator from './components/RulesConfigurator.jsx';
import { Shield, Sparkles } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('participant');
  const [presets, setPresets] = useState([]);
  const [activePreset, setActivePreset] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [rules, setRules] = useState(null);

  // Initial data loading
  useEffect(() => {
    // 1. Fetch system health
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setSystemHealth(data))
      .catch(err => console.error("Health check error:", err));

    // 2. Fetch sample presets
    fetch('/api/samples')
      .then(res => res.json())
      .then(data => setPresets(data))
      .catch(err => console.error("Error loading presets:", err));

    // 3. Fetch rules
    fetch('/api/rules')
      .then(res => res.json())
      .then(data => setRules(data))
      .catch(err => console.error("Error loading rules:", err));
  }, []);

  const handleSelectPreset = (presetKey) => {
    const selected = presets.find(p => p.key === presetKey);
    if (selected) {
      setActivePreset(selected);
      setActiveTab('participant'); // Switch to participant portal to inspect live evaluation
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Navigation & Telemetry Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onSelectPreset={handleSelectPreset}
        presets={presets}
        systemHealth={systemHealth}
      />

      {/* Main View Body */}
      <main style={{ flex: 1 }}>
        {activeTab === 'participant' && (
          <ParticipantPortal
            activePreset={activePreset}
            onVerifyComplete={() => {}}
            rules={rules}
          />
        )}

        {activeTab === 'organizer' && (
          <OrganizerDashboard />
        )}

        {activeTab === 'rules' && (
          <RulesConfigurator
            rules={rules}
            onUpdateRules={(newRules) => setRules(newRules)}
          />
        )}
      </main>

      {/* Platform Footer */}
      <footer style={{
        marginTop: 'auto',
        borderTop: '2px solid var(--color-border-dark)',
        padding: '16px 24px',
        background: '#FFFFFF',
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '24px',
              height: '24px',
              background: 'var(--color-teal)',
              border: '2px solid var(--color-border-dark)',
              borderRadius: '2px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Shield size={14} color="#2D3748" strokeWidth={2.5} />
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--color-text-primary)' }}>
              Hackingly ID-Shield
            </span>
            <span style={{ color: 'var(--color-border-neutral)' }}>•</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', fontWeight: 500 }}>
              AI-Powered Identity & Eligibility Verification
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.75rem' }}>
            <span className="badge badge-teal" style={{ fontSize: '0.68rem', padding: '2px 8px' }}>
              AWS Textract
            </span>
            <span className="badge" style={{ fontSize: '0.68rem', padding: '2px 8px', background: 'var(--color-yellow)', color: '#2D3748' }}>
              Verhoeff
            </span>
            <span className="badge" style={{ fontSize: '0.68rem', padding: '2px 8px', background: 'var(--color-sage)', color: '#2D3748' }}>
              ELA Forensics
            </span>
            <span style={{ color: 'var(--color-text-secondary)', fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Bengaluru 2026
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
