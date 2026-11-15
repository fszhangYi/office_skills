  const layerRows = (() => {
    const urdfPath = String(model?.urdf || status?.model?.urdf || "cs66_cell_c.urdf").split("?")[0];
    const urdfName = urdfPath.split("/").pop() || urdfPath;
    const sceneUrl = overlayCfg?.url || "/assets/scene/g26562-01-00_asm.stl";
    const sceneName = sceneUrl.split("/").pop() || sceneUrl;
    const rows = [
      {
        id: "robot",
        label: "机械臂 URDF",
        file: urdfName,
        color: "#b0b8c4",
        visible: robotVisible,
        loaded: !!threeRef.current?.robot || !!model,
      },
      {
        id: "ghost",
        label: "幽灵预览",
        file: urdfName,
        color: "#ff8a8a",
        visible: ghostVisible,
        loaded: true,
      },
      {
        id: "scene",
        label: overlayCfg?.name || "场景 CAD",
        file: sceneName,
        color: overlayCfg?.color || "#7a93ad",
        visible: !!overlayCfg?.enabled && overlayVisible,
        loaded: !!overlayCfg,
      },
      {
        id: "cam_group",
        label: "相机组",
        file: "realsense/*.stl",
        color: "#e8e8e8",
        visible: !!camOverlayCfg?.enabled && camOverlayVisible,
        loaded: !!camOverlayCfg,
      },
    ];
    (camOverlayCfg?.cameras || []).forEach((c) => {
      const file = String(c.url || "").split("/").pop() || c.model || "mesh";
      rows.push({
        id: `cam:${c.id}`,
        label: c.label || c.id,
        file,
        color: c.color || "#e85d4c",
        visible: !!c.enabled && !!camOverlayCfg?.enabled && camOverlayVisible,
        loaded: true,
        indent: true,
      });
    });
    rows.push({
      id: "draw_group",
      label: "绘制组",
      file: "cuboid/sphere/cylinder",
      color: "#5b8ff9",
      visible: !!drawCfg?.enabled && drawVisible,
      loaded: !!drawCfg,
    });
    (drawCfg?.layers || []).forEach((L) => {
      rows.push({
        id: `draw_layer:${L.id}`,
        label: L.label || L.id,
        file: `${(L.shapes || []).length} 个图元`,
        color: "#9ec5ff",
        visible: !!L.enabled && !!drawCfg?.enabled && drawVisible,
        loaded: true,
        indent: true,
      });
      (L.shapes || []).forEach((s) => {
        rows.push({
          id: `draw_shape:${L.id}:${s.id}`,
          label: s.label || s.id,
          file: s.type || "shape",
          color: s.color || "#5b8ff9",
          visible: !!s.enabled && !!L.enabled && !!drawCfg?.enabled && drawVisible,
          loaded: true,
          indent: true,
        });
      });
    });
    rows.push(
      {
        id: "tcp",
        label: "TCP 标记",
        file: "—",
        color: "#f0b429",
        visible: tcpVisible,
        loaded: true,
      },
      {
        id: "markers",
        label: "M2 点位",
        file: "—",
        color: "#3dd6c6",
        visible: markersVisible,
        loaded: true,
      },
    );
    return rows;
  })();
