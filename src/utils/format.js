export const inr = (n) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 })
    .format(Number(n || 0));

export const pct = (n) => `${Number(n || 0).toFixed(1)}%`;

export const riskColor = (level) =>
  ({
    LOW: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
    MEDIUM: "bg-amber-500/15 text-amber-300 border border-amber-500/30",
    HIGH: "bg-orange-500/15 text-orange-300 border border-orange-500/30",
    CRITICAL: "bg-rose-500/15 text-rose-300 border border-rose-500/30",
  }[level] || "bg-slate-500/15 text-slate-300 border border-slate-500/30");

export const decisionColor = (d) =>
  ({
    ALLOW: "bg-emerald-500/15 text-emerald-300",
    PUBLISH: "bg-emerald-500/15 text-emerald-300",
    APPROVE: "bg-emerald-500/15 text-emerald-300",
    VERIFY: "bg-amber-500/15 text-amber-300",
    REVIEW: "bg-amber-500/15 text-amber-300",
    FLAG: "bg-amber-500/15 text-amber-300",
    MANUAL_REVIEW: "bg-orange-500/15 text-orange-300",
    BLOCK_COD: "bg-rose-500/15 text-rose-300",
    REJECT: "bg-rose-500/15 text-rose-300",
    HIDE: "bg-rose-500/15 text-rose-300",
  }[d] || "bg-slate-500/15 text-slate-300");

export const dt = (s) => (s ? new Date(s).toLocaleString("en-IN") : "-");
