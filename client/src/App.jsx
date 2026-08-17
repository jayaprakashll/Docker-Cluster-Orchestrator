import { useCallback, useEffect, useState } from "react";

import Layout from "./components/Layout";

import Overview from "./pages/Overview";
import Scheduler from "./pages/Scheduler";
import Machines from "./pages/Machines";
import Containers from "./pages/Containers";
import Deploy from "./pages/Deploy";
import Logs from "./pages/Logs";
import Images from "./pages/Images";
import Deployments from "./pages/Deployments";
import Database from "./pages/Database";

import { api } from "./api";

const REFRESH_MS = Number(
  import.meta.env.VITE_REFRESH_MS || 5000
);

const PAGES = [
  ["Overview", "⌂"],
  ["Scheduler", "◈"],
  ["Machines", "▣"],
  ["Containers", "▤"],
  ["Deploy", "＋"],
  ["Logs", "≋"],
  ["Images", "◆"],
  ["Deployments", "◇"],
  ["Database", "▦"],
];

export default function App() {
  const [page, setPage] = useState("Overview");

  const [machines, setMachines] = useState([]);
  const [scores, setScores] = useState({
    ranking: [],
    selected: null,
  });

  const [loading, setLoading] = useState(true);
  const [connectionError, setConnectionError] =
    useState("");

  const refreshCoreData = useCallback(async () => {
    try {
      const [
        machineData,
        scoreData,
      ] = await Promise.all([
        api.getMachineHealth(true),
        api.getSchedulerScores(),
      ]);

      setMachines(machineData?.machines || []);
      setScores(scoreData || {});

      setConnectionError("");
    } catch (error) {
      setConnectionError(error.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshCoreData();

    const interval = setInterval(
      refreshCoreData,
      REFRESH_MS
    );

    return () => clearInterval(interval);
  }, [refreshCoreData]);

  const renderPage = () => {
    const props = {
      machines,
      scores,
      refreshCoreData,
      refreshMs: REFRESH_MS,
    };

    switch (page) {
      case "Scheduler":
        return <Scheduler {...props} />;

      case "Machines":
        return <Machines {...props} />;

      case "Containers":
        return <Containers {...props} />;

      case "Deploy":
        return <Deploy {...props} />;

      case "Logs":
        return <Logs {...props} />;

      case "Images":
        return <Images {...props} />;

      case "Deployments":
        return <Deployments {...props} />;

      case "Database":
        return <Database {...props} />;

      case "Overview":
      default:
        return (
          <Overview
            {...props}
            loading={loading}
          />
        );
    }
  };

  return (
    <Layout
      page={page}
      setPage={setPage}
      pages={PAGES}
      connectionError={connectionError}
      refreshMs={REFRESH_MS}
    >
      {renderPage()}
    </Layout>
  );
}