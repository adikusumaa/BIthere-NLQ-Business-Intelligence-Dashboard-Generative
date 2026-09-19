export default function Step6KnowledgeBase({ onNext, onBack }) {
  return (
    <div>
      <h2>Step 6 — Knowledge Base (TODO)</h2>
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button onClick={onBack}>Back</button>
        <button onClick={onNext}>Finish</button>
      </div>
    </div>
  );
}