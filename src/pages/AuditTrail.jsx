import { useState } from "react";
import useApi from "../hooks/useApi";
import { endpoints } from "../services/api";
import { PageHeader, AuditTimeline, LoadingSpinner, ErrorState, SearchBar, FilterPanel } from "../components";

const AGENTS = [{ label: "All agents", value: "" }, { label: "Risk", value: "risk_agent" },
  { label: "Authenticity", value: "authenticity_agent" }, { label: "Review", value: "review_agent" }];

export default function AuditTrail() {
  const [agent, setAgent] = useState(""); const [q, setQ] = useState("");
  const { data, loading, error, refresh } = useApi(() => endpoints.auditLogs({ agent: agent || undefined }), [agent]);

  return (
    <>
      <PageHeader title="Audit Trail" subtitle="Immutable decision log — every agent output, reason and override" />
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="w-72"><SearchBar value={q} onChange={setQ} placeholder="Search audit IDs, reasons…" /></div>
        <FilterPanel options={AGENTS} value={agent} onChange={setAgent} label="Agent" />
      </div>
      {loading ? <LoadingSpinner /> : error ? <ErrorState message={error} onRetry={refresh} /> : (
        <div className="card">
          <AuditTimeline logs={(data?.logs || []).filter((l) => !q || JSON.stringify(l).toLowerCase().includes(q.toLowerCase()))} />
        </div>
      )}
    </>
  );
}
