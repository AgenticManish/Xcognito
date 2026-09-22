import React, { useState, useEffect } from 'react';
import { Sliders, Save, Check, RefreshCw } from 'lucide-react';

export default function RulesConfigurator({ rules, onUpdateRules }) {
  const [formData, setFormData] = useState(rules || {});
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (rules) {
      setFormData(rules);
    }
  }, [rules]);

  const handleToggleDoc = (docType) => {
    const current = formData.allowed_id_types || [];
    if (current.includes(docType)) {
      setFormData({ ...formData, allowed_id_types: current.filter(d => d !== docType) });
    } else {
      setFormData({ ...formData, allowed_id_types: [...current, docType] });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setSavedSuccess(false);

    try {
      const res = await fetch('/api/rules', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        const updated = await res.json();
        setFormData(updated);
        if (onUpdateRules) onUpdateRules(updated);
        setSavedSuccess(true);
        setTimeout(() => setSavedSuccess(false), 3000);
      }
    } catch (err) {
      alert("Failed to save rules: " + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto', padding: '16px 24px 60px 24px' }}>
      <form onSubmit={handleSubmit} className="card accent-top-teal" style={{ padding: '32px' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', borderBottom: '2px solid var(--color-border-neutral)', paddingBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', color: 'var(--color-text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sliders size={20} color="var(--color-text-primary)" strokeWidth={2.5} />
              Hackathon Eligibility &amp; Anti-Fraud Thresholds
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '4px', fontWeight: 500 }}>
              Tailor eligibility criteria, age gating, document constraints, and triage sensitivity for this event.
            </p>
          </div>

          {savedSuccess && (
            <span className="badge badge-approved" style={{ padding: '6px 14px', fontSize: '0.76rem' }}>
              <Check size={14} strokeWidth={3} /> SAVED LIVE
            </span>
          )}
        </div>

        {/* Hackathon Name */}
        <div className="form-group">
          <label className="form-label">Event Name</label>
          <input
            type="text"
            className="form-input"
            value={formData.hackathon_name || ''}
            onChange={(e) => setFormData({ ...formData, hackathon_name: e.target.value })}
          />
        </div>

        {/* Age Gating */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', margin: '20px 0' }}>
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <label className="form-label" style={{ margin: 0 }}>Minimum Age (Years)</label>
              <strong style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)', fontWeight: 800 }}>
                {formData.min_age || 18} yrs
              </strong>
            </div>
            <input
              type="range"
              min="13"
              max="25"
              value={formData.min_age || 18}
              onChange={(e) => setFormData({ ...formData, min_age: parseInt(e.target.value) })}
              style={{ width: '100%' }}
            />
          </div>

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <label className="form-label" style={{ margin: 0 }}>Maximum Age (Years)</label>
              <strong style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)', fontWeight: 800 }}>
                {formData.max_age || 25} yrs
              </strong>
            </div>
            <input
              type="range"
              min="20"
              max="40"
              value={formData.max_age || 25}
              onChange={(e) => setFormData({ ...formData, max_age: parseInt(e.target.value) })}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        {/* Student Status Switch */}
        <div style={{
          background: 'var(--color-bg)',
          padding: '16px 18px',
          borderRadius: '4px',
          border: '2px solid var(--color-border-dark)',
          boxShadow: 'var(--shadow-sm)',
          marginBottom: '22px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <div style={{ fontWeight: 800, color: 'var(--color-text-primary)', fontSize: '0.92rem', textTransform: 'uppercase' }}>
              Require Student / University Affiliation
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginTop: '2px', fontWeight: 500 }}>
              Enforces applicant to provide an accredited College ID or university proof.
            </div>
          </div>

          <input
            type="checkbox"
            checked={formData.require_student_status || false}
            onChange={(e) => setFormData({ ...formData, require_student_status: e.target.checked })}
            style={{ width: '20px', height: '20px', accentColor: 'var(--color-teal)', cursor: 'pointer' }}
          />
        </div>

        {/* Accepted Document Types */}
        <div className="form-group" style={{ marginBottom: '24px' }}>
          <label className="form-label" style={{ marginBottom: '10px' }}>
            Accepted Indian ID Document Types
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
            {[
              { id: 'AADHAAR_CARD', label: 'Aadhaar Card' },
              { id: 'COLLEGE_ID', label: 'Student College ID' },
              { id: 'PAN_CARD', label: 'PAN Card' },
              { id: 'DRIVING_LICENSE', label: 'Driving License' },
              { id: 'VOTER_ID', label: 'Voter ID (EPIC)' }
            ].map(doc => {
              const isChecked = (formData.allowed_id_types || []).includes(doc.id);
              return (
                <div
                  key={doc.id}
                  onClick={() => handleToggleDoc(doc.id)}
                  style={{
                    padding: '10px 14px',
                    borderRadius: '4px',
                    background: isChecked ? 'var(--color-teal)' : '#FFFFFF',
                    border: '2px solid var(--color-border-dark)',
                    boxShadow: isChecked ? 'var(--shadow-sm)' : 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    color: 'var(--color-text-primary)',
                    transition: 'all 150ms ease',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => {}}
                    style={{ accentColor: '#2D3748', cursor: 'pointer' }}
                  />
                  <span>{doc.label}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* AI & Anti-Fraud Sensitivity Sliders */}
        <div style={{ borderTop: '2px solid var(--color-border-neutral)', paddingTop: '20px', marginBottom: '24px' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--color-text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
            AI Forensic Sensitivity &amp; Triage Controls
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label className="form-label" style={{ margin: 0 }}>Min Face Match Similarity</label>
                <strong style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)', fontWeight: 800 }}>
                  {formData.min_face_match_threshold || 60}%
                </strong>
              </div>
              <input
                type="range"
                min="40"
                max="85"
                value={formData.min_face_match_threshold || 60}
                onChange={(e) => setFormData({ ...formData, min_face_match_threshold: parseFloat(e.target.value) })}
                style={{ width: '100%' }}
              />
            </div>

            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label className="form-label" style={{ margin: 0 }}>Max Tampering ELA Tolerance</label>
                <strong style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)', fontWeight: 800 }}>
                  {formData.max_tamper_threshold || 45}/100
                </strong>
              </div>
              <input
                type="range"
                min="25"
                max="75"
                value={formData.max_tamper_threshold || 45}
                onChange={(e) => setFormData({ ...formData, max_tamper_threshold: parseFloat(e.target.value) })}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={isSaving}
          className="btn btn-primary"
          style={{ width: '100%', padding: '13px', borderRadius: '4px', fontSize: '0.9rem' }}
        >
          {isSaving ? <RefreshCw size={16} className="spin" /> : <Save size={16} strokeWidth={2.5} />}
          Save &amp; Apply Hackathon Eligibility Rules
        </button>

      </form>
    </div>
  );
}
