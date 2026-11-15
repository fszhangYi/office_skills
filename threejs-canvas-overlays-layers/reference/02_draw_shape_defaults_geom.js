function defaultDrawShape(type = "box") {
  const t = type === "sphere" || type === "cylinder" ? type : "box";
  const base = {
    id: newDrawId(t),
    type: t,
    label: t === "box" ? "长方体" : t === "sphere" ? "球体" : "圆柱",
    color: t === "box" ? "#5b8ff9" : t === "sphere" ? "#61ddaa" : "#f6bd16",
    opacity: 0.55,
    enabled: true,
    offset_m: [0.4, 0.0, 0.35],
    offset_rpy_deg: [0, 0, 0],
  };
  if (t === "sphere") base.radius_m = 0.05;
  else if (t === "cylinder") {
    base.radius_m = 0.04;
    base.height_m = 0.1;
  } else {
    base.size_m = [0.1, 0.08, 0.05];
  }
  return base;
}

function defaultDrawLayer(label) {
  const n = Math.max(1, Number(String(label || "").replace(/\D/g, "")) || 1);
  return {
    id: newDrawId("layer"),
    label: label || `绘制层 ${n}`,
    enabled: true,
    shapes: [],
  };
}

function makeShapeGeometry(shape) {
  const t = shape?.type || "box";
  if (t === "sphere") {
    const r = Math.max(1e-4, Number(shape.radius_m) || 0.05);
    return new THREE.SphereGeometry(r, 32, 24);
  }
  if (t === "cylinder") {
    const r = Math.max(1e-4, Number(shape.radius_m) || 0.04);
    const h = Math.max(1e-4, Number(shape.height_m) || 0.1);
    const g = new THREE.CylinderGeometry(r, r, h, 32);
    g.rotateX(Math.PI / 2); // height along ROS Z before Rx(-90°)
    return g;
  }
  const s = Array.isArray(shape.size_m) ? shape.size_m : [0.1, 0.08, 0.05];
  return new THREE.BoxGeometry(
    Math.max(1e-4, Number(s[0]) || 0.1),
    Math.max(1e-4, Number(s[1]) || 0.08),
    Math.max(1e-4, Number(s[2]) || 0.05),
  );
}

export default function ArmPanel({ active }) {
  const hostRef = useRef(null);
  const threeRef = useRef({});
  const modelRef = useRef(null);
  const liveJointsRef = useRef([0, 0, 0, 0, 0, 0]);
  const previewJointsRef = useRef([0, 0, 0, 0, 0, 0]);
