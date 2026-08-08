import { ShieldAlert, BadgeCheck, MessagesSquare } from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

import useApi from "../hooks/useApi";
import { endpoints } from "../services/api";

import {
  DashboardCard,
  ChartCard,
  LoadingSpinner,
  ActivityFeed,
  AgentStatusCard,
} from "../components";

import { pct } from "../utils/format";

const COLORS = ["#34d399", "#fbbf24", "#fb923c", "#fb7185"];

export default function Dashboard() {
  const {
    data,
    loading,
    error,
  } = useApi(() => endpoints.stats(), []);

  const activity = useApi(() => endpoints.activity(), []);

  // Always have a safe object even if the API has not returned data yet.
  const stats = data || {};

  // Always use arrays for chart components.
  const timeseries = Array.isArray(stats.timeseries)
    ? stats.timeseries
    : [];

  const riskDistribution = Array.isArray(stats.risk_distribution)
    ? stats.risk_distribution
    : [];

  const categoryHotspots = Array.isArray(stats.category_hotspots)
    ? stats.category_hotspots
    : [];

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-5 text-red-300">
          <h2 className="text-lg font-semibold">Unable to load dashboard</h2>
          <p className="mt-2 text-sm">
            {error.message || "Something went wrong while loading dashboard data."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Summary cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <DashboardCard
          icon={ShieldAlert}
          label="Transactions screened"
          value={stats.transactions_screened ?? 0}
          sub={`${stats.high_risk_blocked ?? 0} high-risk actions`}
          demo
        />

        <DashboardCard
          icon={MessagesSquare}
          label="Fake reviews detected"
          value={stats.fake_reviews_detected ?? 0}
          sub={`${stats.review_rings ?? 0} coordinated rings`}
          demo
        />

        <DashboardCard
          icon={BadgeCheck}
          label="Counterfeits flagged"
          value={stats.counterfeits_flagged ?? 0}
          sub={`${pct(stats.counterfeit_rate ?? 0)} of listings`}
          demo
        />
      </div>

      {/* Charts */}
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <ChartCard
          title="Fraud attempts over time"
          subtitle="Daily screened vs blocked"
        >
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={timeseries}>
              <CartesianGrid
                stroke="#1c2745"
                vertical={false}
              />

              <XAxis
                dataKey="date"
                stroke="#64748b"
                fontSize={11}
              />

              <YAxis
                stroke="#64748b"
                fontSize={11}
              />

              <Tooltip
                contentStyle={{
                  background: "#0c1225",
                  border: "1px solid #24304f",
                  borderRadius: 12,
                }}
              />

              <Area
                type="monotone"
                dataKey="screened"
                stroke="#38bdf8"
                fill="#38bdf822"
              />

              <Area
                type="monotone"
                dataKey="blocked"
                stroke="#ff7a1a"
                fill="#ff7a1a33"
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Risk distribution"
          subtitle="Share of decisions by band"
        >
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={riskDistribution}
                dataKey="value"
                nameKey="name"
                innerRadius={55}
                outerRadius={90}
                paddingAngle={3}
              >
                {riskDistribution.map((_, i) => (
                  <Cell
                    key={i}
                    fill={COLORS[i % COLORS.length]}
                  />
                ))}
              </Pie>

              <Tooltip
                contentStyle={{
                  background: "#0c1225",
                  border: "1px solid #24304f",
                  borderRadius: 12,
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Category hotspots"
          subtitle="Flagged listings per category"
        >
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={categoryHotspots}>
              <CartesianGrid
                stroke="#1c2745"
                vertical={false}
              />

              <XAxis
                dataKey="category"
                stroke="#64748b"
                fontSize={11}
              />

              <YAxis
                stroke="#64748b"
                fontSize={11}
              />

              <Tooltip
                contentStyle={{
                  background: "#0c1225",
                  border: "1px solid #24304f",
                  borderRadius: 12,
                }}
              />

              <Bar
                dataKey="flagged"
                fill="#ff7a1a"
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Agents */}
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <AgentStatusCard
          name="Risk Scoring Agent"
          detail="Rule engine + gradient boosting"
        />

        <AgentStatusCard
          name="Authenticity Agent"
          detail="CV proxy + text & price signals"
        />

        <AgentStatusCard
          name="Review Moderation Agent"
          detail="TF-IDF + ring graph analysis"
        />
      </div>

      {/* Activity */}
      <div className="mt-6">
        <ChartCard
          title="Live agent activity"
          subtitle="Most recent orchestrator decisions"
        >
          {activity.loading ? (
            <LoadingSpinner />
          ) : activity.error ? (
            <div className="p-4 text-sm text-red-300">
              Unable to load activity.
            </div>
          ) : (
            <ActivityFeed
              items={activity.data?.items || []}
            />
          )}
        </ChartCard>
      </div>
    </div>
  );
}