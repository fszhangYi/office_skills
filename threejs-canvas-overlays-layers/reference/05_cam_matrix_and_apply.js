  const buildCamMatrix = (cam) => {
    const scale = Number(cam.scale ?? (cam.units_of_file === "mm" ? 0.001 : 1));
    const off = cam.offset_m || [0, 0, 0];
    const orpy = (cam.offset_rpy_deg || [0, 0, 0]).map((d) => (Number(d) * Math.PI) / 180);
    const S = new THREE.Matrix4().makeScale(scale, scale, scale);
    const Roff = new THREE.Matrix4().makeRotationFromEuler(
      new THREE.Euler(orpy[0] || 0, orpy[1] || 0, orpy[2] || 0, "XYZ"),
    );
    const Toff = new THREE.Matrix4().makeTranslation(
      Number(off[0]) || 0,
      Number(off[1]) || 0,
      Number(off[2]) || 0,
    );
    // Same Rx(-90°) as URDF / scene overlay (ROS Z-up → Three Y-up)
    const Rx = new THREE.Matrix4().makeRotationX(-Math.PI / 2);
    const m = new THREE.Matrix4();
    m.identity();
    m.multiply(Rx);
    m.multiply(Toff);
    m.multiply(Roff);
    m.multiply(S);
    return m;
  };

  const disposeObject3D = (root) => {
    if (!root) return;
    root.traverse((obj) => {
      if (obj.geometry && !obj.geometry.__rsShared) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose());
        else obj.material.dispose();
      }
    });
  };

  const styleCamMaterials = (group, cfg, selectedId) => {
    if (!group || !cfg) return;
    const cams = cfg.cameras || [];
    group.children.forEach((child) => {
      const cam = cams.find((c) => c.id === child.name);
      if (!cam || !child.isMesh || !child.material) return;
      const selected = selectedId && cam.id === selectedId;
      const baseOp = Number(cam.opacity ?? cfg.opacity ?? 0.72);
      child.material.opacity = selected ? Math.min(0.95, baseOp + 0.15) : baseOp;
      if (cam.color) child.material.color.set(cam.color);
      if (child.material.emissive) {
        child.material.emissive.set(selected ? cam.color || "#ffffff" : "#000000");
        child.material.emissiveIntensity = selected ? 0.22 : 0;
      }
      child.material.needsUpdate = true;
      child.visible = !!cam.enabled;
    });
  };

  const applyCamMatrices = (cfg, selectedId, opts = {}) => {
    const t = threeRef.current;
    if (!t?.cameraOverlays || !cfg) return;
    const cams = cfg.cameras || [];
    const show = opts.visible !== undefined ? !!opts.visible : camOverlayVisibleRef.current;
    t.cameraOverlays.visible = !!cfg.enabled && show;
    t.cameraOverlays.children.forEach((child) => {
      const cam = cams.find((c) => c.id === child.name);
      if (!cam) return;
      child.matrixAutoUpdate = false;
      child.matrix.copy(buildCamMatrix(cam));
      child.updateMatrixWorld(true);
    });
    styleCamMaterials(t.cameraOverlays, cfg, selectedId ?? activeCamId);
  };
