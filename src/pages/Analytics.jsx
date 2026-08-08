import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import useApi from "../hooks/useApi";
import { endpoints } from "../services/api";
import { PageHeader, ChartCard, LoadingSpinner, ErrorState, DashboardCard, DataTable } from "../components";
import { inr, pct } from "../utils/format";

export default function Analytics() {
  const { data, loading, error, refresh } = useApi(() => endpoints.analytics(), []);
  const fairness = useApi(() => endpoints.fairness(), []);
  const metrics = useApi(() => endpoints.modelMetrics(), []);
  const cost = useApi(() => endpoints.cost(), []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;

  return (
    <>
      <PageHeader title="Analytics & Model Governance" subtitle="Performance, fairness, drift and unit economics" />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <DashboardCard label="Detection precision" value={pct((metrics.data?.risk?.precision || 0) * 100)} sub="Risk agent" demo />
        <DashboardCard label="Detection recall" value={pct((metrics.data?.risk?.recall || 0) * 100)} sub="Risk agent" demo />
        <DashboardCard label="False positive rate" value={pct(data.false_positive_rate)} sub="All agents" demo />
        <DashboardCard label="Cost per 1k decisions" value={inr(cost.data?.cost_per_1k_inr || 0)} sub="Compute + review" demo />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <ChartCard title="Precision / recall by agent">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.agent_performance}>
              <CartesianGrid stroke="#1c2745" vertical={false} />
              <XAxis dataKey="agent" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: "#0c1225", border: "1px solid #24304f", borderRadius: 12 }} />
              <Bar dataKey="precision" fill="#ff7a1a" radius={[6, 6, 0, 0]} />
              <Bar dataKey="recall" fill="#38bdf8" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Model drift monitor" subtitle="Population stability index over time">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={data.drift}>
              <CartesianGrid stroke="#1c2745" vertical={false} />
              <XAxis dataKey="week" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: "#0c1225", border: "1px solid #24304f", borderRadius: 12 }} />
              <Line dataKey="psi" stroke="#fbbf24" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="mt-6">
        <ChartCard title="Fairness monitor" subtitle="Flag rates across geography and seller tiers — disparate impact watch">
          {fairness.loading ? <LoadingSpinner /> : (
            <DataTable
              columns={[
                { key: "segment", label: "Segment" },
                { key: "volume", label: "Volume" },
                { key: "flag_rate", label: "Flag rate", render: (r) => pct(r.flag_rate) },
                { key: "disparity", label: "Disparity ratio", render: (r) => r.disparity.toFixed(2) },
                { key: "status", label: "Status" },
              ]}
              rows={fairness.data?.segments || []}
            />
          )}
        </ChartCard>
      </div>
    </>
  );
}
