import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAnalytics, type AnalyticsData } from '../api/client';
import CircularProgress from '../components/CircularProgress';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';

const METRIC_CONFIG: Record<string, { label: string; description: string; icon: string; color: string }> = {
  vocabulary_richness: {
    label: 'Vocabulary Richness',
    description: 'Variety of unique words used',
    icon: '📚',
    color: '#2D6A4F',
  },
  lexical_diversity: {
    label: 'Lexical Diversity',
    description: 'Ratio of unique words to total words',
    icon: '📊',
    color: '#4A7B8C',
  },
  sentence_complexity: {
    label: 'Sentence Complexity',
    description: 'Average sentence length and structure',
    icon: '📝',
    color: '#C8A951',
  },
  paragraph_balance: {
    label: 'Paragraph Balance',
    description: 'Even distribution of ideas across paragraphs',
    icon: '⚖️',
    color: '#2D6A4F',
  },
  readability: {
    label: 'Readability',
    description: 'Ease of reading and comprehension',
    icon: '📖',
    color: '#4A7B8C',
  },
  repetition_detection: {
    label: 'Repetition Detection',
    description: 'Low repetition score is better',
    icon: '🔄',
    color: '#C8A951',
  },
};

export default function Analytics() {
  const navigate = useNavigate();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAnalytics()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  const metrics = data?.metrics ?? {};
  const scoreProgress = data?.score_progress ?? [];

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Writing Analytics</h1>
          <p>Deep insights into your writing patterns and progress</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/evaluate')}>
          ✨ Evaluate New Essay →
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid-3" style={{ marginBottom: 24 }}>
        {Object.entries(METRIC_CONFIG).map(([key, config]) => {
          const value = metrics[key] ?? 0;
          return (
            <div className="metric-card" key={key}>
              <div className="metric-card-info">
                <div
                  className="metric-card-icon"
                  style={{ background: `${config.color}15`, color: config.color }}
                >
                  {config.icon}
                </div>
                <div className="metric-card-value">{value}%</div>
                <div className="metric-card-label">{config.description}</div>
              </div>
              <CircularProgress value={value} size={56} strokeWidth={5} color={config.color} />
            </div>
          );
        })}
      </div>

      {/* Score Progress Over Time */}
      <div className="card">
        <h3 className="card-title">Score Progress Over Time</h3>
        {scoreProgress.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {scoreProgress.map((week, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '80px 1fr 40px 1fr 40px', gap: 12, alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{week.label}</span>
                {/* English bar */}
                <div style={{ height: 20, background: '#E8E4DE', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${week.english}%`,
                    background: '#2D6A4F',
                    borderRadius: 4,
                    transition: 'width 0.6s ease',
                  }} />
                </div>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, textAlign: 'right' }}>
                  {week.english > 0 ? Math.round(week.english) : '—'}
                </span>
                {/* Kannada bar */}
                <div style={{ height: 20, background: '#E8E4DE', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${week.kannada}%`,
                    background: '#8B7D3C',
                    borderRadius: 4,
                    transition: 'width 0.6s ease',
                  }} />
                </div>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, textAlign: 'right' }}>
                  {week.kannada > 0 ? Math.round(week.kannada) : '—'}
                </span>
              </div>
            ))}
            <div style={{ display: 'flex', gap: 24, justifyContent: 'center', marginTop: 8, fontSize: '0.8rem', color: '#6B7280' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: '#2D6A4F', display: 'inline-block' }} />
                English
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: '#8B7D3C', display: 'inline-block' }} />
                Kannada
              </span>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#9CA3AF' }}>
            <div style={{ fontSize: '2rem', marginBottom: 8 }}>📈</div>
            <div>Submit essays to see your progress over time</div>
          </div>
        )}
      </div>

      {loading && (
        <div
          style={{ position: 'fixed', top: 12, right: 12, padding: '8px 16px', background: '#2D6A4F', color: 'white', borderRadius: 8, fontSize: '0.8rem' }}
          className="loading-pulse"
        >
          Loading analytics...
        </div>
      )}
    </div>
  );
}
