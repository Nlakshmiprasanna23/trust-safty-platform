import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Layout from "./components/Layout.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import RiskScoring from "./pages/RiskScoring.jsx";
import Authenticity from "./pages/Authenticity.jsx";
import ReviewModeration from "./pages/ReviewModeration.jsx";
import CaseManagement from "./pages/CaseManagement.jsx";
import AuditTrail from "./pages/AuditTrail.jsx";
import Analytics from "./pages/Analytics.jsx";
import DemoMode from "./pages/DemoMode.jsx";

function Protected({ children }) {
  const { user, ready } = useAuth();
  if (!ready) return null;
  return user ? <Layout>{children}</Layout> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Protected><Dashboard /></Protected>} />
      <Route path="/risk" element={<Protected><RiskScoring /></Protected>} />
      <Route path="/authenticity" element={<Protected><Authenticity /></Protected>} />
      <Route path="/reviews" element={<Protected><ReviewModeration /></Protected>} />
      <Route path="/cases" element={<Protected><CaseManagement /></Protected>} />
      <Route path="/audit" element={<Protected><AuditTrail /></Protected>} />
      <Route path="/analytics" element={<Protected><Analytics /></Protected>} />
      <Route path="/demo" element={<Protected><DemoMode /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
