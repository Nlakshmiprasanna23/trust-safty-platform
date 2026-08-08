import { createContext, useContext, useEffect, useState } from "react";
import { endpoints } from "../services/api";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem("ts_user");
    if (raw && localStorage.getItem("ts_token")) setUser(JSON.parse(raw));
    setReady(true);
  }, []);

  const login = async (email, password) => {
    const data = await endpoints.login({ email, password });
    localStorage.setItem("ts_token", data.access_token);
    const profile = { email: data.email, role: data.role, full_name: data.full_name };
    localStorage.setItem("ts_user", JSON.stringify(profile));
    setUser(profile);
    return profile;
  };

  const logout = () => {
    localStorage.removeItem("ts_token");
    localStorage.removeItem("ts_user");
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, login, logout, ready }}>{children}</AuthContext.Provider>;
}
