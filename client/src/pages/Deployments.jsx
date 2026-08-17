import { useEffect, useState } from "react";
import { api } from "../api";
import { DataTable } from "./Scheduler";

export default function Deployments() {
  const [deployments, setDeployments] =
    useState([]);

  const [error, setError] =
    useState("");

  useEffect(() => {
    async function load() {
      try {
        const data =
          await api.getDeployments();

        setDeployments(
          data?.deployments || []
        );
      } catch (err) {
        setError(err.message);
      }
    }

    load();
  }, []);

  const columns =
    deployments.length > 0
      ? Object.keys(deployments[0])
      : [];

  return (
    <>
      <PageHeader
        eyebrow="WORKLOAD DEFINITIONS"
        title="Deployments"
        subtitle="Deployment records currently stored by the Manager."
      />

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      {deployments.length === 0 ? (
        <div className="empty-state">
          No deployments found.
        </div>
      ) : (
        <DataTable
          columns={columns}
          rows={deployments}
        />
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