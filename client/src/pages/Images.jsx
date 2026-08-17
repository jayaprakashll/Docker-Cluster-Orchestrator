import { useEffect, useState } from "react";
import { api } from "../api";
import { DataTable } from "./Scheduler";

export default function Images() {
  const [images, setImages] =
    useState([]);

  const [error, setError] =
    useState("");

  useEffect(() => {
    async function load() {
      try {
        const data =
          await api.getImages();

        setImages(
          data?.images || []
        );
      } catch (err) {
        setError(err.message);
      }
    }

    load();
  }, []);

  const columns =
    images.length > 0
      ? Object.keys(images[0])
      : [];

  return (
    <>
      <PageHeader
        eyebrow="DOCKER REGISTRY CACHE"
        title="Images"
        subtitle="Docker images visible through the Manager."
      />

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      {images.length === 0 ? (
        <div className="empty-state">
          No Docker images found.
        </div>
      ) : (
        <DataTable
          columns={columns}
          rows={images}
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