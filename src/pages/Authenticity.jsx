import { useState } from "react";
import { endpoints } from "../services/api";
import { useToast } from "../context/ToastContext";
import {
  PageHeader,
  RiskGauge,
  DecisionBadge,
  LoadingSpinner,
  Field,
} from "../components";

const INIT = {
  product_name: "Nike Air Max — 1st copy premium",
  brand: "Nike",
  description: "100% original master quality, no bill",
  price: 1499,
  msrp: 8999,
  seller_code: "SELL-207",
  authorized: false,
  certification_status: "claimed_unverified",
};

export default function Authenticity() {
  const { toast } = useToast();

  const [form, setForm] = useState(INIT);
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const set = (key, value) => {
    setForm((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const submit = async (e) => {
    e.preventDefault();

    setLoading(true);
    setResult(null);

    try {
      const fd = new FormData();

      fd.append("product_name", form.product_name);
      fd.append("brand", form.brand);
      fd.append("description", form.description);
      fd.append("price", String(form.price));
      fd.append("msrp", String(form.msrp));
      fd.append("seller_code", form.seller_code);
      fd.append("authorized", String(form.authorized));
      fd.append("certification_status", form.certification_status);

      if (file) {
        fd.append("image", file);
      }

      console.log("AUTHENTICITY REQUEST:");

      for (const [key, value] of fd.entries()) {
        console.log(key, value);
      }

      const response = await endpoints.analyzeAuthenticity(fd);

      console.log("AUTHENTICITY RESPONSE:", response);

      setResult(response);

      toast("Authenticity scan complete", "success");
    } catch (err) {
      console.error("AUTHENTICITY ERROR:", err);
      toast(err.message || "Authenticity validation failed", "error");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setForm(INIT);
    setFile(null);
    setResult(null);
  };

  const renderBreakdownValue = (value) => {
    if (value === null || value === undefined) {
      return "N/A";
    }

    if (typeof value === "object") {
      if ("score" in value) {
        return value.score;
      }

      if ("value" in value) {
        return value.value;
      }

      return JSON.stringify(value);
    }

    return value;
  };

  const getBreakdownWidth = (value) => {
    const rendered = renderBreakdownValue(value);
    const number = Number(rendered);

    if (Number.isNaN(number)) {
      return 0;
    }

    return Math.min(Math.max(number, 0), 100);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Agent 2 — Product Authenticity"
        subtitle="Counterfeit detection from images, claims and price signals"
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* LEFT SIDE */}
        <div className="card">
          <form onSubmit={submit} className="space-y-4">
            {/* Product Name */}
            <div>
              <label className="label">Listing Title</label>

              <input
                className="input"
                value={form.product_name}
                onChange={(e) => set("product_name", e.target.value)}
                required
              />
            </div>

            {/* Brand */}
            <div>
              <label className="label">Brand</label>

              <input
                className="input"
                value={form.brand}
                onChange={(e) => set("brand", e.target.value)}
              />
            </div>

            {/* Price */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="label">Listed Price (INR)</label>

                <input
                  className="input"
                  type="number"
                  min="0"
                  value={form.price}
                  onChange={(e) => set("price", Number(e.target.value))}
                />
              </div>

              <div>
                <label className="label">Market Price (INR)</label>

                <input
                  className="input"
                  type="number"
                  min="0"
                  value={form.msrp}
                  onChange={(e) => set("msrp", Number(e.target.value))}
                />
              </div>
            </div>

            {/* Seller */}
            <div>
              <label className="label">Seller ID</label>

              <input
                className="input"
                value={form.seller_code}
                onChange={(e) => set("seller_code", e.target.value)}
              />
            </div>

            {/* Certification */}
            <div>
              <label className="label">Certification</label>

              <select
                className="input"
                value={form.certification_status}
                onChange={(e) => set("certification_status", e.target.value)}
              >
                <option value="">None</option>
                <option value="verified">Verified</option>
                <option value="claimed_unverified">Claimed Unverified</option>
              </select>
            </div>

            {/* Description */}
            <div>
              <label className="label">Description</label>

              <textarea
                className="input h-24"
                value={form.description}
                onChange={(e) => set("description", e.target.value)}
              />
            </div>

            {/* Image */}
            <div>
              <label className="label">Product Image (Optional)</label>

              <input
                className="input"
                type="file"
                accept="image/*"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>

            {/* Authorized */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.authorized}
                onChange={(e) => set("authorized", e.target.checked)}
              />

              <span className="text-sm text-slate-300">Authorized seller</span>
            </div>

            {/* Buttons */}
            <div className="flex gap-3">
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? "Scanning..." : "Scan Listing"}
              </button>

              <button
                type="button"
                className="btn-ghost"
                onClick={reset}
                disabled={loading}
              >
                Reset
              </button>
            </div>
          </form>
        </div>

        {/* RIGHT SIDE */}
        <div className="card">
          {loading && <LoadingSpinner label="Inspecting listing..." />}

          {!loading && !result && (
            <p className="p-6 text-sm text-slate-400">
              Run a scan to see the authenticity verdict and evidence breakdown.
            </p>
          )}

          {!loading && result && (
            <div className="space-y-5">
              {/* SCORE */}
              <div className="flex items-center justify-between">
                <RiskGauge
                  score={
                    result.counterfeit_score ??
                    result.counterfeit_probability ??
                    0
                  }
                  level={result.risk_level || "UNKNOWN"}
                />

                <div className="text-right">
                  <DecisionBadge decision={result.decision || "UNKNOWN"} />

                  <p className="mt-2 text-xs text-slate-500">
                    confidence{" "}
                    {result.confidence !== undefined
                      ? `${(result.confidence * 100).toFixed(0)}%`
                      : "N/A"}
                  </p>

                  <p className="text-xs text-slate-500">
                    {result.model_version || ""}
                  </p>

                  <p className="text-xs text-slate-500">
                    audit {result.audit_id || "N/A"}
                  </p>

                  {result.listing_id && (
                    <p className="text-xs text-slate-500">
                      listing {result.listing_id}
                    </p>
                  )}
                </div>
              </div>

              {/* BREAKDOWN */}
              {result.breakdown && typeof result.breakdown === "object" && (
                <div>
                  <p className="label">Evidence Breakdown</p>

                  <div className="space-y-3">
                    {Object.entries(result.breakdown).map(([key, value]) => {
                      const displayValue = renderBreakdownValue(value);

                      const width = getBreakdownWidth(value);

                      return (
                        <div key={key}>
                          <div className="flex justify-between text-xs text-slate-400">
                            <span>{key.replace(/_/g, " ")}</span>

                            <span>{displayValue}</span>
                          </div>

                          <div className="h-1.5 rounded-full bg-white/10">
                            <div
                              className="h-1.5 rounded-full bg-accent"
                              style={{
                                width: `${width}%`,
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* REASONS */}
              <div>
                <p className="label">Evidence</p>

                <ul className="space-y-2">
                  {Array.isArray(result.reasons) &&
                    result.reasons.map((reason, index) => (
                      <li
                        key={index}
                        className="rounded-xl bg-white/5 px-3 py-2 text-sm text-slate-200"
                      >
                        {typeof reason === "object"
                          ? JSON.stringify(reason)
                          : reason}
                      </li>
                    ))}
                </ul>
              </div>

              {/* IMAGE */}
              {result.image_analysis && (
                <div>
                  <p className="label">Image Analysis</p>

                  <pre className="overflow-auto rounded-xl bg-white/5 p-3 text-xs text-slate-400">
                    {JSON.stringify(result.image_analysis, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
