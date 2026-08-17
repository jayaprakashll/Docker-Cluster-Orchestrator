import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import ContainerCard from "../components/ContainerCard";

export default function Containers() {
  const [containers, setContainers] =
    useState([]);

  const [error, setError] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const load = useCallback(async () => {
    try {
      setLoading(true);

      const data =
        await api.getContainers(
          null,
          true
        );

      setContainers(
        data?.containers || []
      );

      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <>
      <PageHeader
        eyebrow="DOCKER WORKLOAD CONTROL"
        title="Containers"
        subtitle="Start, stop, restart, inspect or permanently remove workloads."
      />

      {loading && (
        <div className="loading-bar">
          Loading containers...
        </div>
      )}

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      {!loading &&
        containers.length === 0 && (
          <div className="empty-state">
            No containers found.
          </div>
        )}

      <div className="vertical-stack">
        {containers.map(
          (container, index) => (
            <ContainerCard
              key={
                container.id ||
                container.name ||
                index
              }
              container={container}
              onChanged={load}
            />
          )
        )}
      </div>
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