      const camera = new THREE.PerspectiveCamera(50, 1, 0.01, 20);
      camera.position.set(1.2, 0.9, 1.2);
      renderer = new THREE.WebGLRenderer({ antialias: true });
      host.innerHTML = "";
      host.appendChild(renderer.domElement);
      const controls = new OrbitControls(camera, renderer.domElement);
      controls.target.set(0.3, 0.3, 0);
      controls.enableZoom = true;
      controls.zoomToCursor = true; // wheel + our Ctrl+↑↓ use cursor as zoom center
      controls.minDistance = 0.05;
      controls.maxDistance = 40;
      scene.add(new THREE.HemisphereLight(0xffffff, 0x223344, 0.85));
      const dir = new THREE.DirectionalLight(0xffffff, 0.7);
      dir.position.set(2, 3, 1);
      scene.add(dir);
      scene.add(new THREE.GridHelper(2, 20, 0x3dd6c6, 0x1a2738));
      const tcpMarker = new THREE.Mesh(
        new THREE.SphereGeometry(0.018, 24, 16),
        new THREE.MeshStandardMaterial({ color: 0xf0b429, emissive: 0x553300 })
      );
      scene.add(tcpMarker);
      const markersGroup = new THREE.Group();
      markersGroup.name = "m2_waypoints";
      markersGroup.visible = !!markersVisibleRef.current;
      tcpMarker.visible = !!tcpVisibleRef.current;
      scene.add(markersGroup);
      threeRef.current = {
        scene, camera, renderer, controls, tcpMarker, markersGroup,
        robot: null, ghost: null, sceneOverlay: null, cameraOverlays: null,
        drawShapes: null, loadToken: 0, raf: 0,
      };
      syncSceneMarkers(armSceneMarkers.items);

      // Ctrl+↑/↓ → synthesize wheel at pointer (uses OrbitControls zoomToCursor; avoids freeze)
      const pointer = { x: 0, y: 0, inside: false };
      let zoomRaf = 0;
      let zoomDeltaY = 0;
      const onPointerMove = (e) => {
        pointer.x = e.clientX;
        pointer.y = e.clientY;
        pointer.inside = true;
      };
      const onPointerLeave = () => {
        pointer.inside = false;
      };
      const flushKeyZoom = () => {
        zoomRaf = 0;
        if (!alive || !zoomDeltaY) return;
        const el = renderer.domElement;
        if (!el) return;
        const rect = el.getBoundingClientRect();
        if (rect.width < 1 || rect.height < 1) {
          zoomDeltaY = 0;
          return;
        }
        let cx = pointer.inside ? pointer.x : rect.left + rect.width * 0.5;
        let cy = pointer.inside ? pointer.y : rect.top + rect.height * 0.5;
        cx = Math.min(rect.right, Math.max(rect.left, cx));
        cy = Math.min(rect.bottom, Math.max(rect.top, cy));
        const dy = zoomDeltaY;
        zoomDeltaY = 0;
        el.dispatchEvent(new WheelEvent("wheel", {
          bubbles: true,
          cancelable: true,
          clientX: cx,
          clientY: cy,
          deltaY: dy,
          deltaMode: 0,
        }));
      };
      const onKeyDownZoom = (e) => {
        if (!(e.ctrlKey || e.metaKey)) return;
        if (e.code !== "ArrowUp" && e.code !== "ArrowDown") return;
        const tag = (e.target && e.target.tagName) || "";
        if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
        if (e.target && e.target.isContentEditable) return;
        e.preventDefault();
        // ArrowUp → negative deltaY → zoom in (same as wheel)
        zoomDeltaY += e.code === "ArrowUp" ? -80 : 80;
        // coalesce key-repeat to one wheel event per frame
        if (!zoomRaf) zoomRaf = requestAnimationFrame(flushKeyZoom);
      };
      renderer.domElement.addEventListener("pointermove", onPointerMove);
      renderer.domElement.addEventListener("pointerleave", onPointerLeave);
      window.addEventListener("keydown", onKeyDownZoom);
      threeRef.current._zoomCleanup = () => {
        if (zoomRaf) cancelAnimationFrame(zoomRaf);
        zoomRaf = 0;
        renderer.domElement.removeEventListener("pointermove", onPointerMove);
        renderer.domElement.removeEventListener("pointerleave", onPointerLeave);
        window.removeEventListener("keydown", onKeyDownZoom);
      };
