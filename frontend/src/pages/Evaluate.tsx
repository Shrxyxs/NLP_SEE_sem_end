import { useState, useEffect } from 'react';
import { evaluateEssay, type EvaluateResponse } from '../api/client';
import ScoreGauge from '../components/ScoreGauge';

type TabKey = 'scores' | 'grammar' | 'sentences' | 'rewrite' | 'vocab' | 'analysis';

const TABS: { key: TabKey; label: string; icon: string }[] = [
  { key: 'scores', label: 'Scores', icon: '🎯' },
  { key: 'grammar', label: 'Grammar', icon: '📝' },
  { key: 'sentences', label: 'Sentences', icon: '📋' },
  { key: 'rewrite', label: 'Rewrite', icon: '🔄' },
  { key: 'vocab', label: 'Vocab', icon: '📖' },
  { key: 'analysis', label: 'Analysis', icon: '📊' },
];

const TRAIT_LABELS: Record<string, string> = {
  content_ideas: 'Content & Ideas',
  organization: 'Organization',
  language_use: 'Language Use',
  conventions: 'Conventions',
  vocabulary: 'Vocabulary',
};

const TRAIT_COLORS: Record<string, string> = {
  content_ideas: '#2D6A4F',
  organization: '#2D6A4F',
  language_use: '#C8A951',
  conventions: '#B85C4A',
  vocabulary: '#4A7B8C',
};

