import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { useWizardStore, WIZARD_STEPS } from "../../store/wizardStore";
import { useWorkspaceStore } from "../../store/workspaceStore";
import Step1Account from "./steps/Step1Account.jsx";
import Step2ApiKeys from "./steps/Step2ApiKeys.jsx";
import Step3DataSource from "./steps/Step3DataSource.jsx";
import Step4DatasetUpload from "./steps/Step4DatasetUpload.jsx";
import Step5SchemaBuilder from "./steps/Step5SchemaBuilder.jsx";
import Step6KnowledgeBase from "./steps/Step6KnowledgeBase.jsx";

export default function SetupWizard() {
  const navigate = useNavigate();
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const currentStep = useWizardStore((s) => s.currentStep);
  const setStep = useWizardStore((s) => s.setStep);
  const loadState = useWizardStore((s) => s.loadState);
  const completedSteps = useWizardStore((s) => s.completedSteps);
  const setupCompleted = useWizardStore((s) => s.setupCompleted);

  useEffect(() => {
    if (activeWorkspace?.id) {
      loadState(activeWorkspace.id);
    }
  }, [activeWorkspace?.id, loadState]);

  if (!activeWorkspace) {
    return (
      <div style={{ padding: 32 }}>
        <h2>No workspace selected</h2>
        <p>Please create or select a workspace first.</p>
        <button onClick={() => navigate("/chat")}>Back to Chat</button>
      </div>
    );
  }

  const goNext = () => {
    if (currentStep < WIZARD_STEPS.length) setStep(currentStep + 1);
  };
  const goBack = () => {
    if (currentStep > 1) setStep(currentStep - 1);
  };

  const renderStep = () => {
    const props = { onNext: goNext, onBack: goBack };
    switch (currentStep) {
      case 1: return <Step1Account {...props} />;
      case 2: return <Step2ApiKeys {...props} />;
      case 3: return <Step3DataSource {...props} />;
      case 4: return <Step4DatasetUpload {...props} />;
      case 5: return <Step5SchemaBuilder {...props} />;
      case 6: return <Step6KnowledgeBase {...props} />;
      default: return null;
    }
  };

  return (
    <div style={{ minHeight: "100vh", padding: "32px 24px", background: "var(--ios-bg)" }}>
      <div style={{ maxWidth: 900, margin: "0 auto" }}>
        <header style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, marginBottom: 4 }}>Setup Wizard</h1>
          <p style={{ color: "var(--ios-text-secondary)", fontSize: 14 }}>
            Workspace: <strong>{activeWorkspace.name}</strong>
            {setupCompleted && " — Setup complete"}
          </p>
        </header>

        {/* Stepper */}
        <div style={{ display: "flex", gap: 8, marginBottom: 32, flexWrap: "wrap" }}>
          {WIZARD_STEPS.map((s) => {
            const isActive = s.id === currentStep;
            const isDone = completedSteps[s.id];
            return (
              <button
                key={s.id}
                onClick={() => setStep(s.id)}
                style={{
                  padding: "8px 14px",
                  borderRadius: 8,
                  border: "1px solid",
                  borderColor: isActive ? "#3b82f6" : "#374151",
                  background: isActive ? "#3b82f6" : isDone ? "#10b981" : "transparent",
                  color: isActive || isDone ? "white" : "inherit",
                  cursor: "pointer",
                  fontSize: 13,
                }}
              >
                {s.id}. {s.title} {isDone && !isActive ? "✓" : ""}
              </button>
            );
          })}
        </div>

        <div
          style={{
            background: "rgba(255,255,255,0.03)",
            border: "1px solid #374151",
            borderRadius: 12,
            padding: 24,
          }}
        >
          {renderStep()}
        </div>
      </div>
    </div>
  );
}