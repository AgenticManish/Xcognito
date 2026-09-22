import React, { useState, useRef, useEffect } from 'react';
import {
  Upload, Camera, CheckCircle2, AlertTriangle, XCircle, FileText,
  RefreshCw, User, Mail, Calendar, School, ShieldCheck,
  Info, Check, X as XIcon, Image as ImageIcon, Scan
} from 'lucide-react';

/* ─── Circular confidence progress ring ─── */
function ConfidenceRing({ value = 0, color = 'var(--color-teal)', size = 110, strokeWidth = 8 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className="progress-ring-container" style={{ width: size, height: size, flexShrink: 0 }}>
      <svg className="progress-ring-svg" width={size} height={size}>
        <circle
          className="progress-ring-bg"
          cx={size / 2} cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
        />
        <circle
          className="progress-ring-fill"
          cx={size / 2} cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          stroke={color}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="progress-ring-label">
        <span style={{
          fontSize: '1.4rem',
          fontWeight: 800,
          fontFamily: 'var(--font-mono)',
          color: 'var(--color-text-primary)',
          lineHeight: 1,
        }}>
          {value}%
        </span>
        <span style={{ fontSize: '0.62rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 800 }}>
          Score
        </span>
      </div>
    </div>
  );
}

/* ─── Step Progress Bar ─── */
function StepBar({ current }) {
  const steps = ['Applicant Details', 'Upload Documents', 'Verify & Decide'];
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0', width: '100%' }}>
      {steps.map((label, idx) => {
        const num = idx + 1;
        const done   = num < current;
        const active = num === current;
        return (
          <React.Fragment key={num}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', flex: 0 }}>
              <div className={`step-circle ${done ? 'done' : active ? 'active' : ''}`}>
                {done ? <Check size={16} strokeWidth={3} /> : num}
              </div>
              <span className={`step-label ${done ? 'done' : active ? 'active' : ''}`}>{label}</span>
            </div>
            {idx < steps.length - 1 && (
              <div
                className={`step-connector ${done ? 'done' : ''}`}
                style={{ marginTop: '16px', flex: 1, minWidth: '40px' }}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

/* ─── Audit Timeline entry ─── */
function AuditItem({ text, isLast }) {
  const isPass   = text.startsWith('[PASS]');
  const isFail   = text.startsWith('[FAIL]');

  const type   = isPass ? 'pass' : isFail ? 'fail' : 'review';
  const icon   = isPass ? <Check size={12} strokeWidth={3} /> : isFail ? <XIcon size={12} strokeWidth={3} /> : <Info size={12} strokeWidth={2.5} />;
  const label  = text.replace(/^\[.*?\]\s*/, '');

  return (
    <div className="audit-item">
      <div className="audit-line-col">
        <div className={`audit-dot ${type}`}>{icon}</div>
        {!isLast && <div className="audit-connector-line" />}
      </div>
      <div className="audit-content">
        <p className="audit-text">{label}</p>
      </div>
    </div>
  );
}

/* ─── Main Component ─── */
export default function ParticipantPortal({ activePreset, onVerifyComplete, rules }) {
  const [formData, setFormData] = useState({
    name: 'Aarav Sharma',
    email: 'aarav.sharma@iitb.ac.in',
    dob: '2004-08-15',
    college: 'Indian Institute of Technology Bombay'
  });

  const [idFile, setIdFile]         = useState(null);
  const [idPreview, setIdPreview]   = useState(null);
  const [selfieFile, setSelfieFile] = useState(null);
  const [selfiePreview, setSelfiePreview] = useState(null);
  const [webcamActive, setWebcamActive]   = useState(false);

  const [isVerifying, setIsVerifying]         = useState(false);
  const [verificationStep, setVerificationStep] = useState('');
  const [verificationPct, setVerificationPct]   = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError]   = useState(null);

  const videoRef      = useRef(null);
  const canvasRef     = useRef(null);
  const fileInputRef  = useRef(null);
  const selfieInputRef = useRef(null);

  /* Determine current step */
  const currentStep = result ? 3 : idFile ? 2 : 1;

  /* Load preset */
  useEffect(() => {
    if (!activePreset) return;
    setFormData({
      name: activePreset.applicant_name,
      email: activePreset.applicant_email,
      dob: activePreset.declared_dob || '',
      college: activePreset.declared_college || ''
    });
    fetch(`/api/samples/${activePreset.key}/id_card`)
      .then(r => r.blob())
      .then(blob => { setIdFile(new File([blob], `${activePreset.key}_id.jpg`, { type: 'image/jpeg' })); setIdPreview(URL.createObjectURL(blob)); })
      .catch(() => {});
    fetch(`/api/samples/${activePreset.key}/selfie`)
      .then(r => r.blob())
      .then(blob => { setSelfieFile(new File([blob], `${activePreset.key}_selfie.jpg`, { type: 'image/jpeg' })); setSelfiePreview(URL.createObjectURL(blob)); })
      .catch(() => {});
    setResult(null);
    setError(null);
  }, [activePreset]);

  const handleIdUpload = (e) => {
    const file = e.target.files[0];
    if (file) { setIdFile(file); setIdPreview(URL.createObjectURL(file)); setResult(null); }
  };

  const handleSelfieUpload = (e) => {
    const file = e.target.files[0];
    if (file) { setSelfieFile(file); setSelfiePreview(URL.createObjectURL(file)); }
  };

  const startWebcam = async () => {
    try {
      setWebcamActive(true);
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      if (videoRef.current) videoRef.current.srcObject = stream;
    } catch (err) {
      alert('Webcam denied: ' + err.message);
      setWebcamActive(false);
    }
  };

  const captureWebcamSnapshot = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const v = videoRef.current, c = canvasRef.current;
    c.width = v.videoWidth || 640;
    c.height = v.videoHeight || 480;
    c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
    c.toBlob(blob => {
      setSelfieFile(new File([blob], 'live_selfie.jpg', { type: 'image/jpeg' }));
      setSelfiePreview(URL.createObjectURL(blob));
      if (v.srcObject) v.srcObject.getTracks().forEach(t => t.stop());
      setWebcamActive(false);
    }, 'image/jpeg', 0.95);
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    if (!idFile) { setError('Please upload an ID card image before submitting.'); return; }
    setIsVerifying(true);
    setError(null);
    setResult(null);
    setVerificationPct(0);

    const steps = [
      'Analyzing document sharpness & glare...',
      'Extracting OCR fields via AI pipeline...',
      'Running Error Level Analysis (ELA)...',
      'Validating Verhoeff checksum...',
      'Comparing face against live selfie...',
      'Scanning cross-registration duplicate graph...',
      'Computing eligibility & confidence score...',
    ];

    let idx = 0;
    setVerificationStep(steps[0]);
    const timer = setInterval(() => {
      idx++;
      if (idx < steps.length) {
        setVerificationStep(steps[idx]);
        setVerificationPct(Math.round((idx / steps.length) * 90));
      }
    }, 430);

    try {
      const fd = new FormData();
      fd.append('applicant_name', formData.name);
      fd.append('applicant_email', formData.email);
      fd.append('declared_dob', formData.dob);
      fd.append('declared_college', formData.college);
      fd.append('id_card_file', idFile);
      if (selfieFile) fd.append('selfie_file', selfieFile);

      const res = await fetch('/api/verify', { method: 'POST', body: fd });
      clearInterval(timer);
      setVerificationPct(100);

      if (!res.ok) { const j = await res.json(); throw new Error(j.detail || 'Verification failed'); }
      const data = await res.json();
      setResult(data);
      if (onVerifyComplete) onVerifyComplete(data);
    } catch (err) {
      clearInterval(timer);
      setError(err.message);
    } finally {
      setIsVerifying(false);
    }
  };

  /* Decision theme helpers */
  const decisionTheme = result?.decision === 'APPROVED'
    ? { bg: 'var(--color-sage)', text: '#2D3748', border: 'var(--color-border-dark)', icon: <CheckCircle2 size={32} strokeWidth={2.5} /> }
    : result?.decision === 'MANUAL_REVIEW'
    ? { bg: 'var(--color-yellow)', text: '#2D3748', border: 'var(--color-border-dark)', icon: <AlertTriangle size={32} strokeWidth={2.5} /> }
    : { bg: 'var(--color-rust)', text: '#FFFFFF', border: 'var(--color-border-dark)', icon: <XCircle size={32} strokeWidth={2.5} /> };

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '16px 24px 60px 24px' }}>

      {/* ── Hero Banner ── */}
      <div
        className="card accent-edge-teal"
        style={{
          padding: '24px 28px',
          marginBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span className="badge badge-teal">REGISTRATION GATEWAY</span>
              <span style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                EVENT ID: ABC-BLR-2026
              </span>
            </div>
            <h1 style={{ fontSize: '1.6rem', color: 'var(--color-text-primary)', marginBottom: '6px' }}>
              AI Build Challenge Bengaluru 2026
            </h1>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem', maxWidth: '720px', lineHeight: 1.5, fontWeight: 500 }}>
              Identity &amp; Eligibility verification gateway. Applicants must provide a valid Indian ID
              (Aadhaar, Student College ID, or PAN) to verify age requirements (18–25) and bona fide student status.
            </p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Active Constraints
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              <span className="badge badge-teal" style={{ fontSize: '0.7rem' }}>Age: {rules?.min_age || 18}–{rules?.max_age || 25} yrs</span>
              <span className="badge badge-approved" style={{ fontSize: '0.7rem' }}>Student: {rules?.require_student_status ? 'Required' : 'Optional'}</span>
              <span className="badge badge-review" style={{ fontSize: '0.7rem' }}>Verhoeff Dihedral Check</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Step Bar ── */}
      <div className="card" style={{ padding: '16px 28px', marginBottom: '20px' }}>
        <StepBar current={currentStep} />
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: result ? '1.05fr 0.95fr' : '1.15fr 0.85fr',
        gap: '20px',
        alignItems: 'start',
      }}>

        {/* ── Left: Form ── */}
        <form onSubmit={handleVerify} className="card" style={{ padding: '24px 28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px', paddingBottom: '14px', borderBottom: '2px solid var(--color-border-neutral)' }}>
            <div style={{
              background: 'var(--color-teal)',
              padding: '8px',
              borderRadius: '4px',
              border: '2px solid var(--color-border-dark)',
              color: 'var(--color-text-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'var(--shadow-sm)',
            }}>
              <FileText size={18} strokeWidth={2.5} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.05rem', color: 'var(--color-text-primary)' }}>Applicant Credentials</h2>
              <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', fontWeight: 500 }}>
                Provide identity data and upload clear document scans for AI validation
              </p>
            </div>
          </div>

          {/* Error alert */}
          {error && (
            <div style={{
              background: 'var(--color-rust)',
              border: '2px solid var(--color-border-dark)',
              color: '#FFFFFF',
              padding: '12px 16px',
              borderRadius: '4px',
              marginBottom: '20px',
              fontSize: '0.85rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              boxShadow: 'var(--shadow-sm)',
            }}>
              <AlertTriangle size={18} strokeWidth={2.5} />
              <span>{error}</span>
            </div>
          )}

          {/* Form fields */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label"><User size={12} strokeWidth={2.5} /> Full Name</label>
              <input type="text" required className="form-input" value={formData.name}
                onChange={e => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g. Aarav Sharma" />
            </div>
            <div className="form-group">
              <label className="form-label"><Mail size={12} strokeWidth={2.5} /> Email Address</label>
              <input type="email" required className="form-input" value={formData.email}
                onChange={e => setFormData({ ...formData, email: e.target.value })}
                placeholder="candidate@university.edu" />
            </div>
            <div className="form-group">
              <label className="form-label"><Calendar size={12} strokeWidth={2.5} /> Date of Birth</label>
              <input type="date" required className="form-input" value={formData.dob}
                onChange={e => setFormData({ ...formData, dob: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label"><School size={12} strokeWidth={2.5} /> University / College</label>
              <input type="text" className="form-input" value={formData.college}
                onChange={e => setFormData({ ...formData, college: e.target.value })}
                placeholder="IIT Bombay / BITS Pilani" />
            </div>
          </div>

          <div style={{ height: '2px', background: 'var(--color-border-neutral)', margin: '16px 0' }} />

          {/* ── ID Document Upload ── */}
          <div className="form-group" style={{ marginBottom: '18px' }}>
            <label className="form-label" style={{ marginBottom: '8px' }}>
              <Scan size={12} strokeWidth={2.5} />
              Identity Proof Document (Aadhaar / College ID / PAN) *
            </label>
            <input type="file" ref={fileInputRef} onChange={handleIdUpload}
              accept="image/jpeg,image/png,image/webp" style={{ display: 'none' }} />
            <div
              onClick={() => fileInputRef.current?.click()}
              className={`upload-zone ${idPreview ? 'has-file' : ''}`}
              style={{ padding: idPreview ? '12px' : '30px 20px', textAlign: 'center' }}
            >
              {idPreview ? (
                <div>
                  <img src={idPreview} alt="Uploaded ID"
                    style={{ maxHeight: '190px', maxWidth: '100%', borderRadius: '4px', border: '2px solid var(--color-border-dark)', objectFit: 'contain' }} />
                  <div style={{ marginTop: '10px', fontSize: '0.8rem', color: 'var(--color-text-primary)', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                    <RefreshCw size={13} strokeWidth={2.5} /> Click to replace document
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{
                    width: '46px',
                    height: '46px',
                    borderRadius: '4px',
                    background: 'var(--color-teal)',
                    border: '2px solid var(--color-border-dark)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 10px',
                    boxShadow: 'var(--shadow-sm)',
                  }}>
                    <Upload size={22} color="#2D3748" strokeWidth={2.5} />
                  </div>
                  <div style={{ fontWeight: 800, color: 'var(--color-text-primary)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.03em', marginBottom: '4px' }}>
                    Click or drag &amp; drop ID document
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', fontWeight: 500 }}>
                    Aadhaar, Student College ID, PAN Card — JPEG, PNG
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* ── Selfie / Live photo ── */}
          <div className="form-group" style={{ marginBottom: '22px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label className="form-label" style={{ margin: 0 }}>
                <Camera size={12} strokeWidth={2.5} /> Live Selfie &amp; Face Match <span style={{ color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'none' }}>(Recommended)</span>
              </label>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button type="button"
                  onClick={webcamActive ? captureWebcamSnapshot : startWebcam}
                  className={`btn ${webcamActive ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
                  <Camera size={12} strokeWidth={2.5} />{webcamActive ? '📸 Snap' : 'Open Cam'}
                </button>
                <button type="button" onClick={() => selfieInputRef.current?.click()}
                  className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
                  <ImageIcon size={12} strokeWidth={2.5} /> Upload
                </button>
                <input type="file" ref={selfieInputRef} onChange={handleSelfieUpload}
                  accept="image/jpeg,image/png,image/webp" style={{ display: 'none' }} />
              </div>
            </div>

            {webcamActive && (
              <div style={{ borderRadius: '4px', overflow: 'hidden', background: '#000', border: '2px solid var(--color-border-dark)', marginBottom: '10px' }}>
                <video ref={videoRef} autoPlay playsInline style={{ width: '100%', maxHeight: '200px', objectFit: 'cover', display: 'block' }} />
                <canvas ref={canvasRef} style={{ display: 'none' }} />
              </div>
            )}

            {selfiePreview && !webcamActive && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: '14px',
                background: '#FFFFFF',
                padding: '10px 14px', borderRadius: '4px',
                border: '2px solid var(--color-border-dark)',
                boxShadow: 'var(--shadow-sm)',
              }}>
                <img src={selfiePreview} alt="Selfie"
                  style={{ width: '50px', height: '50px', borderRadius: '4px', objectFit: 'cover', border: '2px solid var(--color-border-dark)' }} />
                <div style={{ fontSize: '0.84rem' }}>
                  <div style={{ fontWeight: 800, color: 'var(--color-text-primary)', textTransform: 'uppercase', fontSize: '0.8rem' }}>Selfie Captured</div>
                  <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.75rem', marginTop: '2px', fontWeight: 500 }}>
                    Biometric cross-match with ID portrait enabled
                  </div>
                </div>
                <div style={{ marginLeft: 'auto', background: 'var(--color-sage)', border: '2px solid var(--color-border-dark)', borderRadius: '9999px', padding: '3px 8px', fontSize: '0.68rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Check size={12} strokeWidth={3} /> READY
                </div>
              </div>
            )}
          </div>

          {/* ── Submit Button ── */}
          <button
            type="submit"
            disabled={isVerifying || !idFile}
            className="btn btn-primary"
            style={{ width: '100%', padding: '13px', fontSize: '0.92rem', borderRadius: '4px' }}
          >
            {isVerifying ? (
              <><RefreshCw size={16} className="spin" /> Evaluating Verification Engine...</>
            ) : (
              <><ShieldCheck size={18} strokeWidth={2.5} /> Run AI Identity &amp; Eligibility Check</>
            )}
          </button>

          {/* Progress bar during verification */}
          {isVerifying && (
            <div style={{ marginTop: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.78rem', fontWeight: 700 }}>
                <span style={{ color: 'var(--color-text-primary)' }}>{verificationStep}</span>
                <span style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}>{verificationPct}%</span>
              </div>
              <div style={{ height: '8px', borderRadius: '2px', background: 'var(--color-surface-muted)', border: '1px solid var(--color-border-dark)', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${verificationPct}%`,
                  background: 'var(--color-teal)',
                  transition: 'width 0.4s ease',
                }} />
              </div>
            </div>
          )}
        </form>

        {/* ── Right: Result / Information Card ── */}
        <div>
          {result ? (
            <div className="card" style={{ padding: '0', overflow: 'hidden' }}>

              {/* Decision Hero Banner */}
              <div style={{
                background: decisionTheme.bg,
                color: decisionTheme.text,
                padding: '20px 24px',
                borderBottom: '2px solid var(--color-border-dark)',
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
              }}>
                <div style={{
                  background: '#FFFFFF',
                  border: '2px solid var(--color-border-dark)',
                  padding: '10px',
                  borderRadius: '4px',
                  boxShadow: 'var(--shadow-sm)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--color-text-primary)',
                  flexShrink: 0
                }}>
                  {decisionTheme.icon}
                </div>
                <div style={{ flex: 1 }}>
                  <span className="badge" style={{
                    background: '#FFFFFF',
                    color: 'var(--color-text-primary)',
                    fontSize: '0.72rem',
                    marginBottom: '4px',
                  }}>
                    {result.decision === 'APPROVED' ? 'ELIGIBLE • ADMITTED' :
                     result.decision === 'MANUAL_REVIEW' ? 'FLAGGED • MANUAL TRIAGE' : 'INELIGIBLE • REJECTED'}
                  </span>
                  <div style={{ fontSize: '1.05rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.02em', marginTop: '4px', lineHeight: 1.25 }}>
                    {result.summary}
                  </div>
                </div>
                {/* Circular ring */}
                <ConfidenceRing value={result.confidence_score} color="var(--color-border-dark)" size={92} strokeWidth={8} />
              </div>

              <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>

                {/* Extracted fields */}
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, letterSpacing: '0.05em', marginBottom: '10px' }}>
                    AI-Extracted Credential Metadata
                  </div>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '10px',
                    background: 'var(--color-bg)',
                    padding: '14px',
                    borderRadius: '4px',
                    border: '2px solid var(--color-border-dark)',
                  }}>
                    <div>
                      <div style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Document Type</div>
                      <div style={{ fontWeight: 700, fontSize: '0.86rem', color: 'var(--color-text-primary)' }}>
                        {result.extracted_fields?.document_type?.replace(/_/g, ' ') || '—'}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Name on ID</div>
                      <div style={{ fontWeight: 700, fontSize: '0.86rem', color: 'var(--color-text-primary)' }}>
                        {result.extracted_fields?.name || 'Uncertain'}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>DOB / Age</div>
                      <div style={{ fontWeight: 700, fontSize: '0.86rem', color: 'var(--color-text-primary)' }}>
                        {result.extracted_fields?.dob || 'N/A'}
                        {result.extracted_fields?.age ? ` (${result.extracted_fields.age} yrs)` : ''}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>ID Number</div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '0.86rem', color: 'var(--color-text-primary)' }}>
                        {result.extracted_fields?.id_number || 'Detected'}
                      </div>
                    </div>
                    {result.extracted_fields?.institution && (
                      <div style={{ gridColumn: 'span 2' }}>
                        <div style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Institution</div>
                        <div style={{ fontWeight: 700, fontSize: '0.86rem', color: 'var(--color-text-primary)' }}>
                          {result.extracted_fields.institution}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Audit trail */}
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, letterSpacing: '0.05em', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Info size={14} strokeWidth={2.5} /> Verification Audit Trail
                  </div>
                  <div className="audit-timeline">
                    {result.reasons?.map((reason, idx) => (
                      <AuditItem key={idx} text={reason} isLast={idx === result.reasons.length - 1} />
                    ))}
                  </div>
                </div>

                {/* Forensic thumbnails */}
                {(result.forensics?.ela_heatmap_url || result.face_verification?.id_face_crop_url) && (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, letterSpacing: '0.05em', marginBottom: '10px' }}>
                      Visual Forensics &amp; Biometric Match
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      {result.forensics?.ela_heatmap_url && (
                        <div style={{ border: '2px solid var(--color-border-dark)', borderRadius: '4px', padding: '8px', background: 'var(--color-bg)' }}>
                          <div style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, marginBottom: '6px' }}>ELA Tamper Heatmap</div>
                          <img src={result.forensics.ela_heatmap_url} alt="ELA"
                            style={{ width: '100%', height: '90px', objectFit: 'cover', borderRadius: '2px', border: '1px solid var(--color-border-dark)' }} />
                        </div>
                      )}
                      {result.face_verification?.id_face_crop_url && (
                        <div style={{ border: '2px solid var(--color-border-dark)', borderRadius: '4px', padding: '8px', background: 'var(--color-bg)' }}>
                          <div style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, marginBottom: '6px' }}>Extracted Portrait</div>
                          <img src={result.face_verification.id_face_crop_url} alt="Portrait"
                            style={{ width: '100%', height: '90px', objectFit: 'cover', borderRadius: '2px', border: '1px solid var(--color-border-dark)' }} />
                        </div>
                      )}
                    </div>
                  </div>
                )}

              </div>
            </div>
          ) : (
            /* Empty state */
            <div className="card" style={{ padding: '36px 28px', textAlign: 'center' }}>
              <div style={{
                width: '60px', height: '60px', borderRadius: '4px',
                background: 'var(--color-teal)',
                border: '2px solid var(--color-border-dark)',
                boxShadow: 'var(--shadow-sm)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                margin: '0 auto 16px',
              }}>
                <ShieldCheck size={30} color="#2D3748" strokeWidth={2.5} />
              </div>
              <h3 style={{ fontSize: '1.15rem', color: 'var(--color-text-primary)', marginBottom: '6px' }}>
                Automated Verification Engine
              </h3>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.88rem', lineHeight: 1.5, marginBottom: '22px', maxWidth: '340px', margin: '0 auto 22px', fontWeight: 500 }}>
                Upload an applicant document or pick a scenario from the top navbar to run the verification engine.
              </p>
              <div style={{
                background: 'var(--color-bg)',
                borderRadius: '4px',
                padding: '16px 18px',
                textAlign: 'left',
                border: '2px solid var(--color-border-dark)',
                boxShadow: 'var(--shadow-sm)',
              }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 800, marginBottom: '10px', letterSpacing: '0.05em' }}>
                  Automated Integrity Checks
                </div>
                <ul style={{ fontSize: '0.82rem', color: 'var(--color-text-primary)', paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '8px', fontWeight: 600 }}>
                  <li><strong>AWS Textract + Local OCR</strong> — Instant field extraction</li>
                  <li><strong>UIDAI Checksum</strong> — Verhoeff dihedral group validation</li>
                  <li><strong>Digital Forensics</strong> — Error Level Analysis (ELA) for image tampering</li>
                  <li><strong>Sybil Defense</strong> — Cross-registration duplicate ID graph tracking</li>
                  <li><strong>Biometric Match</strong> — Card portrait vs live selfie cross-check</li>
                </ul>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
