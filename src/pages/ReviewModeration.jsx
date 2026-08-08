import { useState } from "react";
import { endpoints } from "../services/api";
import { useToast } from "../context/ToastContext";
import {
  PageHeader,
  RiskGauge,
  DecisionBadge,
  LoadingSpinner,
} from "../components";

const INIT = {
  text: "Best product must buy highly recommend amazing quality",
  rating: 5,
  user_code: "USER-9931",
  seller_code: "SELL-207",
  product_id: "PROD-551",
  account_age_days: 100,
  verified_purchase: false,
};

export default function ReviewModeration() {
  const { toast } = useToast();

  const [form, setForm] = useState(INIT);
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
      console.log("REVIEW REQUEST:", form);

      const response = await endpoints.analyzeReview(form);

      console.log("REVIEW RESPONSE:", response);

      setResult(response);

      toast("Review analysis complete", "success");
    } catch (err) {
      console.error("REVIEW ERROR:", err);

      toast(err.message || "Review validation failed", "error");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setForm(INIT);
    setResult(null);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Agent 3 — Review Integrity"
        subtitle="Fake review detection and coordinated ring discovery"
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* FORM */}
        <div className="card">
          <form onSubmit={submit} className="space-y-4">
            {/* REVIEW TEXT */}
            <div>
              <label className="label">Review Text</label>

              <textarea
                className="input h-24"
                value={form.text}
                onChange={(e) => set("text", e.target.value)}
                required
              />
            </div>

            {/* RATING + USER */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="label">Rating</label>

                <input
                  className="input"
                  type="number"
                  min="1"
                  max="5"
                  value={form.rating}
                  onChange={(e) => set("rating", Number(e.target.value))}
                />
              </div>

              <div>
                <label className="label">Reviewer ID</label>

                <input
                  className="input"
                  value={form.user_code}
                  onChange={(e) => set("user_code", e.target.value)}
                />
              </div>
            </div>

            {/* SELLER */}
            <div>
              <label className="label">Seller ID</label>

              <input
                className="input"
                value={form.seller_code}
                onChange={(e) => set("seller_code", e.target.value)}
              />
            </div>

            {/* PRODUCT */}
            <div>
              <label className="label">Product ID</label>

              <input
                className="input"
                value={form.product_id}
                onChange={(e) => set("product_id", e.target.value)}
              />
            </div>

            {/* ACCOUNT AGE */}
            <div>
              <label className="label">Account Age (Days)</label>

              <input
                className="input"
                type="number"
                min="0"
                value={form.account_age_days}
                onChange={(e) =>
                  set("account_age_days", Number(e.target.value))
                }
              />
            </div>

            {/* VERIFIED */}
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.verified_purchase}
                onChange={(e) => set("verified_purchase", e.target.checked)}
              />

              <span className="text-sm text-slate-300">Verified purchase</span>
            </label>

            {/* BUTTONS */}
            <div className="flex gap-3">
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? "Analyzing..." : "Analyze Review"}
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

        {/* RESULT */}
        <div className="card">
          {loading && <LoadingSpinner label="Analyzing review..." />}

          {!loading && !result && (
            <p className="p-6 text-sm text-slate-400">
              Analyze a review to see review integrity scoring and linguistic
              evidence.
            </p>
          )}

          {!loading && result && (
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <RiskGauge
                  score={
                    result.risk_score ??
                    result.fake_review_score ??
                    result.review_score ??
                    0
                  }
                  level={result.risk_level || "UNKNOWN"}
                />

                <div className="text-right">
                  <DecisionBadge decision={result.decision || "UNKNOWN"} />

                  {result.confidence !== undefined && (
                    <p className="mt-2 text-xs text-slate-500">
                      confidence {(result.confidence * 100).toFixed(0)}%
                    </p>
                  )}

                  {result.audit_id && (
                    <p className="text-xs text-slate-500">
                      audit {result.audit_id}
                    </p>
                  )}
                </div>
              </div>

              {/* REASONS */}
              {Array.isArray(result.reasons) && (
                <div>
                  <p className="label">Why this decision</p>

                  <ul className="space-y-2">
                    {result.reasons.map((reason, index) => (
                      <li
                        key={index}
                        className="rounded-xl bg-white/5 px-3 py-2 text-sm"
                      >
                        {typeof reason === "object"
                          ? JSON.stringify(reason)
                          : reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* SIGNALS */}
              {result.signals && (
                <div>
                  <p className="label">Signals</p>

                  <pre className="overflow-auto rounded-xl bg-white/5 p-3 text-xs text-slate-400">
                    {JSON.stringify(result.signals, null, 2)}
                  </pre>
                </div>
              )}

              {/* RING */}
              {result.ring_analysis && (
                <div>
                  <p className="label">Ring Analysis</p>

                  <pre className="overflow-auto rounded-xl bg-white/5 p-3 text-xs text-slate-400">
                    {JSON.stringify(result.ring_analysis, null, 2)}
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
