export default function Step3DataSource({ onNext, onBack }) {
  return (
    <div>
      <h2>Step 3 — Data Source (TODO)</h2>
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button onClick={onBack}>Back</button>
        <button onClick={onNext}>Next</button>
      </div>
    </div>
  );
}