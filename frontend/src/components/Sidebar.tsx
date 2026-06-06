import { NavLink } from 'react-router-dom';

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">✦</div>
        <div className="sidebar-brand-text">
          <h2>SahityaAI</h2>
          <span>Bilingual Essay Evaluator</span>
        </div>
      </div>

      <div className="sidebar-section-label">Menu</div>

      <nav className="sidebar-nav">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
        >
          <span className="icon">📊</span>
          Dashboard
        </NavLink>

        <NavLink
          to="/evaluate"
          className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
        >
          <span className="icon">✏️</span>
          Evaluate Essay
        </NavLink>

        <NavLink
          to="/tutor"
          className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
        >
          <span className="icon">💬</span>
          AI Tutor
        </NavLink>

        <NavLink
          to="/analytics"
          className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
        >
          <span className="icon">📈</span>
          Analytics
        </NavLink>
      </nav>

      <div className="sidebar-bottom">
        <NavLink
          to="/settings"
          className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
        >
          <span className="icon">⚙️</span>
          Settings
        </NavLink>
      </div>
    </aside>
  );
}
