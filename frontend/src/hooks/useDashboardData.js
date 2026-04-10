import { useState, useEffect } from "react";
import api from "../api/client";

/**
 * Fetches all dashboard data in parallel on mount.
 *
 * Returns { signal, forecast, quitForecast, leading, wages, metadata, loading, error }
 */
export function useDashboardData() {
  const [data, setData] = useState({
    signal: null,
    forecast: null,
    quitForecast: null,
    leading: null,
    wages: null,
    metadata: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchAll() {
      try {
        const [signal, forecast, quitForecast, leading, wages, metadata] =
          await Promise.all([
            api.get("/api/signal"),
            api.get("/api/forecast/employment"),
            api.get("/api/forecast/quit-rate"),
            api.get("/api/indicators/leading"),
            api.get("/api/indicators/wages"),
            api.get("/api/metadata"),
          ]);
        setData({ signal, forecast, quitForecast, leading, wages, metadata });
      } catch (err) {
        setError(err.message || "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, []);

  return { ...data, loading, error };
}
