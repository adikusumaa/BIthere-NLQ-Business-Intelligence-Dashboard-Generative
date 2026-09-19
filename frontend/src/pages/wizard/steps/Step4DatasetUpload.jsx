export default function Step4DatasetUpload({ onNext, onBack }) {
  return (
    <div>
      <h2>Step 4 — Dataset Upload (TODO)</h2>
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button onClick={onBack}>Back</button>
        <button onClick={onNext}>Next</button>
      </div>
    </div>
  );
}