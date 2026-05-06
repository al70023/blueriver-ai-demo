import type { HealthResponse } from "../types";

type HealthStatusProps = {
  health: HealthResponse | null;
  loading: boolean;
  error: string | null;
};

const services: Array<keyof HealthResponse> = ["api", "postgres", "qdrant"];

export function HealthStatus({ health, loading, error }: HealthStatusProps) {
  return (
    <section className="panel health-panel" aria-labelledby="health-title">
      <div className="panel-heading">
        <h2 id="health-title">Backend Status</h2>
        {loading ? <span className="muted">Checking...</span> : null}
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="status-grid">
        {services.map((service) => {
          const value = health?.[service] ?? "unknown";
          const ok = value === "ok";

          return (
            <div className="status-item" key={service}>
              <span className={`status-dot ${ok ? "ok" : "bad"}`} />
              <span className="status-name">{service}</span>
              <span className="status-value">{value}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
