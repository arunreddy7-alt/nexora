import { useState } from "react";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import Dashboard from "./pages/Dashboard";
import "./styles.css";

type Screen = "landing" | "auth" | "dashboard";

export default function App() {
  const [screen, setScreen] = useState<Screen>("landing");

  if (screen === "auth") {
    return (
      <AuthPage
        onSuccess={() => setScreen("dashboard")}
        onBack={() => setScreen("landing")}
      />
    );
  }

  if (screen === "dashboard") {
    return (
      <Dashboard
        onLogout={() => {
          localStorage.removeItem("access_token");
          setScreen("landing");
        }}
      />
    );
  }

  return <LandingPage onLogin={() => setScreen("auth")} />;
}
