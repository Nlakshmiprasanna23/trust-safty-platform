import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

export default function Login() {
  const { login } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@trustsafety.local");
  const [password, setPassword] = useState("Admin@123");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast("Signed in successfully", "success");
      navigate("/");
    } catch (err) {
      toast(err.message, "error");
    } finally { setLoading(false); }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={submit} className="card w-full max-w-md">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-xl bg-accent/15 p-2.5 text-accent"><ShieldCheck /></div>
          <div>
            <h1 className="text-xl">TrustGuard Console</h1>
            <p className="text-xs text-slate-400">Multi-agent fraud, review &amp; counterfeit defense</p>
          </div>
        </div>
        <label className="label">Email</label>
        <input className="input mb-4" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label className="label">Password</label>
        <input className="input mb-6" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button className="btn-primary w-full justify-center" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </button>
        <div className="mt-5 rounded-xl bg-white/5 p-3 text-xs text-slate-400">
          <p className="font-semibold text-slate-300">Demo accounts</p>
          <p>admin@trustsafety.local / Admin@123</p>
          <p>analyst@trustsafety.local / Analyst@123</p>
        </div>
      </form>
    </div>
  );
}