export default function Evaluate() {
  const [text, setText] = useState('');
  const [language, setLanguage] = useState<'english' | 'kannada'>('english');
  const [promptId, setPromptId] = useState(1);
  const [activeTab, setActiveTab] = useState<TabKey>('scores');
  const [result, setResult] = useState<EvaluateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoSaveStatus, setAutoSaveStatus] = useState('');

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;

  const handleEvaluate = async () => {
    if (text.trim().length < 20) return;
    setLoading(true);
    setAutoSaveStatus('Evaluating...');
    try {
      const res = await evaluateEssay(text, promptId);
      setResult(res);
      if (res.language_detected) {
        setLanguage(res.language_detected as 'english' | 'kannada');
      }
      setAutoSaveStatus('Auto-saved');
      setTimeout(() => setAutoSaveStatus(''), 3000);
    } catch (err) {
      console.error('Evaluation failed:', err);
      setAutoSaveStatus('Error evaluating');
    } finally {
      setLoading(false);
    }
  };

  // Auto-detect language from typing (debounced or simple)
  useEffect(() => {
    const kannadaRegex = /[\u0C80-\u0CFF]/;
    if (kannadaRegex.test(text) && language !== 'kannada') {
      setLanguage('kannada');
    } else if (text.length > 10 && !kannadaRegex.test(text) && language !== 'english') {
      setLanguage('english');
    }
  }, [text]);

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Essay Evaluation</h1>
          <div className="lang-toggle">
            <button
              className={language === 'english' ? 'active' : ''}
              onClick={() => setLanguage('english')}
            >
              T English
            </button>
            <button
              className={language === 'kannada' ? 'active' : ''}
              onClick={() => setLanguage('kannada')}
            >
              ಅ ಕನ್ನಡ
            </button>
          </div>
        </div>
        <div style={{ fontSize: '0.85rem', color: '#6B7280' }}>
          {wordCount} words · {charCount} chars
        </div>
      </div>

      {/* Main Layout */}
      <div className="evaluate-layout">
        {/* Left: Editor */}
        <div className="essay-editor">
          <textarea
            className="essay-textarea"
            placeholder={language === 'english'
              ? "Start writing your essay here...\n\nPaste or type your essay, then click 'Evaluate' to get AI-powered feedback on your writing."
              : "ಇಲ್ಲಿ ನಿಮ್ಮ ಪ್ರಬಂಧವನ್ನು ಬರೆಯಲು ಪ್ರಾರಂಭಿಸಿ..."
            }
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="essay-footer">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ color: language === 'english' ? '#2D6A4F' : '#C8A951' }}>●</span>
              {language === 'english' ? 'English' : 'Kannada'} detected
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              {autoSaveStatus && <span style={{ color: '#9CA3AF' }}>{autoSaveStatus}</span>}
              <select
                value={promptId}
                onChange={(e) => setPromptId(Number(e.target.value))}
                style={{
                  padding: '4px 8px', borderRadius: 6, border: '1px solid #E5E1DB',
                  fontSize: '0.8rem', background: 'white', color: '#2C2C2C'
                }}
              >
                <option value={1}>Prompt 1 (General)</option>
                <option value={2}>Prompt 2</option>
                <option value={3}>Prompt 3</option>
                <option value={4}>Prompt 4</option>
                <option value={5}>Prompt 5</option>
                <option value={6}>Prompt 6</option>
                <option value={7}>Prompt 7</option>
                <option value={8}>Prompt 8</option>
              </select>
              <button
                className="btn btn-primary"
                onClick={handleEvaluate}
                disabled={loading || text.trim().length < 20}
                style={{ opacity: loading || text.trim().length < 20 ? 0.6 : 1 }}
              >
                {loading ? '⏳ Evaluating...' : '✨ Evaluate'}
              </button>
            </div>
          </div>
        </div>

        {/* Right: Results Panel */}
        <div className="results-panel">
          {/* Tabs */}
          <div className="card" style={{ padding: 0 }}>
            <div className="tabs" style={{ padding: '0 12px' }}>
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  className={`tab${activeTab === tab.key ? ' active' : ''}`}
                  onClick={() => setActiveTab(tab.key)}
                >
                  <span className="tab-icon">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </div>

            <div style={{ padding: '20px 24px' }}>
              {/* Scores Tab */}
              {activeTab === 'scores' && (
                <div className="fade-in">
                  {result ? (
                    <>
                      <div style={{ textAlign: 'center', marginBottom: 16 }}>
                        <ScoreGauge score={result.score_100} />
                        <div style={{ marginTop: 12, display: 'flex', justifyContent: 'center', gap: 8 }}>
                          <span className="grade-badge green">Grade {result.grade}</span>
                          <span style={{ fontSize: '0.85rem', color: '#6B7280' }}>
                            Confidence {result.confidence}%
                          </span>
                        </div>
                      </div>

                      <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: 12, marginTop: 20 }}>
                        Trait Scores
                      </h4>
                      {Object.entries(TRAIT_LABELS).map(([key, label]) => {
                        const val = result.traits[key as keyof typeof result.traits] ?? 0;
                        const pct = (val / 20) * 100;
                        const color = TRAIT_COLORS[key] || '#2D6A4F';
                        return (
                          <div className="trait-bar" key={key}>
                            <span className="trait-bar-label">{label}</span>
                            <div className="trait-bar-track">
                              <div
                                className="trait-bar-fill"
                                style={{ width: `${pct}%`, background: color }}
                              />
                            </div>
                            <span className="trait-bar-value">{val} / 20</span>
                          </div>
                        );
                      })}

                      <div style={{
                        marginTop: 20, padding: 16, background: 'rgba(45,106,79,0.04)',
                        borderRadius: 8
                      }}>
                        <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                          🤖 AI Predictions
                        </h4>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: '0.85rem' }}>
                          <span>Human Score Prediction</span>
                          <span style={{ fontWeight: 700 }}>{Math.round(result.score_100)}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                          <span>Grade Prediction</span>
                          <span className="grade-badge green" style={{ padding: '2px 8px', fontSize: '0.75rem' }}>
                            {result.grade}
                          </span>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px 0', color: '#9CA3AF' }}>
                      <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>🎯</div>
                      <div style={{ fontSize: '0.95rem', fontWeight: 500 }}>No results yet</div>
                      <div style={{ fontSize: '0.85rem', marginTop: 4 }}>
                        Write an essay and click Evaluate
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Grammar Tab */}
              {activeTab === 'grammar' && (
                <div className="fade-in">
                  {result && result.grammar_errors.length > 0 ? (
                    <>
                      <div style={{ marginBottom: 12, fontSize: '0.85rem', color: '#6B7280' }}>
                        Found {result.grammar_error_count} issue{result.grammar_error_count !== 1 ? 's' : ''}
                      </div>
                      {result.grammar_errors.map((err, i) => (
                        <div key={i} style={{
                          padding: 12, marginBottom: 8, background: 'rgba(184,92,74,0.04)',
                          borderRadius: 8, borderLeft: '3px solid #B85C4A'
                        }}>
                          <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                            {err.message}
                          </div>
                          <div style={{ fontSize: '0.8rem', color: '#6B7280' }}>
                            {err.context}
                          </div>
                          {err.replacements.length > 0 && (
                            <div style={{ marginTop: 6, fontSize: '0.8rem', color: '#2D6A4F' }}>
                              Suggestion: {err.replacements.join(', ')}
                            </div>
                          )}
                        </div>
                      ))}
                    </>
                  ) : result ? (
                    <div style={{ textAlign: 'center', padding: '40px 0', color: '#2D6A4F' }}>
                      <div style={{ fontSize: '2rem', marginBottom: 8 }}>✅</div>
                      No grammar issues found!
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px 0', color: '#9CA3AF' }}>
                      Evaluate an essay to see grammar feedback
                    </div>
                  )}
                </div>
              )}

              {/* Sentences Tab */}
              {activeTab === 'sentences' && (
                <div className="fade-in">
                  {result ? (
                    <>
                      <div style={{ fontSize: '0.85rem', color: '#6B7280', marginBottom: 12 }}>
                        {result.sentence_count} sentences · {result.paragraph_count} paragraphs
                      </div>
                      <div style={{ padding: 12, background: '#FAFAF7', borderRadius: 8, marginBottom: 12 }}>
                        <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>Avg Sentence Length</div>
                        <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>
                          {result.word_count && result.sentence_count
                            ? Math.round(result.word_count / result.sentence_count)
                            : 0} words
                        </div>
                      </div>
                      <div style={{ padding: 12, background: '#FAFAF7', borderRadius: 8 }}>
                        <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>Reading Level</div>
                        <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>
                          Grade {Math.round(result.readability?.flesch_kincaid_grade ?? 0)}
                        </div>
                        <div style={{ fontSize: '0.8rem', color: '#6B7280', marginTop: 2 }}>
                          Flesch-Kincaid
                        </div>
                      </div>
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px 0', color: '#9CA3AF' }}>
                      Evaluate an essay to see sentence analysis
                    </div>
                  )}
                </div>
              )}

              {/* Rewrite Tab */}
              {activeTab === 'rewrite' && (
                <div className="fade-in" style={{ textAlign: 'center', padding: '40px 0', color: '#9CA3AF' }}>
                  <div style={{ fontSize: '2rem', marginBottom: 8 }}>🔄</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 500 }}>Coming Soon</div>
                  <div style={{ fontSize: '0.85rem', marginTop: 4 }}>
                    AI-powered rewrite suggestions
                  </div>
                </div>
              )}

              {/* Vocab Tab */}
              {activeTab === 'vocab' && (
                <div className="fade-in">
                  {result ? (
                    <>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
                        <div style={{ padding: 12, background: '#FAFAF7', borderRadius: 8, textAlign: 'center' }}>
                          <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{result.unique_words}</div>
                          <div style={{ fontSize: '0.75rem', color: '#6B7280' }}>Unique Words</div>
                        </div>
                        <div style={{ padding: 12, background: '#FAFAF7', borderRadius: 8, textAlign: 'center' }}>
                          <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>
                            {result.word_count > 0 ? Math.round(result.unique_words / result.word_count * 100) : 0}%
                          </div>
                          <div style={{ fontSize: '0.75rem', color: '#6B7280' }}>Lexical Diversity</div>
                        </div>
                      </div>
                      <div className="trait-bar">
                        <span className="trait-bar-label">Vocabulary Score</span>
                        <div className="trait-bar-track">
                          <div
                            className="trait-bar-fill"
                            style={{
                              width: `${(result.traits.vocabulary / 20) * 100}%`,
                              background: '#4A7B8C',
                            }}
                          />
                        </div>
                        <span className="trait-bar-value">{result.traits.vocabulary}/20</span>
                      </div>
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px 0', color: '#9CA3AF' }}>
                      Evaluate an essay to see vocabulary analysis
                    </div>
                  )}
                </div>
              )}

              {/* Analysis Tab */}
              {activeTab === 'analysis' && (
                <div className="fade-in">
                  {result ? (
                    <>
                      {Object.entries({
                        vocabulary_richness: 'Vocabulary Richness',
                        lexical_diversity: 'Lexical Diversity',
                        sentence_complexity: 'Sentence Complexity',
                        readability: 'Readability',
                        repetition_detection: 'Repetition Score',
                      }).map(([key, label]) => {
                        const val = result.analytics?.[key] ?? 0;
                        return (
                          <div className="trait-bar" key={key}>
                            <span className="trait-bar-label">{label}</span>
                            <div className="trait-bar-track">
                              <div
                                className="trait-bar-fill green"
                                style={{ width: `${val}%` }}
                              />
                            </div>
                            <span className="trait-bar-value">{val}%</span>
                          </div>
                        );
                      })}
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px 0', color: '#9CA3AF' }}>
                      Evaluate an essay to see detailed analysis
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
