export default function Step5SchemaBuilder({ onNext, onBack }) {
  return (
    <div>
      <h2>Step 5 — Schema Builder (TODO)</h2>
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button onClick={onBack}>Back</button>
        <button onClick={onNext}>Next</button>
      </div>
    </div>
  );
}