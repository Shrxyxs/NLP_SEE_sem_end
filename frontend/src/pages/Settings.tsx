import { useState } from 'react';

export default function Settings() {
  const [promptId, setPromptId] = useState(1);
  const [autoSave, setAutoSave] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <p>Configure your SahityaAI experience</p>
        </div>
      </div>

      <div style={{ maxWidth: 600 }}>
        {/* Default Prompt */}
        <div className="card" style={{ marginBottom: 20 }}>
          <h3 className="card-title">Default Prompt</h3>
          <p style={{ fontSize: '0.85rem', color: '#6B7280', marginBottom: 12 }}>
            Select which ASAP prompt to use for scoring by default.
          </p>
          <select
            value={promptId}
            onChange={(e) => setPromptId(Number(e.target.value))}
            style={{
              width: '100%', padding: '10px 12px', borderRadius: 8,
              border: '1px solid #E5E1DB', fontSize: '0.9rem',
              background: 'white', color: '#2C2C2C',
            }}
          >
            <option value={1}>Prompt 1 — Persuasive / Argumentative (General)</option>
            <option value={2}>Prompt 2 — Persuasive / Opinion</option>
            <option value={3}>Prompt 3 — Source-Dependent Response</option>
            <option value={4}>Prompt 4 — Source-Dependent Response</option>
            <option value={5}>Prompt 5 — Source-Dependent Response</option>
            <option value={6}>Prompt 6 — Source-Dependent Response</option>
            <option value={7}>Prompt 7 — Narrative / Persuasive</option>
            <option value={8}>Prompt 8 — Narrative</option>
          </select>
        </div>

        {/* Auto-Save */}
        <div className="card" style={{ marginBottom: 20 }}>
          <h3 className="card-title">Auto-Save Essays</h3>
          <p style={{ fontSize: '0.85rem', color: '#6B7280', marginBottom: 12 }}>
            Automatically save evaluated essays to your history.
          </p>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={autoSave}
              onChange={(e) => setAutoSave(e.target.checked)}
              style={{ width: 18, height: 18, accentColor: '#2D6A4F' }}
            />
            <span style={{ fontSize: '0.9rem' }}>Save essays after evaluation</span>
          </label>
        </div>

        {/* Model Info */}
        <div className="card" style={{ marginBottom: 20 }}>
          <h3 className="card-title">Model Information</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div style={{ padding: 12, background: '#FAFAF7', borderRadius: 8 }}>
              <div style={{ fontSize: '0.8rem', color: '#6B7280' }}>English Model</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>BERT-base-uncased</div>
              <div style={{ fontSize: '0.75rem', color: '#2D6A4F' }}>QWK: ~0.75</div>
            </div>
            <div style={{ padding: 12, background: '#FAFAF7', borderRadius: 8 }}>
              <div style={{ fontSize: '0.8rem', color: '#6B7280' }}>Kannada Model</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>MuRIL (planned)</div>
              <div style={{ fontSize: '0.75rem', color: '#C8A951' }}>Not yet trained</div>
            </div>
          </div>
        </div>

        {/* About */}
        <div className="card">
          <h3 className="card-title">About SahityaAI</h3>
          <p style={{ fontSize: '0.85rem', color: '#6B7280', lineHeight: 1.7 }}>
            SahityaAI is a bilingual essay evaluation platform powered by fine-tuned BERT models.
            It provides automated scoring, grammar checking, vocabulary analysis, and personalized
            improvement suggestions for both English and Kannada essays.
          </p>
          <div style={{ marginTop: 12, fontSize: '0.8rem', color: '#9CA3AF' }}>
            Version 1.0.0 · Built with FastAPI + React
          </div>
        </div>
      </div>
    </div>
  );
}
