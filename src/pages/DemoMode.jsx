import { useState } from "react";
import useApi from "../hooks/useApi";
import { endpoints } from "../services/api";
import { useToast } from "../context/ToastContext";
import {
  PageHeader,
  LoadingSpinner,
  ErrorState,
  DecisionBadge,
  RiskBadge,
} from "../components";

export default function DemoMode() {
  const { toast } = useToast();

  const { data, loading, error, refresh } = useApi(
    () => endpoints.scenarios(),
    [],
  );

  const [active, setActive] = useState(null);

  // -----------------------------
  // Loading state
  // -----------------------------
  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Demo Mode"
          subtitle="Interactive Trust & Safety scenarios"
        />

        <div className="card">
          <LoadingSpinner label="Loading demo scenarios..." />
        </div>
      </div>
    );
  }

  // -----------------------------
  // Error state
  // -----------------------------
  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Demo Mode"
          subtitle="Interactive Trust & Safety scenarios"
        />

        <ErrorState
          message={error?.message || "Unable to load demo scenarios."}
          onRetry={refresh}
        />
      </div>
    );
  }

  // -----------------------------
  // Safely get scenarios
  // -----------------------------
  const scenarios = Array.isArray(data?.scenarios) ? data.scenarios : [];

  // -----------------------------
  // Open scenario
  // -----------------------------
  const openScenario = (scenario) => {
    setActive(scenario);

    toast(`Running: ${scenario?.title || "Demo scenario"}`, "info");
  };

  // -----------------------------
  // Close scenario
  // -----------------------------
  const closeScenario = () => {
    setActive(null);
  };

  return (
    <div className="space-y-6">
      {/* =====================================================
          PAGE HEADER
      ====================================================== */}
      <PageHeader
        title="Demo Mode"
        subtitle="Interactive Trust & Safety scenarios"
      />

      {/* =====================================================
          SCENARIO CARDS
      ====================================================== */}
      {scenarios.length === 0 ? (
        <div className="card">
          <p className="text-sm text-slate-400">
            No demo scenarios are available.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {scenarios.map((scenario, index) => (
            <button
              key={scenario?.id || `scenario-${index}`}
              type="button"
              onClick={() => openScenario(scenario)}
              className="card text-left transition hover:border-accent/40"
            >
              {/* Scenario title */}
              <h3 className="text-base font-semibold text-white">
                {scenario?.title || "Untitled scenario"}
              </h3>

              {/* Scenario description */}
              <p className="mt-2 text-sm text-slate-400">
                {scenario?.description ||
                  scenario?.narrative ||
                  "No description available."}
              </p>

              {/* Optional risk / decision information */}
              <div className="mt-4 flex flex-wrap gap-2">
                {scenario?.risk_level && (
                  <RiskBadge level={scenario.risk_level} />
                )}

                {scenario?.decision && (
                  <DecisionBadge decision={scenario.decision} />
                )}
              </div>

              {/* Start text */}
              <p className="mt-5 text-xs font-medium text-accent">
                Click to start walkthrough →
              </p>
            </button>
          ))}
        </div>
      )}

      {/* =====================================================
          ACTIVE SCENARIO
      ====================================================== */}
      {active && (
        <div className="card">
          {/* Header */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Active scenario
              </p>

              <h2 className="mt-1 text-xl font-semibold text-white">
                {active?.title || "Demo scenario"}
              </h2>

              <p className="mt-2 text-sm text-slate-400">
                {active?.description ||
                  active?.narrative ||
                  "No description available."}
              </p>
            </div>

            <button type="button" onClick={closeScenario} className="btn-ghost">
              Close
            </button>
          </div>

          {/* =================================================
              WALKTHROUGH
          ================================================== */}
          <div className="mt-6">
            <p className="label">Walkthrough</p>

            {Array.isArray(active?.steps) && active.steps.length > 0 ? (
              <ol className="space-y-3">
                {active.steps.map((step, index) => (
                  <li
                    key={index}
                    className="flex gap-3 rounded-xl bg-white/5 px-4 py-3"
                  >
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/20 text-xs font-semibold text-accent">
                      {index + 1}
                    </span>

                    <span className="text-sm text-slate-200">
                      {typeof step === "string"
                        ? step
                        : step?.text ||
                          step?.description ||
                          JSON.stringify(step)}
                    </span>
                  </li>
                ))}
              </ol>
            ) : (
              <div className="rounded-xl bg-white/5 px-4 py-4 text-sm text-slate-400">
                No walkthrough steps are available for this scenario.
              </div>
            )}
          </div>

          {/* =================================================
              NARRATIVE
          ================================================== */}
          <div className="mt-6">
            <p className="label">Narrative</p>

            <div className="rounded-xl bg-white/5 px-4 py-4 text-sm text-slate-200">
              {active?.narrative ||
                active?.description ||
                "No narrative is available for this scenario."}
            </div>
          </div>

          {/* =================================================
              SCENARIO DATA
          ================================================== */}
          <div className="mt-6">
            <p className="label">Scenario Data</p>

            <pre className="overflow-x-auto rounded-xl bg-black/20 p-4 text-xs leading-6 text-slate-300">
              {JSON.stringify(
                active?.data || active?.scenario_data || active?.payload || {},
                null,
                2,
              )}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
