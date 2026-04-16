/* ----------------------------
   🌟 FEATURE LOADING SECTION
   ---------------------------- */

// 🔹 Fetch and populate all materials in dropdown
async function fetchAndPopulateMaterials() {
  console.log("🔄 Fetching materials from /api/materials...");
  try {
    const response = await fetch("/api/materials");
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const materials = await response.json();

    const materialSelect = document.getElementById("materialSelect");
    if (!materialSelect) return console.warn("⚠️ Material select element not found");

    // Clear and re-populate
    materialSelect.innerHTML = '<option value="">Select Material</option>';
    materials.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m.material_id;
      opt.textContent = `${m.material_name}`;
      materialSelect.appendChild(opt);
    });

    console.log(`✅ Loaded ${materials.length} materials`);
  } catch (err) {
    console.error("❌ Error loading materials:", err);
  }
}

// 🔹 Fetch and populate all features
async function fetchAndPopulateFeatures() {
  console.log("🔄 Fetching features from /api/features...");
  try {
    const response = await fetch("/api/features");
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const features = await response.json();

    const featureSelect = document.getElementById("featureSelect");
    if (!featureSelect) return console.warn("⚠️ Feature select element not found");

    featureSelect.innerHTML = '<option value="">Select a feature</option>';

    if (features.length === 0) {
      const opt = document.createElement("option");
      opt.textContent = "No features available";
      featureSelect.appendChild(opt);
      console.warn("⚠️ No features found for material:", materialId);
      return;
    }

    features.forEach((f) => {
      const opt = document.createElement("option");
      opt.value = f.feature_id;
      opt.textContent = f.feature_name;
      featureSelect.appendChild(opt);
    });

    console.log(`✅ Loaded ${features.length} features`);
  } catch (err) {
    console.error("❌ Error loading features:", err);
  }
}

// 🔹 Fetch and populate operations
async function fetchAndPopulateOperations() {
  console.log("🔄 Fetching operations from /api/operations...");
  try {
    const response = await fetch("/api/operations");
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const operations = await response.json();

    const operationSelect = document.getElementById("operationSelect");
    if (!operationSelect) return console.warn("⚠️ Operation select element not found");

    operationSelect.innerHTML = '<option value="">Select Operation</option>';
    operations.forEach((op) => {
      const opt = document.createElement("option");
      opt.value = op.operation_id || op.id; // Handle both response formats
      opt.textContent = `${op.operation_name || op.name} (${op.description || ''})`;
      // Store the operation type in a data attribute (using only the first word)
      opt.dataset.type = (op.operation_name || op.name).split(' ')[0].toLowerCase();
      operationSelect.appendChild(opt);
    });

    console.log(`✅ Loaded ${operations.length} operations`);
  } catch (err) {
    console.error("❌ Error loading operations:", err);
  }
}

// Setup event listeners when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  // Material selection handler
  const materialSelect = document.getElementById("materialSelect");
  if (materialSelect) {
    materialSelect.addEventListener("change", (e) => {
      const materialId = e.target.value;
      console.log(`📦 Material selected: ${materialId}`);
      // Features are no longer filtered by material
    });
  }

  // Feature selection handler - Load operations for selected feature
  const featureSelect = document.getElementById("featureSelect");
  if (featureSelect) {
    featureSelect.addEventListener("change", async (e) => {
      const featureId = e.target.value;
      const operationSelect = document.getElementById("operationSelect");
      
      if (!featureId) {
        operationSelect.innerHTML = '<option value="">Select an operation</option>';
        return;
      }

      console.log(`🎛 Feature selected: ${featureId}`);
      
      try {
        console.log(`🔄 Fetching operations for feature ${featureId}...`);
        const response = await fetch(`/api/feature_operations/${featureId}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const operations = await response.json();

        operationSelect.innerHTML = '<option value="">Select an operation</option>';
        
        operations.forEach((op) => {
          const opt = document.createElement("option");
          opt.value = op.operation_id;
          opt.textContent = `${op.operation_name}${op.description ? ` (${op.description})` : ''}`;
          // Store the operation type in a data attribute (using only the first word)
          opt.dataset.type = op.operation_name.split(' ')[0].toLowerCase();
          operationSelect.appendChild(opt);
        });

        console.log(`✅ Loaded ${operations.length} operations for feature ${featureId}`);
      } catch (err) {
        console.error("❌ Error loading operations for feature:", err);
        operationSelect.innerHTML = '<option value="">Error loading operations</option>';
      }
    });
  }

  // Initialize all dropdowns on page load
  (async () => {
    try {
      await Promise.all([
        fetchAndPopulateMaterials(),
        fetchAndPopulateOperations(),
        fetchAndPopulateFeatures(),
      ]);
      console.log("✅ All dropdowns initialized");
    } catch (error) {
      console.error("❌ Error initializing dropdowns:", error);
    }
  })();

});
