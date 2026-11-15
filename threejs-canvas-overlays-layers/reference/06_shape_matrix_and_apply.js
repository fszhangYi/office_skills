  const buildShapeMatrix = (shape) => {
    const off = shape.offset_m || [0, 0, 0];
    const orpy = (shape.offset_rpy_deg || [0, 0, 0]).map((d) => (Number(d) * Math.PI) / 180);
    const Roff = new THREE.Matrix4().makeRotationFromEuler(
      new THREE.Euler(orpy[0] || 0, orpy[1] || 0, orpy[2] || 0, "XYZ"),
    );
    const Toff = new THREE.Matrix4().makeTranslation(
      Number(off[0]) || 0,
      Number(off[1]) || 0,
      Number(off[2]) || 0,
    );
    const Rx = new THREE.Matrix4().makeRotationX(-Math.PI / 2);
    const m = new THREE.Matrix4();
    m.identity();
    m.multiply(Rx);
    m.multiply(Toff);
    m.multiply(Roff);
    return m;
  };

  const applyDrawShapes = (cfg, selectedId, opts = {}) => {
    const t = threeRef.current;
    if (!t?.drawShapes || !cfg) return;
    const root = t.drawShapes;
    const show = opts.visible !== undefined ? !!opts.visible : drawVisibleRef.current;
    root.visible = !!cfg.enabled && show;
    const sel = selectedId !== undefined ? selectedId : activeShapeId;
    const layers = cfg.layers || [];
    root.children.forEach((layerG) => {
      const L = layers.find((x) => x.id === layerG.name);
      if (!L) {
        layerG.visible = false;
        return;
      }
      layerG.visible = !!L.enabled;
      const shapes = L.shapes || [];
      layerG.children.forEach((mesh) => {
        const s = shapes.find((x) => x.id === mesh.name);
        if (!s) {
          mesh.visible = false;
          return;
        }
        mesh.visible = !!s.enabled;
        mesh.matrixAutoUpdate = false;
        mesh.matrix.copy(buildShapeMatrix(s));
        mesh.updateMatrixWorld(true);
        if (mesh.material) {
          const selected = sel && s.id === sel;
          const baseOp = Number(s.opacity ?? 0.55);
          mesh.material.opacity = selected ? Math.min(0.95, baseOp + 0.18) : baseOp;
          if (s.color) mesh.material.color.set(s.color);
          if (mesh.material.emissive) {
            mesh.material.emissive.set(selected ? s.color || "#ffffff" : "#000000");
            mesh.material.emissiveIntensity = selected ? 0.2 : 0;
          }
          mesh.material.needsUpdate = true;
        }
      });
    });
  };
