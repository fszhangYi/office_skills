/** Snap value to step grid inside [min, max] (stable ± nudges). */
function clampRound(v, min, max, step) {
  const s = Number(step);
  const stepSafe = Number.isFinite(s) && s > 0 ? s : 0.001;
  let x = Math.min(max, Math.max(min, Number(v) || 0));
  x = Math.round(x / stepSafe) * stepSafe;
  x = Math.min(max, Math.max(min, x));
  const decimals = Math.min(8, Math.max(0, Math.ceil(-Math.log10(stepSafe) + 1e-12)));
  return Number(x.toFixed(decimals));
}

function NudgeSliderRow({
  label, value, min, max, step, digits, onChange, style,
}) {
  const stepSafe = Number(step) > 0 ? Number(step) : 0.001;
  const shown = Number(value) || 0;
  const setClamped = (v) => onChange(clampRound(v, min, max, stepSafe));
  return (
    <div className="arm-joint-row with-nudge" style={style}>
      <span className="lab">{label}</span>
      <Slider
        min={min}
        max={max}
        step={stepSafe}
        value={shown}
        onChange={setClamped}
      />
      <span className="arm-joint-nudge">
        <Button size="small" onClick={() => setClamped(shown - stepSafe)}>−</Button>
        <Button size="small" onClick={() => setClamped(shown + stepSafe)}>+</Button>
      </span>
      <span className="arm-joint-val">{shown.toFixed(digits)}</span>
    </div>
  );
}

function StepControls({ xyzStep, rpyStep, onXyzStep, onRpyStep, xyzMin = 0.0001, rpyMin = 0.01 }) {
  return (
    <div className="arm-step-row">
      <span className="arm-step-item">
        <span>XYZ step (m)</span>
        <InputNumber
          size="small"
          min={xyzMin}
          max={0.1}
          step={xyzMin}
          value={xyzStep}
          onChange={(v) => {
            const n = Number(v);
            if (Number.isFinite(n) && n > 0) onXyzStep(n);
          }}
          style={{ width: 92 }}
        />
      </span>
      <span className="arm-step-item">
        <span>RPY step (°)</span>
        <InputNumber
          size="small"
          min={rpyMin}
          max={30}
          step={rpyMin}
          value={rpyStep}
          onChange={(v) => {
            const n = Number(v);
            if (Number.isFinite(n) && n > 0) onRpyStep(n);
          }}
          style={{ width: 84 }}
        />
      </span>
    </div>
  );
}
