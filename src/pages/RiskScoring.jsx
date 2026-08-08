import { useState } from "react";
import { endpoints } from "../services/api";
import { useToast } from "../context/ToastContext";
import {
  PageHeader,
  RiskGauge,
  DecisionBadge,
  LoadingSpinner,
} from "../components";
import { inr } from "../utils/format";

const INIT = {
  customer_id: "CUST-1042",
  order_id: "ORD-1001",
  order_amount: 8999,
  payment_method: "COD",
  is_cod: true,

  previous_orders: 12,
  previous_returns: 5,
  cod_refusals: 3,

  account_age_days: 40,

  device_id: "",
  ip_address: "",
  ip_velocity: 6,

  new_device: true,
  payment_risk_flag: false,
  location_mismatch: true,
};

export default function RiskScoring() {
  const { toast } = useToast();

  const [form, setForm] = useState(INIT);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const set = (key, value) => {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const submit = async (e) => {
    e.preventDefault();

    setLoading(true);
    setResult(null);

    try {
      console.log("RISK REQUEST:", form);

      const response = await endpoints.analyzeRisk(form);

      console.log("RISK RESPONSE:", response);

      setResult(response);

      toast("Risk analysis complete", "success");
    } catch (err) {
      console.error("RISK ERROR:", err);
      toast(err.message || "Risk analysis failed", "error");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setForm(INIT);
    setResult(null);
  };

  return (
    <div>
      <PageHeader
        title="Risk Scoring Agent"
        subtitle="Analyze transactions for fraud and risk signals"
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* =========================
            LEFT SIDE - INPUT FORM
           ========================= */}
        <div className="card">
          <form onSubmit={submit} className="space-y-5">
            {/* Customer ID */}
            <div>
              <label className="label">Customer ID</label>

              <input
                className="input"
                value={form.customer_id}
                onChange={(e) => set("customer_id", e.target.value)}
                placeholder="CUST-1042"
              />
            </div>

            {/* Order ID */}
            <div>
              <label className="label">Order ID</label>

              <input
                className="input"
                value={form.order_id}
                onChange={(e) => set("order_id", e.target.value)}
                placeholder="ORD-1001"
              />
            </div>

            {/* Order Amount */}
            <div>
              <label className="label">Order Amount (INR)</label>

              <input
                className="input"
                type="number"
                min="0"
                value={form.order_amount}
                onChange={(e) =>
                  set("order_amount", Number(e.target.value))
                }
              />
            </div>

            {/* Payment Method */}
            <div>
              <label className="label">Payment Method</label>

              <select
                className="input"
                value={form.payment_method}
                onChange={(e) => {
                  const value = e.target.value;

                  set("payment_method", value);
                  set("is_cod", value === "COD");
                }}
              >
                <option value="COD">COD</option>
                <option value="UPI">UPI</option>
                <option value="CARD">Card</option>
                <option value="NETBANKING">Net Banking</option>
              </select>
            </div>

            {/* Previous Orders */}
            <div>
              <label className="label">Previous Orders</label>

              <input
                className="input"
                type="number"
                min="0"
                value={form.previous_orders}
                onChange={(e) =>
                  set("previous_orders", Number(e.target.value))
                }
              />
            </div>

            {/* Previous Returns */}
            <div>
              <label className="label">Previous Returns</label>

              <input
                className="input"
                type="number"
                min="0"
                value={form.previous_returns}
                onChange={(e) =>
                  set("previous_returns", Number(e.target.value))
                }
              />
            </div>

            {/* COD Refusals */}
            <div>
              <label className="label">COD Refusals</label>

              <input
                className="input"
                type="number"
                min="0"
                value={form.cod_refusals}
                onChange={(e) =>
                  set("cod_refusals", Number(e.target.value))
                }
              />
            </div>

            {/* Account Age */}
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

            {/* IP Velocity */}
            <div>
              <label className="label">IP Velocity</label>

              <input
                className="input"
                type="number"
                min="0"
                value={form.ip_velocity}
                onChange={(e) =>
                  set("ip_velocity", Number(e.target.value))
                }
              />
            </div>

            {/* Device ID */}
            <div>
              <label className="label">Device ID</label>

              <input
                className="input"
                value={form.device_id}
                onChange={(e) =>
                  set("device_id", e.target.value)
                }
                placeholder="Optional"
              />
            </div>

            {/* IP Address */}
            <div>
              <label className="label">IP Address</label>

              <input
                className="input"
                value={form.ip_address}
                onChange={(e) =>
                  set("ip_address", e.target.value)
                }
                placeholder="Optional"
              />
            </div>

            {/* Checkboxes */}
            <div className="space-y-3">
              <label className="flex items-center gap-3 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={form.new_device}
                  onChange={(e) =>
                    set("new_device", e.target.checked)
                  }
                />
                New device
              </label>

              <label className="flex items-center gap-3 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={form.location_mismatch}
                  onChange={(e) =>
                    set("location_mismatch", e.target.checked)
                  }
                />
                Location mismatch
              </label>

              <label className="flex items-center gap-3 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={form.payment_risk_flag}
                  onChange={(e) =>
                    set("payment_risk_flag", e.target.checked)
                  }
                />
                Payment risk flag
              </label>
            </div>

            {/* Buttons */}
            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                className="btn-primary"
                disabled={loading}
              >
                {loading ? "Scoring..." : "Analyze Transaction"}
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

        {/* =========================
            RIGHT SIDE - RESULT
           ========================= */}
        <div className="card">
          {loading && (
            <LoadingSpinner label="Agent reasoning..." />
          )}

          {!loading && !result && (
            <div className="p-6">
              <p className="text-sm text-slate-400">
                Submit a transaction to see the agent's score,
                decision and full reasoning.
              </p>
            </div>
          )}

          {!loading && result && (
            <div className="space-y-5">
              {/* Score + Decision */}
              <div className="flex items-center justify-between">
                <RiskGauge
                  score={result.risk_score}
                  level={result.risk_level}
                />

                <div className="text-right">
                  <DecisionBadge
                    decision={
                      result.recommended_action ||
                      result.decision ||
                      "N/A"
                    }
                  />

                  {result.confidence !== undefined && (
                    <p className="mt-2 text-xs text-slate-500">
                      confidence{" "}
                      {(Number(result.confidence) * 100).toFixed(0)}%
                    </p>
                  )}

                  {result.model_version && (
                    <p className="text-xs text-slate-500">
                      {result.model_version}
                    </p>
                  )}

                  {result.audit_id && (
                    <p className="text-xs text-slate-500">
                      audit {result.audit_id}
                    </p>
                  )}
                </div>
              </div>

              {/* Reasons */}
              {Array.isArray(result.reasons) && (
                <div>
                  <p className="label">Why this decision</p>

                  <ul className="space-y-2">
                    {result.reasons.map((reason, index) => (
                      <li
                        key={index}
                        className="rounded-xl bg-white/5 px-3 py-2 text-sm text-slate-200"
                      >
                        {typeof reason === "string"
                          ? reason
                          : JSON.stringify(reason)}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Feature Contributions */}
              {Array.isArray(result.feature_contributions) && (
                <div>
                  <p className="label">
                    Feature contributions
                  </p>

                  {result.feature_contributions.map(
                    (feature, index) => {
                      const impact = Number(feature.impact) || 0;

                      return (
                        <div
                          key={`${feature.feature}-${index}`}
                          className="mb-3"
                        >
                          <div className="flex justify-between text-xs text-slate-400">
                            <span>{feature.feature}</span>

                            <span>
                              +{impact.toFixed(2)}
                            </span>
                          </div>

                          <div className="h-1.5 rounded-full bg-white/10">
                            <div
                              className="h-1.5 rounded-full bg-accent"
                              style={{
                                width: `${Math.min(
                                  Math.max(impact * 2, 0),
                                  100
                                )}%`,
                              }}
                            />
                          </div>
                        </div>
                      );
                    }
                  )}
                </div>
              )}

              {/* Recommended Action */}
              <p className="text-xs text-slate-500">
                Recommended action:{" "}
                {result.recommended_action ||
                  result.decision ||
                  "N/A"}

                {result.exposure_inr !== undefined && (
                  <>
                    {" "}
                    · exposure{" "}
                    {inr(Number(result.exposure_inr) || 0)}
                  </>
                )}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}