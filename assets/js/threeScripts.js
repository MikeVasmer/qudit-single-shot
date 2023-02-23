     
      var scene = new THREE.Scene();

      var renderer = new THREE.WebGLRenderer({
        antialias: true,
        preserveDrawingBuffer: true
      });
      
      var maxWidth = parseInt(getComputedStyle(document.querySelector('body')).maxWidth,10);
      var maxHeight = parseInt(getComputedStyle(document.querySelector('body')).width,10);

      var width = parseInt(getComputedStyle(document.querySelector('body')).width,10);
      var height = parseInt(getComputedStyle(document.querySelector('body')).width,10);

      width = (width < maxWidth) ? width:maxWidth

      var ratio = 1;

      renderer.setPixelRatio(ratio);
      renderer.setSize(width, height);
      renderer.setClearColor(0xffffff, 1);
      document.body.appendChild(renderer.domElement);


      var options = {
        "aspect_ratio": [1.0, 1.0, 1.0],
        "axes": false,
        "axes_labels": false,
        "decimals": 2,
        "frame": false,
        "projection": "perspective"
      };

      var box = new THREE.Geometry();

      var animate = false; // options.animate;

      var ar = options.aspect_ratio;
      var a = [ar[0], ar[1], ar[2]]; // aspect multipliers
      var autoAspect = 2.5;

      function addLabel(text, x, y, z) {
        var fontsize = 14;

        var canvas = document.createElement('canvas');
        var pixelRatio = Math.round(ratio);
        canvas.width = 128 * pixelRatio;
        canvas.height = 32 * pixelRatio; // powers of two
        canvas.style.width = '128px';
        canvas.style.height = '32px';

        var context = canvas.getContext('2d');
        context.scale(pixelRatio, pixelRatio);
        context.fillStyle = 'black';
        context.font = fontsize + 'px monospace';
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        context.fillText(text, canvas.width / 2 / pixelRatio, canvas.height / 2 / pixelRatio);

        var texture = new THREE.Texture(canvas);
        texture.needsUpdate = true;

        var sprite = new THREE.Sprite(new THREE.SpriteMaterial({
          map: texture
        }));
        sprite.position.set(x, y, z);

        var scale = midToCorner / 2;
        sprite.scale.set(scale, scale * .25); // ratio of canvas width to height

        scene.add(sprite);
      }

      var camera = createCamera();

      function createCamera() {

        var aspect = width / height;

        if (options.projection === 'orthographic') {
          var camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -1000, 1000);
          updateCameraAspect(camera, aspect);
          return camera;
        }

        return new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);

      }

      function updateCameraAspect(camera, aspect,midToCorner) {
        if (camera.isPerspectiveCamera) {
          camera.aspect = aspect;
        } else if (camera.isOrthographicCamera) {
          // Fit the camera frustum to the bounding box's diagonal so that the entire plot fits
          // within at the default zoom level and camera position.
          if (aspect > 1) { // Wide window
            camera.top = midToCorner;
            camera.right = midToCorner * aspect;
          } else { // Tall or square window
            camera.top = midToCorner / aspect;
            camera.right = midToCorner;
          }
          camera.bottom = -camera.top;
          camera.left = -camera.right;
        }

        camera.updateProjectionMatrix();

      }

      function addLine(json) {

        var geometry = new THREE.Geometry();
        for (var i = 0; i < json.points.length; i++) {
          var v = json.points[i];
          geometry.vertices.push(new THREE.Vector3(a[0] * v[0], a[1] * v[1], a[2] * v[2]));
        }

        var transparent = json.opacity < 1 ? true : false;
        var material = new THREE.LineBasicMaterial({
          color: json.color,
          linewidth: json.linewidth,
          transparent: transparent,
          opacity: json.opacity
        });

        var c = new THREE.Vector3();
        geometry.computeBoundingBox();
        geometry.boundingBox.getCenter(c);
        geometry.translate(-c.x, -c.y, -c.z);

        var mesh = new THREE.Line(geometry, material);
        mesh.position.set(c.x, c.y, c.z);
        scene.add(mesh);

      }

      function addSurface(json) {

        var useFaceColors = 'faceColors' in json ? true : false;

        var geometry = new THREE.Geometry();
        for (var i = 0; i < json.vertices.length; i++) {
          var v = json.vertices[i];
          geometry.vertices.push(new THREE.Vector3(a[0] * v.x, a[1] * v.y, a[2] * v.z));
        }
        for (var i = 0; i < json.faces.length; i++) {
          var f = json.faces[i];
          for (var j = 0; j < f.length - 2; j++) {
            var face = new THREE.Face3(f[0], f[j + 1], f[j + 2]);
            if (useFaceColors) face.color.set(json.faceColors[i]);
            geometry.faces.push(face);
          }
        }
        geometry.computeVertexNormals();

        var side = json.singleSide ? THREE.FrontSide : THREE.DoubleSide;
        var transparent = json.opacity < 1 ? true : false;

        var material = new THREE.MeshPhongMaterial({
          side: side,
          color: useFaceColors ? 'white' : json.color,
          vertexColors: useFaceColors ? THREE.FaceColors : THREE.NoColors,
          transparent: transparent,
          opacity: json.opacity,
          shininess: 20,
          flatShading: json.useFlatShading
        });

        var c = new THREE.Vector3();
        geometry.computeBoundingBox();
        geometry.boundingBox.getCenter(c);
        geometry.translate(-c.x, -c.y, -c.z);

        var mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(c.x, c.y, c.z);
        if (transparent && json.renderOrder) mesh.renderOrder = json.renderOrder;
        scene.add(mesh);

        if (json.showMeshGrid) {

          var geometry = new THREE.Geometry();

          for (var i = 0; i < json.faces.length; i++) {
            var f = json.faces[i];
            for (var j = 0; j < f.length; j++) {
              var k = j === f.length - 1 ? 0 : j + 1;
              var v1 = json.vertices[f[j]];
              var v2 = json.vertices[f[k]];
              // vertices in opposite directions on neighboring faces
              var nudge = f[j] < f[k] ? .0005 * zRange : -.0005 * zRange;
              geometry.vertices.push(new THREE.Vector3(a[0] * v1.x, a[1] * v1.y, a[2] * (v1.z + nudge)));
              geometry.vertices.push(new THREE.Vector3(a[0] * v2.x, a[1] * v2.y, a[2] * (v2.z + nudge)));
            }
          }

          var material = new THREE.LineBasicMaterial({
            color: 'black',
            linewidth: 1
          });

          var c = new THREE.Vector3();
          geometry.computeBoundingBox();
          geometry.boundingBox.getCenter(c);
          geometry.translate(-c.x, -c.y, -c.z);

          var mesh = new THREE.LineSegments(geometry, material);
          mesh.position.set(c.x, c.y, c.z);
          scene.add(mesh);

        }

      }

      var scratch = new THREE.Vector3();

      function render() {

        if (animate) requestAnimationFrame(render);
        renderer.render(scene, camera);
        
        // Resize text based on distance from camera.
        // Not neccessary for orthographic due to the nature of the projection (preserves sizes).
        if (!camera.isOrthographicCamera) {
          for (var i = 0; i < scene.children.length; i++) {
            if (scene.children[i].type === 'Sprite') {
              var sprite = scene.children[i];
              var adjust = scratch.addVectors(sprite.position, scene.position)
                .sub(camera.position).length() / 5;
              sprite.scale.set(adjust, .25 * adjust); // ratio of canvas width to height
            }
          }
        }
      }
      
      window.addEventListener('resize', function() {

        var rescale = .95;
        width = (rescale*document.body.clientWidth > maxWidth) ? maxWidth:rescale*document.body.clientWidth;
        height = width;

        renderer.setSize(width, height);
        updateCameraAspect(camera, width/height,midToCorner);
        if (!animate) render();

      });


      // menu functions

      function toggleMenu() {
        var m = document.getElementById('menu-content');
        if (m.style.display === 'block') m.style.display = 'none'
        else m.style.display = 'block';

      }

      function saveAsPNG() {

        var a = document.body.appendChild(document.createElement('a'));
        a.href = renderer.domElement.toDataURL('image/png');
        a.download = 'screenshot';
        a.click();

      }

      function saveAsHTML() {

        toggleMenu(); // otherwise visible in output
        event.stopPropagation();

        var blob = new Blob(['<!DOCTYPE html>\n' + document.documentElement.outerHTML]);
        var a = document.body.appendChild(document.createElement('a'));
        a.href = window.URL.createObjectURL(blob);
        a.download = 'graphic.html';
        a.click();

      }

      function getViewpoint() {

        var info = '<pre>' + JSON.stringify(camera, null, '\t') + '</pre>';
        window.open().document.write(info);

      }