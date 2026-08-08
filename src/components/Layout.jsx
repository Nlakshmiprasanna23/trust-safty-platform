import { NavLink, useNavigate } from "react-router-dom";
import { LayoutDashboard, ShieldAlert, BadgeCheck, MessagesSquare, FolderKanban, ScrollText, BarChart3, PlayCircle, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/risk", label: "Risk Scoring", icon: ShieldAlert },
  { to: "/authenticity", label: "Authenticity", icon: BadgeCheck },
  { to: "/reviews", label: "Review Moderation", icon: MessagesSquare },
  { to: "/cases", label: "Case Management", icon: FolderKanban },
  { to: "/audit", label: "Audit Trail", icon: ScrollText },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/demo", label: "Demo Mode", icon: PlayCircle },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 border-r border-white/10 bg-navy-800/60 p-4 lg:block">
        <div className="mb-8 px-2">
          <p className="text-lg font-extrabold text-white">Trust<span className="text-accent">Guard</span></p>
          <p className="text-[11px] uppercase tracking-widest text-slate-500">Multi-Agent T&amp;S</p>
        </div>
        <nav className="space-y-1">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end}
              className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${isActive ? "bg-accent/15 text-accent" : "text-slate-300 hover:bg-white/5"}`}>
              <Icon size={17} /> {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-white/10 bg-navy-800/40 px-6 py-3 backdrop-blur">
          <span className="chip bg-emerald-500/15 text-emerald-300">3 agents online</span>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm text-white">{user?.full_name || user?.email}</p>
              <p className="text-[11px] uppercase text-slate-500">{user?.role}</p>
            </div>
            <button className="btn-ghost" onClick={() => { logout(); navigate("/login"); }}>
              <LogOut size={15} /> Logout
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-x-hidden p-6">{children}</main>
      </div>
    </div>
  );
}
