import { RefreshCw, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import type { ProcessInfo, ProcessTopResponse, SystemOverview } from "../api/types";

interface StatusPanelProps {
  onClose: () => void;
}

function formatBytes(bytes: number) {
  const gb = bytes / 1024 / 1024 / 1024;
  return `${gb.toFixed(1)} GB`;
}

export function StatusPanel({ onClose }: StatusPanelProps) {
  const [overview, setOverview] = useState<SystemOverview | null>(null);
  const [processes, setProcesses] = useState<ProcessInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [overviewResponse, processResponse] = await Promise.all([
        fetch("http://127.0.0.1:8765/api/system/overview"),
        fetch("http://127.0.0.1:8765/api/process/top")
      ]);
      if (!overviewResponse.ok || !processResponse.ok) {
        throw new Error("request failed");
      }
      const overviewPayload = (await overviewResponse.json()) as SystemOverview;
      const processPayload = (await processResponse.json()) as ProcessTopResponse;
      setOverview(overviewPayload);
      setProcesses(processPayload.processes ?? []);
    } catch {
      setOverview(null);
      setProcesses([]);
      setError("Agent 后端未连接，暂时无法读取电脑状态。");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <section className="statusPanel" aria-label="System status">
      <header className="panelHeader">
        <strong>电脑状态</strong>
        <div className="panelActions">
          <button className="panelIconButton" type="button" aria-label="Refresh status" onClick={() => void refresh()}>
            <RefreshCw className={loading ? "spin" : ""} size={16} />
          </button>
          <button className="panelIconButton" type="button" aria-label="Close status" onClick={onClose}>
            <X size={16} />
          </button>
        </div>
      </header>

      {error ? (
        <p className="panelError">{error}</p>
      ) : (
        <>
          <div className="metricGrid">
            <div>
              <span>CPU</span>
              <strong>{overview ? `${overview.cpu_percent}%` : "-"}</strong>
            </div>
            <div>
              <span>内存</span>
              <strong>{overview ? `${overview.memory.percent}%` : "-"}</strong>
              <small>{overview ? `${formatBytes(overview.memory.available)} 可用` : ""}</small>
            </div>
            <div>
              <span>磁盘</span>
              <strong>{overview ? `${overview.disk.percent}%` : "-"}</strong>
              <small>{overview ? `${formatBytes(overview.disk.free)} 可用` : ""}</small>
            </div>
          </div>

          <div className="processList">
            {processes.slice(0, 10).map((process) => (
              <div className="processRow" key={process.pid}>
                <span>{process.name}</span>
                <small>
                  CPU {process.cpu_percent.toFixed(1)}% · MEM {process.memory_percent.toFixed(2)}%
                </small>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
