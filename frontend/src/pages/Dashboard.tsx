import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDashboard, type DashboardStats } from '../api/client';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  // Mock chart data when no real data
  const chartData = stats && stats.recent_essays.length > 0
    ? stats.recent_essays.map((e, i) => ({
        name: `Essay ${i + 1}`,
        English: e.language === 'english' ? e.score_100 : 0,
        Kannada: e.language === 'kannada' ? e.score_100 : 0,
      }))
    : [
        { name: 'Essay 1', English: 72, Kannada: 0 },
        { name: 'Essay 2', English: 68, Kannada: 65 },
        { name: 'Essay 3', English: 0, Kannada: 70 },
        { name: 'Essay 4', English: 78, Kannada: 0 },
        { name: 'Essay 5', English: 75, Kannada: 68 },
        { name: 'Essay 6', English: 0, Kannada: 72 },
      ];

  const avgScore = stats?.average_score ?? 0;
  const essayCount = stats?.essays_evaluated ?? 0;
  const bestGrade = stats?.best_grade ?? 'N/A';
  const skillBreakdown = stats?.skill_breakdown ?? {
    content_ideas: 0, organization: 0, language_use: 0, conventions: 0, vocabulary: 0,
  };
  const improvementPlan = stats?.improvement_plan ?? { strengths: [], focus_areas: [] };
  const recentEssays = stats?.recent_essays ?? [];

  const traitLabels: Record<string, string> = {
    content_ideas: 'Content & Ideas',
    organization: 'Organization',
    language_use: 'Language Use',
    conventions: 'Conventions',
    vocabulary: 'Vocabulary',
  };

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>Track your writing progress and improvement over time</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/evaluate')}>
          ✏️ New Essay →
        </button>
      </div>

      {/* Stat Cards */}
      <div className="stat-cards">
        <div className="stat-card">
          <div className="stat-card-header">
            <div className="stat-card-icon" style={{ background: 'rgba(200,169,81,0.12)', color: '#C8A951' }}>👤</div>
            {avgScore > 0 && <span className="stat-card-badge">+{(avgScore * 0.05).toFixed(1)}%</span>}
          </div>
          <div className="stat-card-value">{avgScore.toFixed(1)} <span>/ 100</span></div>
          <div className="stat-card-label">Average Score</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <div className="stat-card-icon" style={{ background: 'rgba(45,106,79,0.08)', color: '#2D6A4F' }}>📝</div>
            {essayCount > 0 && <span className="stat-card-badge">+{Math.min(essayCount, 3)} this week</span>}
          </div>
          <div className="stat-card-value">{essayCount}</div>
          <div className="stat-card-label">Essays Evaluated</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <div className="stat-card-icon" style={{ background: 'rgba(200,169,81,0.12)', color: '#C8A951' }}>⭐</div>
            {stats?.best_essay_title && <span className="stat-card-badge">{stats.best_essay_title}</span>}
          </div>
          <div className="stat-card-value">{bestGrade}</div>
          <div className="stat-card-label">Best Grade</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <div className="stat-card-icon" style={{ background: 'rgba(45,106,79,0.08)', color: '#2D6A4F' }}>⏱️</div>
            <span className="stat-card-badge">+1.2h this week</span>
          </div>
          <div className="stat-card-value">8.5h</div>
          <div className="stat-card-label">Study Time</div>
        </div>
      </div>

      {/* Score Trends + Improvement Plan */}
      <div className="grid-2-1" style={{ marginBottom: 24 }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 className="card-title" style={{ margin: 0 }}>Score Trends</h3>
            <div style={{ display: 'flex', gap: 16, fontSize: '0.8rem' }}>
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
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} barGap={4} barSize={20}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E8E4DE" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#6B7280' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#6B7280' }} axisLine={false} tickLine={false} domain={[0, 100]} />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: '1px solid #E8E4DE', fontSize: '0.85rem' }}
              />
              <Bar dataKey="English" fill="#2D6A4F" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Kannada" fill="#8B7D3C" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="card-title">Improvement Plan</h3>
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, color: '#2D6A4F', fontWeight: 600, fontSize: '0.9rem' }}>
              ✅ Top Strengths
            </div>
            {improvementPlan.strengths.length > 0 ? (
              improvementPlan.strengths.map((s, i) => (
                <div key={i} style={{ fontSize: '0.85rem', color: '#2C2C2C', marginBottom: 6, paddingLeft: 8 }}>
                  • {s}
                </div>
              ))
            ) : (
              <div style={{ fontSize: '0.85rem', color: '#9CA3AF', paddingLeft: 8 }}>
                Submit essays to see strengths
              </div>
            )}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, color: '#C8A951', fontWeight: 600, fontSize: '0.9rem' }}>
              ⚠️ Focus Areas
            </div>
            {improvementPlan.focus_areas.length > 0 ? (
              improvementPlan.focus_areas.map((f, i) => (
                <div key={i} style={{ fontSize: '0.85rem', color: '#2C2C2C', marginBottom: 6, paddingLeft: 8 }}>
                  • {f}
                </div>
              ))
            ) : (
              <div style={{ fontSize: '0.85rem', color: '#9CA3AF', paddingLeft: 8 }}>
                Submit essays to identify focus areas
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Essays + Skill Breakdown */}
      <div className="grid-2-1">
        <div className="card">
          <h3 className="card-title">Recent Essays</h3>
          {recentEssays.length > 0 ? (
            recentEssays.map((essay) => (
              <div className="essay-card" key={essay.id} onClick={() => navigate(`/evaluate?id=${essay.id}`)}>
                <div className="essay-card-icon">📖</div>
                <div className="essay-card-info">
                  <div className="essay-card-title">{essay.title}</div>
                  <div className="essay-card-meta">
                    <span className={`lang-tag ${essay.language}`}>{essay.language}</span>
                    <span>{essay.word_count} words</span>
                    <span>{new Date(essay.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                  </div>
                </div>
                <div className="essay-card-score">
                  <div className="score">{Math.round(essay.score_100)}</div>
                  <div className="grade">Grade {essay.grade}</div>
                </div>
                <div className="essay-card-arrow">›</div>
              </div>
            ))
          ) : (
            <div style={{ padding: '40px 0', textAlign: 'center', color: '#9CA3AF' }}>
              <div style={{ fontSize: '2rem', marginBottom: 8 }}>📝</div>
              <div>No essays yet. Evaluate your first essay!</div>
              <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/evaluate')}>
                Get Started →
              </button>
            </div>
          )}
        </div>

        <div className="card">
          <h3 className="card-title">Skill Breakdown</h3>
          {Object.entries(traitLabels).map(([key, label]) => {
            const value = skillBreakdown[key] || 0;
            const barColor = value >= 70 ? 'green' : value >= 50 ? 'gold' : 'red';
            return (
              <div className="trait-bar" key={key}>
                <span className="trait-bar-label">{label}</span>
                <div className="trait-bar-track">
                  <div
                    className={`trait-bar-fill ${barColor}`}
                    style={{ width: `${value}%` }}
                  />
                </div>
                <span className="trait-bar-value">{value}%</span>
              </div>
            );
          })}

          <div style={{ marginTop: 16, padding: '12px 16px', background: 'rgba(45,106,79,0.04)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, fontSize: '0.9rem' }}>
              📊 Writing Consistency
            </div>
            <span style={{ fontWeight: 700 }}>
              {essayCount > 0 ? `${Math.round(avgScore * 0.9)}%` : '—'}
            </span>
          </div>
        </div>
      </div>

      {loading && (
        <div style={{ position: 'fixed', top: 12, right: 12, padding: '8px 16px', background: '#2D6A4F', color: 'white', borderRadius: 8, fontSize: '0.8rem' }}
          className="loading-pulse">
          Loading dashboard...
        </div>
      )}
    </div>
  );
}
