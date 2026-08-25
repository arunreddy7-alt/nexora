import { useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

export default function AuthPage({
  onSuccess,
  onBack,
}: {
  onSuccess: () => void;
  onBack: () => void;
}) {
  const [mode, setMode] =
    useState<"login" | "signup">("login");

  const [name, setName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [message, setMessage] =
    useState("");

  async function handleSubmit() {
    setError("");
    setMessage("");

    if (!email.trim() || !password.trim()) {
      setError(
        "Please enter your email and password."
      );
      return;
    }

    if (
      mode === "signup" &&
      !name.trim()
    ) {
      setError(
        "Please enter your name."
      );
      return;
    }

    setLoading(true);

    try {
      if (mode === "signup") {
        const response =
          await fetch(
            `${API_BASE_URL}/api/auth/register`,
            {
              method: "POST",
              headers: {
                "Content-Type":
                  "application/json",
              },
              body: JSON.stringify({
                name: name.trim(),
                email: email.trim(),
                password,
              }),
            }
          );

        const data =
          await response.json();

        if (!response.ok) {
          throw new Error(
            data?.detail ||
              data?.message ||
              "Registration failed."
          );
        }

        setMode("login");
        setPassword("");

        setMessage(
          "Account created successfully. Sign in to continue."
        );

        return;
      }

      const response =
        await fetch(
          `${API_BASE_URL}/api/auth/login`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              email: email.trim(),
              password,
            }),
          }
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            "Invalid email or password."
        );
      }

      if (!data?.access_token) {
        throw new Error(
          "Authentication succeeded but no access token was returned."
        );
      }

      localStorage.setItem(
        "access_token",
        data.access_token
      );

      onSuccess();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-screen">
      <div className="auth-background-grid" />

      <button
        className="auth-back-button"
        onClick={onBack}
      >
        ← Back
      </button>

      <div className="auth-layout">
        <section className="auth-intro">
          <div className="auth-brand">
            <span
              className="auth-brand-mark"
              aria-hidden="true"
            >
              <span className="auth-mark-line auth-mark-line-one" />
              <span className="auth-mark-line auth-mark-line-two" />
              <span className="auth-mark-core" />
            </span>

            <span>Nexora</span>
          </div>

          <div className="auth-intro-content">
            <div className="auth-eyebrow">
              MULTI-AGENT ENGINEERING
            </div>

            <h1>
              Build ideas
              <br />
              <span>into software.</span>
            </h1>

            <p>
              One workspace for planning,
              architecture, development,
              testing and deployment.
            </p>
          </div>

          <div className="auth-capabilities">
            <div>
              <strong>01</strong>
              <span>Plan</span>
            </div>

            <div>
              <strong>02</strong>
              <span>Build</span>
            </div>

            <div>
              <strong>03</strong>
              <span>Ship</span>
            </div>
          </div>
        </section>

        <section className="auth-form-panel">
          <div className="auth-card">
            <div className="auth-card-top">
              <div>
                <div className="auth-card-kicker">
                  {mode === "login"
                    ? "WELCOME BACK"
                    : "GET STARTED"}
                </div>

                <h2>
                  {mode === "login"
                    ? "Sign in"
                    : "Create account"}
                </h2>

                <p>
                  {mode === "login"
                    ? "Continue where you left off."
                    : "Start building with Nexora."}
                </p>
              </div>

              <div className="auth-status-mark">
                ✦
              </div>
            </div>

            <div className="auth-mode-switch">
              <button
                className={
                  mode === "login"
                    ? "active"
                    : ""
                }
                onClick={() => {
                  setMode("login");
                  setError("");
                  setMessage("");
                }}
              >
                Sign in
              </button>

              <button
                className={
                  mode === "signup"
                    ? "active"
                    : ""
                }
                onClick={() => {
                  setMode("signup");
                  setError("");
                  setMessage("");
                }}
              >
                Sign up
              </button>
            </div>

            <div className="auth-form">
              {mode === "signup" && (
                <div className="auth-field">
                  <label>
                    NAME
                  </label>

                  <input
                    type="text"
                    value={name}
                    onChange={(event) =>
                      setName(
                        event.target.value
                      )
                    }
                    placeholder="Your name"
                    autoComplete="name"
                  />
                </div>
              )}

              <div className="auth-field">
                <label>
                  EMAIL
                </label>

                <input
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(
                      event.target.value
                    )
                  }
                  placeholder="you@example.com"
                  autoComplete="email"
                />
              </div>

              <div className="auth-field">
                <label>
                  PASSWORD
                </label>

                <input
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(
                      event.target.value
                    )
                  }
                  onKeyDown={(event) => {
                    if (
                      event.key === "Enter"
                    ) {
                      handleSubmit();
                    }
                  }}
                  placeholder="••••••••"
                  autoComplete={
                    mode === "login"
                      ? "current-password"
                      : "new-password"
                  }
                />
              </div>

              {error && (
                <div className="auth-message error">
                  {error}
                </div>
              )}

              {message && (
                <div className="auth-message success">
                  {message}
                </div>
              )}

              <button
                className="auth-submit"
                onClick={handleSubmit}
                disabled={loading}
              >
                {loading
                  ? "Please wait..."
                  : mode === "login"
                  ? "Enter Nexora →"
                  : "Create account →"}
              </button>
            </div>

            <div className="auth-footer">
              <span>
                {mode === "login"
                  ? "New to Nexora?"
                  : "Already have an account?"}
              </span>

              <button
                onClick={() => {
                  setMode(
                    mode === "login"
                      ? "signup"
                      : "login"
                  );

                  setError("");
                  setMessage("");
                }}
              >
                {mode === "login"
                  ? "Create an account"
                  : "Sign in"}
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}