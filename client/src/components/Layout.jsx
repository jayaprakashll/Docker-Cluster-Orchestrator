export default function Layout({
  page,
  setPage,
  pages,
  connectionError,
  refreshMs,
  children,
}) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">◈ ORBIT</div>

        <div className="brand-subtitle">
          DOCKER CLUSTER CONTROL PLANE
        </div>

        <div
          className={
            connectionError
              ? "connection connection-error"
              : "connection"
          }
        >
          ●{" "}
          {connectionError
            ? "CONTROL PLANE OFFLINE"
            : "CONTROL PLANE ONLINE"}
        </div>

        <div className="sidebar-label">
          CONTROL PLANE
        </div>

        <nav className="navigation">
          {pages.map(([name, icon]) => (
            <button
              key={name}
              className={
                page === name
                  ? "nav-button active"
                  : "nav-button"
              }
              onClick={() => setPage(name)}
            >
              <span className="nav-icon">
                {icon}
              </span>

              <span>{name}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-divider" />

        <div className="manager-info">
          <div>MANAGER</div>

          <span>
            {import.meta.env.VITE_MANAGER_URL ||
              "http://localhost:8000"}
          </span>

          <br />

          <br />

          <div>LIVE REFRESH</div>

          <span>
            {Math.floor(refreshMs / 1000)}s
          </span>
        </div>
      </aside>

      <main className="main-content">
        {children}

        <footer className="footer">
          ORBIT CONTROL PLANE • LIVE TELEMETRY •
          WEIGHTED RESOURCE SCHEDULER
        </footer>
      </main>
    </div>
  );
}