/**
 * Three.js 3D Data Constellation Animation for Hero Header
 * Renders an interactive 3D network of connecting data nodes representing Fabric Lakehouse pipelines.
 */
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("hero-3d-container");
  if (!container || typeof THREE === "undefined") {
    console.log("Three.js or container not ready.");
    return;
  }

  // 1. Scene, Camera, Renderer Setup
  const scene = new THREE.Scene();
  const width = container.clientWidth;
  const height = container.clientHeight || 280;

  const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
  camera.position.z = 180;

  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  // 2. Create 3D Data Particles & Connections
  const particleCount = 45;
  const particlesGroup = new THREE.Group();
  scene.add(particlesGroup);

  const particles = [];
  const particleGeo = new THREE.SphereGeometry(1.6, 12, 12);
  
  const colors = [0x6366F1, 0x38BDF8, 0xA855F7, 0xEC4899];

  for (let i = 0; i < particleCount; i++) {
    const color = colors[Math.floor(Math.random() * colors.length)];
    const mat = new THREE.MeshBasicMaterial({ color: color });
    const mesh = new THREE.Mesh(particleGeo, mat);

    mesh.position.x = (Math.random() - 0.5) * 260;
    mesh.position.y = (Math.random() - 0.5) * 160;
    mesh.position.z = (Math.random() - 0.5) * 160;

    mesh.userData = {
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      vz: (Math.random() - 0.5) * 0.25
    };

    particlesGroup.add(mesh);
    particles.push(mesh);
  }

  // Line Mesh for 3D Node Connections
  const lineMat = new THREE.LineBasicMaterial({
    color: 0x6366F1,
    transparent: true,
    opacity: 0.25
  });

  const lineGeo = new THREE.BufferGeometry();
  const lineMesh = new THREE.LineSegments(lineGeo, lineMat);
  particlesGroup.add(lineMesh);

  // Mouse Interactivity
  let targetRotationX = 0;
  let targetRotationY = 0;
  let mouseX = 0;
  let mouseY = 0;

  window.addEventListener("mousemove", (e) => {
    const rect = container.getBoundingClientRect();
    if (e.clientY >= rect.top && e.clientY <= rect.bottom) {
      mouseX = (e.clientX - rect.left - width / 2) * 0.0005;
      mouseY = (e.clientY - rect.top - height / 2) * 0.0005;
    }
  });

  // 3. Animation Loop
  function animate() {
    requestAnimationFrame(animate);

    // Rotate particle group
    particlesGroup.rotation.y += 0.002;
    particlesGroup.rotation.x += 0.001;

    // Smooth mouse tilt
    targetRotationX += (mouseY - targetRotationX) * 0.05;
    targetRotationY += (mouseX - targetRotationY) * 0.05;
    particlesGroup.rotation.x += targetRotationX;
    particlesGroup.rotation.y += targetRotationY;

    // Update particle positions & lines
    const linePositions = [];
    const maxDist = 55;

    for (let i = 0; i < particleCount; i++) {
      const p = particles[i];
      p.position.x += p.userData.vx;
      p.position.y += p.userData.vy;
      p.position.z += p.userData.vz;

      // Bounce off boundary
      if (Math.abs(p.position.x) > 130) p.userData.vx *= -1;
      if (Math.abs(p.position.y) > 80) p.userData.vy *= -1;
      if (Math.abs(p.position.z) > 80) p.userData.vz *= -1;

      // Connect close nodes
      for (let j = i + 1; j < particleCount; j++) {
        const p2 = particles[j];
        const dist = p.position.distanceTo(p2.position);

        if (dist < maxDist) {
          linePositions.push(p.position.x, p.position.y, p.position.z);
          linePositions.push(p2.position.x, p2.position.y, p2.position.z);
        }
      }
    }

    lineGeo.setAttribute("position", new THREE.Float32BufferAttribute(linePositions, 3));
    lineGeo.computeBoundingSphere();

    renderer.render(scene, camera);
  }

  animate();

  // Handle Window Resize
  window.addEventListener("resize", () => {
    const newW = container.clientWidth;
    const newH = container.clientHeight || 280;
    camera.aspect = newW / newH;
    camera.updateProjectionMatrix();
    renderer.setSize(newW, newH);
  });
});
