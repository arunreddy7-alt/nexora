import { useEffect, useState } from "react";

export default function LandingPage({ onLogin }: { onLogin: () => void }) {
  const [rotation, setRotation] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => setRotation(v => v + 1), 40);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="landing">
      <div className="landing-grid" />
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <div className="light-ribbon ribbon-one" />
      <div className="light-ribbon ribbon-two" />
      <div className="light-ribbon ribbon-three" />

      <header className="landing-nav">
        <div className="brand">
          <span className="brand-mark">N</span>
          <span>Nexora</span>
        </div>

        <div className="nav-actions">
          <span className="nav-status">
            <span className="live-dot" />
            AI ENGINEERING PLATFORM
          </span>
          <button className="ghost-button" onClick={onLogin}>Login</button>
        </div>
      </header>

      <div className="telemetry telemetry-left">
        <div>// NEXORA AGENT · LIVE RUN</div>
        <div>RESEARCHED 412 ACCOUNTS</div>
        <div>UPDATED 1,068 FIELDS</div>
        <div>DRAFTED 240 FOLLOW-UPS</div>
        <div>PREPPED 96 MEETINGS</div>
        <div>// DAY 14 OF 20 · STILL RUNNING</div>
      </div>

      <div className="telemetry telemetry-right">
        <div>// AGENT · LIVE RUN</div>
        <div>PROPOSED 240 ACTIONS</div>
        <div>APPROVED 218 · REJECTED 22</div>
        <div>EVERY DECISION = 1 TRAINING SIGNAL</div>
        <div>MODEL UPDATED 218 TIMES</div>
        <div>LEARNING NEVER FORGETS</div>
      </div>

      <main className="hero">
        <div className="hero-orbit">
          <div
            className="core-3d"
            style={{ transform: `rotateX(58deg) rotateZ(${rotation * 0.8}deg)` }}
          />
        </div>

        <div className="hero-copy">
          <div className="eyebrow">✦ MULTI-AGENT SOFTWARE ENGINEERING</div>

          <h1>
            Superintelligence
            <br />
            <span>for software creation</span>
          </h1>

          <p>
            Systems that compound AI engineering and deploy it at scale.
            Every decision, action, and outcome informs the next.
          </p>

          <div className="hero-actions">
            <button className="primary-button" onClick={onLogin}>
              Start building <span>→</span>
            </button>
            <button className="light-button" onClick={onLogin}>Login</button>
          </div>

          <button
            className="learn-more"
            onClick={() => document.getElementById("platform")?.scrollIntoView({ behavior: "smooth" })}
          >
            LEARN MORE
            <span>↓</span>
          </button>
        </div>
      </main>

      <section id="platform" className="landing-section">
        <div className="section-kicker">// THE NEXORA SYSTEM</div>
        <h2>From an idea<br /><span>to working software.</span></h2>
        <p className="section-lead">
          A coordinated engineering system that turns natural-language
          requirements into tested, runnable applications.
        </p>

        <div className="feature-grid">
          <Feature number="01" title="Plan" text="Understand the product, requirements, constraints and expected outcomes." />
          <Feature number="02" title="Architect" text="Design the technical architecture, services, data model and APIs." />
          <Feature number="03" title="Build" text="Generate the application, connect the pieces and create a runnable workspace." />
          <Feature number="04" title="Validate" text="Run tests, build checks and automated fixes before exposing the preview." />
        </div>
      </section>

      <section className="system-section">
        <div className="system-visual">
          <div className="system-ring ring-a" />
          <div className="system-ring ring-b" />
          <div className="system-ring ring-c" />
          <div className="system-center">N</div>
        </div>

        <div className="system-copy">
          <div className="section-kicker">// AGENT ORCHESTRATION</div>
          <h2>One request.<br /><span>Multiple specialists.</span></h2>
          <p>
            Nexora coordinates product thinking, architecture, development,
            testing and build execution as one continuous engineering flow.
          </p>

          <div className="mini-list">
            <div><b>CEO</b><span>Direction & product intent</span></div>
            <div><b>PM</b><span>Requirements & acceptance criteria</span></div>
            <div><b>ARCHITECT</b><span>Systems & technical design</span></div>
            <div><b>DEVELOPER</b><span>Implementation & integration</span></div>
            <div><b>TEST</b><span>Quality & regression checks</span></div>
            <div><b>BUILD</b><span>Runnable application preview</span></div>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="section-kicker">// READY WHEN YOU ARE</div>
        <h2>Build the next thing.</h2>
        <p>Turn a sentence into a working software project.</p>
        <button className="primary-button" onClick={onLogin}>
          Enter Nexora <span>→</span>
        </button>
      </section>

      <footer className="landing-footer">
        <div className="brand"><span className="brand-mark">N</span><span>Nexora</span></div>
        <span>AI Engineering Platform</span>
        <span>© 2026 Nexora</span>
      </footer>
    </div>
  );
}

function Feature({ number, title, text }: { number: string; title: string; text: string }) {
  return (
    <article className="feature-card">
      <span>{number}</span>
      <h3>{title}</h3>
      <p>{text}</p>
    </article>
  );
}
