import { useRef, useEffect } from 'react'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

interface SelectedItem {
  id: number;
  name: string;
  room: string;
}

interface ModelProps {
  selectedItem: SelectedItem | null;
}

function Model({ selectedItem }: ModelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const cameraPositionsRef = useRef<any>(null);
  const modelLoadedRef = useRef<boolean>(false);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    initThreeJS();
    loadCameraPositions();
  }, []);

  useEffect(() => {
    if (cameraRef.current && controlsRef.current && cameraPositionsRef.current) {
      setCameraPosition(selectedItem);
    }
  }, [selectedItem]);

  const loadCameraPositions = async () => {
    try {
      const response = await fetch('/camera_positions.json');
      const positions = await response.json();
      cameraPositionsRef.current = positions;
      
      // Set default position after both camera positions are loaded and model is loaded
      trySetDefaultPosition();
    } catch (error) {
      console.error('Failed to load camera positions:', error);
    }
  };

  const trySetDefaultPosition = () => {
    if (cameraRef.current && controlsRef.current && cameraPositionsRef.current && modelLoadedRef.current) {
      setCameraPosition(null);
    }
  };

  const setCameraPosition = (item: SelectedItem | null) => {
    if (!cameraRef.current || !controlsRef.current || !cameraPositionsRef.current) return;

    const camera = cameraRef.current;
    const controls = controlsRef.current;
    const positions = cameraPositionsRef.current;

    let targetPosition;
    
    if (!item) {
      // Return to default position when no item is selected
      targetPosition = positions.default;
    } else {
      // Map item name to camera position key
      let itemKey = item.name.toLowerCase().replace(/\s+/g, '');
      
      // Handle special cases for step mapping
      if (itemKey === 'step') {
        // Use room information to distinguish between step1 and step2
        if (item.room === 'Bathroom') {
          itemKey = 'step1';
        } else if (item.room === 'Kitchen') {
          itemKey = 'step2';
        }
      }
      
      targetPosition = positions[itemKey] || positions.default;
    }

    if (targetPosition) {
      animateCameraToPosition(camera, controls, targetPosition);
    }
  };

  const animateCameraToPosition = (camera: THREE.PerspectiveCamera, controls: OrbitControls, targetPosition: any) => {
    // Cancel any existing animation
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    // Store starting values
    const startPosition = camera.position.clone();
    const startTarget = controls.target.clone();
    const startRotation = camera.rotation.clone();

    // Target values
    const endPosition = new THREE.Vector3(
      targetPosition.position.x,
      targetPosition.position.y,
      targetPosition.position.z
    );
    const endTarget = new THREE.Vector3(
      targetPosition.lookAt.x,
      targetPosition.lookAt.y,
      targetPosition.lookAt.z
    );
    const endRotation = targetPosition.rotation ? new THREE.Euler(
      targetPosition.rotation.x,
      targetPosition.rotation.y,
      targetPosition.rotation.z
    ) : null;

    // Animation parameters
    const duration = 500; // 0.5 seconds
    const startTime = Date.now();

    // Easing function (ease-in-out)
    const easeInOutCubic = (t: number) => {
      return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    };

    // Animation loop
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeInOutCubic(progress);

      // Interpolate position
      camera.position.lerpVectors(startPosition, endPosition, easedProgress);
      
      // Interpolate target
      controls.target.lerpVectors(startTarget, endTarget, easedProgress);

      // Interpolate rotation if specified
      if (endRotation) {
        // Disable controls during rotation animation
        controls.enabled = false;
        
        // Create quaternions for smooth rotation interpolation
        const startQuaternion = new THREE.Quaternion().setFromEuler(startRotation);
        const endQuaternion = new THREE.Quaternion().setFromEuler(endRotation);
        const currentQuaternion = new THREE.Quaternion().slerpQuaternions(startQuaternion, endQuaternion, easedProgress);
        
        // Apply the interpolated rotation
        camera.setRotationFromQuaternion(currentQuaternion);
      } else {
        // Re-enable controls for positions without explicit rotation
        controls.enabled = true;
      }

      // Update controls
      controls.update();

      // Continue animation or finish
      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      } else {
        // Animation complete
        animationRef.current = null;
        
        // Final cleanup - re-enable controls if they were disabled
        if (endRotation) {
          // For positions with rotation, keep controls disabled initially
          setTimeout(() => {
            if (controlsRef.current) {
              controlsRef.current.enabled = true;
            }
          }, 200);
        }
      }
    };

    // Start the animation
    animate();
  };

  const initThreeJS = () => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    
    // Store camera reference
    cameraRef.current = camera;
    
    renderer.setSize(canvas.clientWidth, canvas.clientHeight);
    renderer.setClearColor(0xf0f0f0);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.5;
    
    // Improved lighting setup for house visualization
    // Balanced ambient light for overall illumination
    const ambientLight = new THREE.AmbientLight(0x404040, 1.8);
    scene.add(ambientLight);
    
    // Main directional light (sun-like) - balanced intensity
    const directionalLight = new THREE.DirectionalLight(0xffffff, 2.0);
    directionalLight.position.set(10, 15, 10);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    directionalLight.shadow.camera.near = 0.5;
    directionalLight.shadow.camera.far = 100;
    directionalLight.shadow.camera.left = -20;
    directionalLight.shadow.camera.right = 20;
    directionalLight.shadow.camera.top = 20;
    directionalLight.shadow.camera.bottom = -20;
    scene.add(directionalLight);
    
    // Secondary fill light from opposite side - balanced intensity
    const fillLight = new THREE.DirectionalLight(0xffffff, 1.2);
    fillLight.position.set(-10, 10, -5);
    scene.add(fillLight);
    
    // Hemisphere light for natural sky/ground lighting - balanced intensity
    const hemisphereLight = new THREE.HemisphereLight(0x87ceeb, 0x8b7355, 0.8);
    scene.add(hemisphereLight);
    
    // Point light for interior illumination - balanced intensity
    const pointLight = new THREE.PointLight(0xffffff, 1.5, 50);
    pointLight.position.set(0, 8, 0);
    scene.add(pointLight);
    
    // Additional point lights for better coverage - reduced intensity
    const pointLight2 = new THREE.PointLight(0xffffff, 1.0, 40);
    pointLight2.position.set(10, 5, 10);
    scene.add(pointLight2);
    
    const pointLight3 = new THREE.PointLight(0xffffff, 1.0, 40);
    pointLight3.position.set(-10, 5, -10);
    scene.add(pointLight3);
    
    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    
    // Store controls reference
    controlsRef.current = controls;
    
    camera.position.set(5, 5, 5);
    camera.lookAt(0, 0, 0);
    
    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Load GLB file
    loadGLB(scene);
  };

  const loadGLB = (scene: THREE.Scene) => {
    const loader = new GLTFLoader();

    loader.load('/models/jason_house_censored.glb', (gltf) => {
      console.log('GLB loaded successfully!');
      
      // Add new model
      const model = gltf.scene;
      
      // Ensure materials receive lighting properly
      model.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          child.castShadow = true;
          child.receiveShadow = true;
          
          // Ensure material is properly lit
          if (child.material) {
            if (Array.isArray(child.material)) {
              child.material.forEach(mat => {
                if (mat instanceof THREE.MeshStandardMaterial || mat instanceof THREE.MeshPhysicalMaterial) {
                  mat.needsUpdate = true;
                }
              });
            } else if (child.material instanceof THREE.MeshStandardMaterial || child.material instanceof THREE.MeshPhysicalMaterial) {
              child.material.needsUpdate = true;
            }
          }
        }
      });
      
      scene.add(model);
      
      // Get model size
      const box = new THREE.Box3().setFromObject(model);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      
      console.log('GLB model size:', {
        width: size.x,
        height: size.y,
        depth: size.z,
        maxDimension: Math.max(size.x, size.y, size.z)
      });
      console.log('GLB model center:', center);
      
      // Center the model
      model.position.sub(center);
      
      // Mark model as loaded and try to set default camera position
      modelLoadedRef.current = true;
      trySetDefaultPosition();
      
      // Load and display bounding box annotations with the same centering offset
      loadBoundingBoxes(scene, center);
    }, (progress) => {
      console.log('Loading progress:', progress);
    }, (error) => {
      console.error('Error loading GLB:', error);
    });
  };

  const loadBoundingBoxes = (scene: THREE.Scene, modelCenter: THREE.Vector3) => {
    fetch('/jason_house_2d_floor_clusters.json')
      .then(response => response.json())
      .then(data => {
        console.log('Loaded annotations:', data);
        
        data.annotations.forEach((annotation: any) => {
          const minBound = new THREE.Vector3(...annotation.min_bound);
          const maxBound = new THREE.Vector3(...annotation.max_bound);
          
          // Create bounding box
          const size = new THREE.Vector3().subVectors(maxBound, minBound);
          const center = new THREE.Vector3().addVectors(minBound, maxBound).multiplyScalar(0.5);
          
          // Apply the same centering transformation as the model
          center.sub(modelCenter);
          
          // Different colors for different annotation types
          let color = 0xff0000; // Default red
          if (annotation.annotation_type === 'plane') {
            color = 0x00ff00; // Green for planes
          } else if (annotation.annotation_type === 'cluster') {
            color = 0x0000ff; // Blue for clusters
          }
          
          // Create wireframe box
          const boxGeometry = new THREE.BoxGeometry(size.x, size.y, size.z);
          const edges = new THREE.EdgesGeometry(boxGeometry);
          const lineMaterial = new THREE.LineBasicMaterial({ 
            color: color,
            linewidth: 2,
            transparent: true,
            opacity: 0.8
          });
          const wireframe = new THREE.LineSegments(edges, lineMaterial);
          wireframe.position.copy(center);
          wireframe.name = `bbox_${annotation.label}`;
          
          scene.add(wireframe);
          
          console.log(`Added ${annotation.annotation_type} bbox: ${annotation.label} at position:`, center);
        });
      })
      .catch(error => {
        console.error('Error loading annotations:', error);
      });
  };

  return (
    // responsive container for canvas
    <div style={{ width: '100%', height: '100%', position: 'relative' }} >
      <canvas
        ref={canvasRef}
        style={{
          width: '100%', height: '100%',
          margin: '0 auto',
          display: 'block',
          border: '1px solid #ccc',
          borderRadius: '4px'
        }}
      />
    </div>

    // <div style={{ width: '100%', padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      
    //   <canvas 
    //     ref={canvasRef}
    //     width='100%'
    //     height={500}
    //     style={{ 
    //       border: '1px solid #ccc',
    //       borderRadius: '4px',
    //       display: 'block'
    //     }}
    //   />
      
    //   <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
    //     Controls: Left click + drag to rotate, Right click + drag to pan, Scroll to zoom
    //   </div>
    // </div>
  )
}

export default Model