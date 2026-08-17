import { useEffect, useState } from "react";
import { api } from "../api";

export default function Database() {
  const [database, setDatabase] =
    useState(null);

  const [error, setError] =
    useState("");

  useEffect(() => {
    async function load() {
      try {
        const data =
          await api.getDatabaseInfo();

        setDatabase(data);
      } catch (err) {
        setError(err.message);
      }
    }

    load();
  }, []);

  return (
    <>
      <PageHeader
        eyebrow="MANAGER STORAGE"
        title="Database"
        subtitle="Database statistics and persistence information."
      />

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      {database &&
      typeof database === "object" ? (
        <>
          <div className="metric-grid">
            {Object.entries(database)
                .slice(0, 4)
                .map(([key, value]) => (
                <div className="metric-card" key={key}>
                    <div className="metric-label">
                    {key.replace(/_/g, " ").toUpperCase()}
                    </div>

                    <div
                    className="metric-value"
                    title={String(value)}
                    >
                    {String(value)}
                    </div>
                </div>
                ))}
            </div>

          <details className="raw-response">
            <summary>
              RAW DATABASE RESPONSE
            </summary>

            <pre>
              {JSON.stringify(
                database,
                null,
                2
              )}
            </pre>
          </details>
        </>
      ) : (
        !error && (
          <div className="empty-state">
            Loading database information...
          </div>
        )
      )}
    </>
  );
}

function PageHeader({
  eyebrow,
  title,
  subtitle,
}) {
  return (
    <header className="page-header">
      <div className="eyebrow">
        {eyebrow}
      </div>

      <h1>{title}</h1>

      <p>{subtitle}</p>
    </header>
  );
}