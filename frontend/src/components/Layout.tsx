import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function Layout() {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-area">
        <header className="topbar">
          <div style={{ width: 20 }} />
          <div className="topbar-right">
            <span className="topbar-title">Bilingual Essay Evaluation Platform</span>
            <div className="topbar-avatar">S</div>
          </div>
        </header>
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
