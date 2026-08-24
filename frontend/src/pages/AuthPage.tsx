import { useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

export default function AuthPage({
  onSuccess,
  onBack,
}: {
  onSuccess: () => void;
  onBack: () => void;
}) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit() {
    setMessage("");

    if (!email.trim() || !password.trim()) {
      setMessage("Enter your email and password.");
      return;
    }

    if (mode === "register" && !name.trim()) {
      setMessage("Enter your name.");
      return;
    }

    setLoading(true);

    try {
      if (mode === "register") {
        const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, password }),
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data?.detail || "Registration failed.");
        }

        setMode("login");
        setPassword("");
        setMessage("Account created. Sign in to continue.");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || "Invalid email or password.");
      }

      localStorage.setItem("access_token", data.access_token);
      onSuccess();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-glow" />

      <button className="back-button" onClick={onBack}>← Back to Nexora</button>

      <div className="auth-card">
        <div className="auth-brand">
          <span className="brand-mark">N</span>
          <span>Nexora</span>
        </div>

        <div className="auth-heading">
          <div className="section-kicker">// ACCESS PLATFORM</div>
          <h1>{mode === "login" ? "Welcome back." : "Create your account."}</h1>
          <p>
            {mode === "login"
              ? "Continue building with your engineering agents."
              : "Start turning ideas into working software."}
          </p>
        </div>

        {mode === "register" && (
          <input className="auth-input" placeholder="Full name" value={name} onChange={e => setName(e.target.value)} />
        )}

        <input className="auth-input" type="email" placeholder="Email address" value={email} onChange={e => setEmail(e.target.value)} />

        <input
          className="auth-input"
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter") submit(); }}
        />

        {message && <div className="auth-message">{message}</div>}

        <button className="auth-submit" onClick={submit} disabled={loading}>
          {loading ? "Working..." : mode === "login" ? "Sign in →" : "Create account →"}
        </button>

        <button
          className="switch-auth"
          onClick={() => {
            setMode(mode === "login" ? "register" : "login");
            setMessage("");
          }}
        >
          {mode === "login" ? "Don't have an account? Create one" : "Already have an account? Sign in"}
        </button>
      </div>
    </div>
  );
}
