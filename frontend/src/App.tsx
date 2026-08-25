import { useState } from "react";
import AuthPage from "./pages/AuthPage";
import Dashboard from "./pages/Dashboard";
import "./styles.css";

type Screen = "auth" | "dashboard";

export default function App() {
  const [screen, setScreen] =
    useState<Screen>(
      localStorage.getItem("access_token")
        ? "dashboard"
        : "auth"
    );

  if (screen === "auth") {
    return (
      <AuthPage
        onSuccess={() =>
          setScreen("dashboard")
        }
        onBack={() =>
          setScreen("auth")
        }
      />
    );
  }

  return (
    <Dashboard
      onLogout={() => {
        localStorage.removeItem(
          "access_token"
        );

        setScreen("auth");
      }}
    />
  );
}