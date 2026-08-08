import { useState } from "react";
import { Search, Loader2, X, Inbox } from "lucide-react";
import { riskColor, decisionColor } from "../utils/format";

export const LoadingSpinner = ({ label = "Loading…" }) => (
  <div className="flex items-center gap-3 p-8 text-slate-400">
    <Loader2 className="animate-spin text-accent" size={20} /> {label}
  </div>
);

export const EmptyState = ({ message = "No records yet." }) => (
  <div className="flex flex-col items-center gap-2 p-10 text-slate-500">
    <Inbox size={28} /> <span className="text-sm">{message}</span>
  </div>
);

export const ErrorState = ({ message, onRetry }) => (
  <div className="card border-rose-500/30 text-sm text-rose-300">
    {message}
    {onRetry && <button className="btn-ghost ml-3" onClick={onRetry}>Retry</button>}
  </div>
);

export const RiskBadge = ({ level }) => (
  <span className={`chip ${riskColor(level)}`}>{level}</span>
);

export const DecisionBadge = ({ decision }) => (
  <span className={`chip ${decisionColor(decision)}`}>{String(decision).replace("_", " ")}</span>
);

export const DashboardCard = ({ icon: Icon, label, value, sub, demo }) => (
  <div className="card">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-xs uppercase tracking-wider text-slate-400">{label}</p>
        <p className="mt-2 text-2xl font-bold text-white">{value}</p>
        {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
      </div>
      {Icon && (
        <div className="rounded-xl bg-accent/15 p-2.5 text-accent">
          <Icon size={18} />
        </div>
      )}
    </div>
    {demo && <span className="chip mt-3 bg-accent/15 text-accent">DEMO DATA</span>}
  </div>
);

export const ChartCard = ({ title, subtitle, children, right }) => (
  <div className="card">
    <div className="mb-4 flex items-center justify-between">
      <div>
        <h3 className="text-sm font-semibold text-white">{title}</h3>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>
      {right}
    </div>
    {children}
  </div>
);

export const RiskGauge = ({ score = 0, level = "LOW" }) => {
  const radius = 70, circ = Math.PI * radius;
  const offset = circ - (Math.min(score, 100) / 100) * circ;
  const stroke = { LOW: "#34d399", MEDIUM: "#fbbf24", HIGH: "#fb923c", CRITICAL: "#fb7185" }[level] || "#ff7a1a";
  return (
    <div className="flex flex-col items-center">
      <svg width="180" height="105" viewBox="0 0 180 105">
        <path d="M20 95 A70 70 0 0 1 160 95" fill="none" stroke="#1c2745" strokeWidth="14" strokeLinecap="round" />
        <path d="M20 95 A70 70 0 0 1 160 95" fill="none" stroke={stroke} strokeWidth="14" strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset} style={{ transition: "stroke-dashoffset .8s ease" }} />
        <text x="90" y="82" textAnchor="middle" className="fill-white" fontSize="30" fontWeight="700">
          {Math.round(score)}
        </text>
      </svg>
      <RiskBadge level={level} />
    </div>
  );
};

export const SearchBar = ({ value, onChange, placeholder = "Search…" }) => (
  <div className="relative">
    <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
    <input className="input pl-9" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
  </div>
);

export const FilterPanel = ({ options, value, onChange, label = "Filter" }) => (
  <div className="flex flex-wrap items-center gap-2">
    <span className="text-xs uppercase text-slate-500">{label}:</span>
    {options.map((o) => (
      <button key={o.value || "all"} onClick={() => onChange(o.value)}
        className={`chip ${value === o.value ? "bg-accent text-navy-900" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}>
        {o.label}
      </button>
    ))}
  </div>
);

export const DataTable = ({ columns, rows, empty = "No records found." }) => (
  <div className="overflow-x-auto rounded-2xl border border-white/10">
    <table className="min-w-full divide-y divide-white/10">
      <thead className="bg-white/[0.03]">
        <tr>{columns.map((c) => <th key={c.key} className="th">{c.label}</th>)}</tr>
      </thead>
      <tbody className="divide-y divide-white/5">
        {rows.length === 0 ? (
          <tr><td className="td" colSpan={columns.length}><EmptyState message={empty} /></td></tr>
        ) : rows.map((row, i) => (
          <tr key={row.id || i} className="hover:bg-white/[0.03]">
            {columns.map((c) => <td key={c.key} className="td">{c.render ? c.render(row) : row[c.key]}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export const ConfirmationModal = ({ open, title, children, onCancel, onConfirm, confirmLabel = "Confirm" }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="glass w-full max-w-md p-6">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-base">{title}</h3>
          <button onClick={onCancel}><X size={16} /></button>
        </div>
        <div className="text-sm text-slate-300">{children}</div>
        <div className="mt-6 flex justify-end gap-2">
          <button className="btn-ghost" onClick={onCancel}>Cancel</button>
          <button className="btn-primary" onClick={onConfirm}>{confirmLabel}</button>
        </div>
      </div>
    </div>
  );
};

export const AgentStatusCard = ({ name, status = "ONLINE", detail }) => (
  <div className="card flex items-center justify-between">
    <div>
      <p className="text-sm font-semibold text-white">{name}</p>
      <p className="text-xs text-slate-500">{detail}</p>
    </div>
    <span className="chip bg-emerald-500/15 text-emerald-300">
      <span className="mr-1.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />{status}
    </span>
  </div>
);

export const ActivityFeed = ({ items = [] }) => (
  <div className="space-y-3">
    {items.length === 0 && <EmptyState message="No agent activity yet." />}
    {items.map((a, i) => (
      <div key={i} className="flex items-start gap-3 border-b border-white/5 pb-3 last:border-0">
        <span className="mt-0.5 font-mono text-xs text-accent">{a.time}</span>
        <div className="flex-1">
          <p className="text-sm text-slate-200">{a.message}</p>
          <p className="text-xs text-slate-500">{a.agent}</p>
        </div>
        <DecisionBadge decision={a.decision} />
      </div>
    ))}
  </div>
);

export const AuditTimeline = ({ logs = [] }) => (
  <ol className="relative border-l border-white/10 pl-5">
    {logs.map((l) => (
      <li key={l.audit_id} className="mb-5">
        <span className="absolute -left-[5px] mt-1.5 h-2.5 w-2.5 rounded-full bg-accent" />
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs text-accent">{l.audit_id}</span>
          <DecisionBadge decision={l.decision} />
          <RiskBadge level={l.risk_level} />
        </div>
        <p className="mt-1 text-sm text-slate-200">{l.agent} · input {l.input_reference} · score {l.risk_score}</p>
        <ul className="mt-1 list-disc pl-4 text-xs text-slate-400">
          {(l.reasons || []).slice(0, 4).map((r, i) => <li key={i}>{r}</li>)}
        </ul>
        <p className="mt-1 text-[11px] text-slate-500">
          {l.model_version} · {l.policy_version} · {new Date(l.created_at).toLocaleString("en-IN")} ·
          override: {l.reviewer_override ? "YES" : "NO"}
        </p>
      </li>
    ))}
  </ol>
);

export const Field = ({ label, children }) => (
  <div><span className="label">{label}</span>{children}</div>
);

export const useForm = (initial) => {
  const [values, setValues] = useState(initial);
  const set = (k, v) => setValues((s) => ({ ...s, [k]: v }));
  return [values, set, setValues];
};

export const PageHeader = ({ title, subtitle, children }) => (
  <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
    <div>
      <h1 className="text-2xl">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
    </div>
    {children}
  </div>
);
