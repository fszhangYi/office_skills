  const setCamGroupShown = async (show) => {
    const on = !!show;
    camOverlayVisibleRef.current = on;
    setCamOverlayVisible(on);
    if (!camOverlayCfg) return;
    if (on) {
      const next = { ...camOverlayCfg, enabled: true };
      if (!camOverlayCfg.enabled) setCamOverlayCfg(next);
      if (!threeRef.current?.cameraOverlays) {
        await loadCameraOverlays(next, { selectedId: activeCamId, visible: true });
      } else {
        applyCamMatrices(next, activeCamId, { visible: true });
      }
    } else if (threeRef.current?.cameraOverlays) {
      threeRef.current.cameraOverlays.visible = false;
    }
  };

  const setCamLayerShown = (camId, show) => {
    if (!camOverlayCfg) return;
    const cameras = (camOverlayCfg.cameras || []).map((c) =>
      c.id === camId ? { ...c, enabled: !!show } : c,
    );
    const next = { ...camOverlayCfg, cameras };
    setCamOverlayCfg(next);
    applyCamMatrices(next, activeCamId);
  };

  const setDrawGroupShown = async (show) => {
    const on = !!show;
    drawVisibleRef.current = on;
    setDrawVisible(on);
    if (!drawCfg) return;
    if (on) {
      const next = { ...drawCfg, enabled: true };
      if (!drawCfg.enabled) setDrawCfg(next);
      if (!threeRef.current?.drawShapes) {
        await loadDrawShapes(next, { visible: true });
      } else {
        applyDrawShapes(next, undefined, { visible: true });
      }
    } else if (threeRef.current?.drawShapes) {
      threeRef.current.drawShapes.visible = false;
    }
  };

  const setDrawLayerShown = (layerId, show) => {
    if (!drawCfg) return;
    const layers = (drawCfg.layers || []).map((L) =>
      L.id === layerId ? { ...L, enabled: !!show } : L,
    );
    const next = { ...drawCfg, layers };
    setDrawCfg(next);
    applyDrawShapes(next);
  };

  const setDrawShapeShown = (layerId, shapeId, show) => {
    if (!drawCfg) return;
    const layers = (drawCfg.layers || []).map((L) => {
      if (L.id !== layerId) return L;
      return {
        ...L,
        shapes: (L.shapes || []).map((s) =>
          s.id === shapeId ? { ...s, enabled: !!show } : s,
        ),
      };
    });
    const next = { ...drawCfg, layers };
    setDrawCfg(next);
    applyDrawShapes(next);
  };

  /** Toggle visibility of a canvas model layer (does not persist config). */
  const setLayerVisible = (layerId, show) => {
    if (layerId === "robot") setRobotShown(show);
    else if (layerId === "ghost") setGhostShown(show);
    else if (layerId === "scene") setSceneLayerShown(show);
    else if (layerId === "cam_group") setCamGroupShown(show);
    else if (layerId === "draw_group") setDrawGroupShown(show);
    else if (layerId === "markers") setMarkersShown(show);
    else if (layerId === "tcp") setTcpShown(show);
    else if (layerId.startsWith("cam:")) setCamLayerShown(layerId.slice(4), show);
    else if (layerId.startsWith("draw_layer:")) setDrawLayerShown(layerId.slice(11), show);
    else if (layerId.startsWith("draw_shape:")) {
      const rest = layerId.slice(11);
      const idx = rest.indexOf(":");
      if (idx > 0) setDrawShapeShown(rest.slice(0, idx), rest.slice(idx + 1), show);
    }
  };
