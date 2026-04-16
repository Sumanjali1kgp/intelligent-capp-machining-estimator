// jobs.js - Handles job and part management for the lathe operations page
console.log("🧱 jobs.js loaded");

// Global state storage per job
const jobDataStore = {};

// Export required functions to global scope
window.initializeLatheCalculator = initializeLatheCalculator;
window.calculateAndDisplayTimes = calculateAndDisplayTimes;
window.calculateAndDisplayCosts = calculateAndDisplayCosts;
window.showNewJobModal = showNewJobModal;
window.closeNewJobModal = closeNewJobModal;
window.createNewJob = createNewJob;
window.deleteJob = deleteJob;


// Update or create job data in the store
function updateJobData(jobId, updates) {
  if (!jobDataStore[jobId]) jobDataStore[jobId] = {};
  jobDataStore[jobId] = { ...jobDataStore[jobId], ...updates };
  console.log(`📦 Updated jobDataStore[${jobId}]:`, jobDataStore[jobId]);
  return jobDataStore[jobId];
}

// Format a date string to a readable format
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

// Format currency
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '₹0.00';
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

// Show a success message
function showSuccessMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded shadow-lg flex items-center';
    messageDiv.innerHTML = `
        <i class="fas fa-check-circle mr-2"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(messageDiv);
    
    // Remove the message after 3 seconds
    setTimeout(() => {
        messageDiv.classList.add('opacity-0', 'transition-opacity', 'duration-300');
        setTimeout(() => messageDiv.remove(), 300);
    }, 3000);
}

// Show an error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded shadow-lg flex items-center';
    errorDiv.innerHTML = `
        <i class="fas fa-exclamation-circle mr-2"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(errorDiv);
    
    // Remove the message after 5 seconds
    setTimeout(() => {
        errorDiv.classList.add('opacity-0', 'transition-opacity', 'duration-300');
        setTimeout(() => errorDiv.remove(), 300);
    }, 5000);
}

// Delete a job
async function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/jobs/${jobId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Show success message and reload jobs
        showSuccessMessage('Job deleted successfully');
        loadJobs();
    } catch (error) {
        console.error('Error deleting job:', error);
        showError('Failed to delete job. Please try again.');
    }
}

// Get CSRF token from cookies
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

// Show add part form
function showAddPartForm(jobId) {
    // You can implement a modal or redirect to a new page for adding a part
    window.location.href = `/jobs/${jobId}/parts/new`;
}

// Show operation form
function showOperationForm(partId) {
    // You can implement a modal or redirect to a new page for adding an operation
    window.location.href = `/parts/${partId}/operations/new`;
}

// Load and display jobs
async function loadJobs() {
    const jobsList = document.getElementById('jobsList');
    if (!jobsList) return;

    try {
        // Show loading state
        jobsList.innerHTML = `
            <div class="text-center text-gray-500 py-4">
                <i class="fas fa-spinner fa-spin mr-2"></i> Loading jobs...
            </div>
        `;

        // Fetch jobs from the API
        const response = await fetch('/api/jobs');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const jobs = await response.json();
        
        if (jobs.length === 0) {
            jobsList.innerHTML = `
                <div class="text-center text-gray-500 py-4">
                    <p>No jobs found. Create a new job to get started.</p>
                    <button onclick="showNewJobModal()" 
                            class="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                        <i class="fas fa-plus mr-1"></i> Create New Job
                    </button>
                </div>
            `;
            return;
        }

        // Generate HTML for each job
        jobsList.innerHTML = jobs.map(job => `
            <div class="job-card bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow duration-200" 
                 data-job-id="${job.id}" 
                 style="cursor: pointer;"
                 onclick="selectJob(${job.id}); return false;">
                <div class="job-header bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
                    <div>
                        <h4 class="font-semibold text-gray-800">${job.name}</h4>
                        <p class="text-xs text-gray-500">Created: ${formatDate(job.created_at)}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button class="toggle-parts-btn text-blue-600 hover:text-blue-800 text-sm" 
                                data-job-id="${job.id}" title="Toggle parts">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                        <button onclick="event.stopPropagation(); deleteJob(${job.id})" 
                                class="text-red-500 hover:text-red-700 text-sm" 
                                title="Delete job">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="job-parts hidden px-4 py-3" id="job-${job.id}-parts">
                    ${job.parts && job.parts.length > 0 ? 
                        job.parts.map(part => `
                            <div class="part-item bg-gray-50 rounded p-3 mb-2 border border-gray-100">
                                <div class="flex justify-between items-center">
                                    <div>
                                        <h5 class="font-medium text-gray-800">${part.name}</h5>
                                        <p class="text-sm text-gray-600">Material Cost: ${formatCurrency(part.material_cost)}</p>
                                    </div>
                                    <div class="flex space-x-2">
                                        <button class="add-operation-btn text-blue-600 hover:text-blue-800 text-sm" 
                                                data-part-id="${part.id}">
                                            <i class="fas fa-plus-circle mr-1"></i> Add Operation
                                        </button>
                                        <button class="view-part-btn text-blue-600 hover:text-blue-800 text-sm" 
                                                data-job-id="${job.id}" 
                                                data-part-id="${part.id}">
                                            <i class="fas fa-arrow-right"></i> View
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `).join('') : 
                        '<p class="text-sm text-gray-500">No parts found for this job.</p>'
                    }
                    <button onclick="event.stopPropagation(); showAddPartForm(${job.id})" 
                            class="mt-2 text-sm text-blue-600 hover:text-blue-800">
                        <i class="fas fa-plus mr-1"></i> Add Part
                    </button>
                </div>
            </div>
        `).join('');

        // Handle job card clicks to load job details
        document.addEventListener('click', (e) => {
            const jobCard = e.target.closest('.job-card');
            if (jobCard) {
                e.preventDefault();
                e.stopPropagation();
                
                // Remove active class from all job cards
                document.querySelectorAll('.job-card').forEach(card => {
                    card.classList.remove('active', 'border-blue-500');
                });
                
                // Add active class to clicked job card
                jobCard.classList.add('active', 'border-blue-500');
                
                // Show the calculator section
                const calc = document.getElementById('jobCalcTemplate');
                if (calc) {
                    calc.classList.remove('hidden');
                    
                    // Load job details
                    const jobId = jobCard.getAttribute('data-job-id');
                    if (jobId) {
                        loadJobDetails(jobId);
                    }
                }
                
                return;
            }
            
            // Handle parts toggles
            const btn = e.target.closest('.toggle-parts-btn');
            if (!btn) return;
            
            e.preventDefault();
            e.stopPropagation();
            const jobId = btn.getAttribute('data-job-id');
            const partsContainer = document.getElementById(`job-${jobId}-parts`);
            const icon = btn.querySelector('i');
            
            if (partsContainer && icon) {
                // Toggle the visibility of the parts container
                partsContainer.classList.toggle('hidden');
                
                // Toggle the chevron icon
                if (partsContainer.classList.contains('hidden')) {
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                } else {
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                    
                    // Load parts if not already loaded
                    if (!partsContainer.hasAttribute('data-loaded')) {
                        loadJobParts(jobId, partsContainer);
                    }
                }
            }
        });

        // Add event listeners for view part buttons
        document.querySelectorAll('.view-part-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const jobId = btn.getAttribute('data-job-id');
                const partId = btn.getAttribute('data-part-id');
                if (jobId && partId) {
                    window.location.href = `/jobs/${jobId}/parts/${partId}`;
                }
            });
        });

        // Add event listeners for add operation buttons
        document.querySelectorAll('.add-operation-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const partId = btn.getAttribute('data-part-id');
                if (partId) {
                    showOperationForm(partId);
                }
            });
        });

    } catch (error) {
        console.error('Error loading jobs:', error);
        jobsList.innerHTML = `
            <div class="text-center text-red-500 py-4">
                <i class="fas fa-exclamation-circle mr-2"></i>
                Failed to load jobs. Please try again later.
            </div>
        `;
    }
}

// Load parts for a specific job
async function loadJobParts(jobId, container) {
    if (!jobId || !container) return;
    
    try {
        const response = await fetch(`/api/jobs/${jobId}/parts`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const parts = await response.json();
        
        // Mark as loaded
        container.setAttribute('data-loaded', 'true');
        
    } catch (error) {
        console.error(`Error loading parts for job ${jobId}:`, error);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-red-500 text-sm mt-2';
        errorDiv.innerHTML = 'Failed to load parts. Please try again.';
        container.appendChild(errorDiv);
    }
}

// Show the new job modal
function showNewJobModal() {
    const modal = document.getElementById('newJobModal');
    if (modal) {
        modal.classList.remove('hidden');
        document.getElementById('jobName').focus();
    }
}

// Close the new job modal
function closeNewJobModal() {
    const modal = document.getElementById('newJobModal');
    if (modal) {
        modal.classList.add('hidden');
        // Clear the input
        document.getElementById('jobName').value = '';
    }
}

// Create a new job
async function createNewJob() {
    const jobName = document.getElementById('jobName').value.trim();
    if (!jobName) {
        showError('Please enter a job name');
        return;
    }

    try {
        const response = await fetch('/api/jobs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: jobName })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || 'Failed to create job');
        }

        const job = await response.json();
        
        // Close the modal and refresh the jobs list
        closeNewJobModal();
        await loadJobs();
        
        // Show success message
        showSuccessMessage(`Job "${job.name}" created successfully!`);
        
    } catch (error) {
        console.error('Error creating job:', error);
        showError(error.message || 'Failed to create job. Please try again.');
    }
}

// Show the add part form (implementation at the top of the file)

// Initialize the lathe calculator
function initializeLatheCalculator() {
    console.log("🔧 Initializing lathe calculator...");
    // Add any initialization code needed for the calculator
}

// Calculate and display times (dummy implementation)
function calculateAndDisplayTimes() {
    if (!selectedJobId) {
        console.log("ℹ️ No job selected for time calculation");
        return;
    }
    
    console.log("⏱️ Calculating times for job:", selectedJobId);
    // This will be overridden by time.js
    // After calculation, update the job data:
    // updateJobData(selectedJobId, { total_time: calculatedTime });
}

// Calculate and display costs (dummy implementation)
function calculateAndDisplayCosts() {
    if (!selectedJobId) {
        console.log("ℹ️ No job selected for cost calculation");
        return;
    }
    
    console.log("💰 Calculating costs for job:", selectedJobId);
    // This will be overridden by cost.js
    // After calculation, update the job data:
    // updateJobData(selectedJobId, { total_cost: calculatedCost });
}

// Save the current job (with time, cost, etc.)
async function saveCurrentJob() {
    if (!selectedJobId) {
        console.error("❌ No job selected to save!");
        showError("Please select a job before saving.");
        return;
    }

    try {
        // Get form inputs with safe fallbacks
        const nameInput = document.getElementById('jobName');
        const clientInput = document.getElementById('clientName');
        const descInput = document.getElementById('jobDescription');
        const materialSelect = document.getElementById('materialSelect');
        const featureSelect = document.getElementById('featureSelect');
        const operationSelect = document.getElementById('operationSelect');
        
        // Collect all dimension inputs
        const dimensions = {};
        document.querySelectorAll('input[type="number"]').forEach(input => {
            if (input.name && input.name !== 'quantity') { // Skip quantity if it's not a dimension
                dimensions[input.name] = parseFloat(input.value) || 0;
            }
        });
        
        // Get the current time and cost values using the correct element IDs
        const totalTimeEl = document.getElementById('totalTimeDisplay');
        const totalCostEl = document.getElementById('totalCostDisplay');
        
        // Get values with proper fallbacks
        const jobData = {
            name: (nameInput?.value || '').trim() || `Job_${selectedJobId}`,
            client_name: (clientInput?.value || '').trim() || 'N/A',
            description: (descInput?.value || '').trim() || 'No description provided',
            material_id: materialSelect?.value || null,
            feature_id: featureSelect?.value || null,
            operation_id: operationSelect?.value || null,
            operation_name: operationSelect?.options[operationSelect?.selectedIndex]?.text || '',
            dimensions: dimensions,
            total_time: totalTimeEl ? parseFloat(totalTimeEl.textContent) || 0 : 0,
            total_cost: totalCostEl ? parseFloat(totalCostEl.textContent.replace(/[^\d.-]+/g, '')) || 0 : 0
        };
        
        console.log('💾 Saving job data:', jobData);
        
        // Prepare payload for backend
        const payload = {
            name: jobData.name,
            client_name: jobData.client_name,
            description: jobData.description,
            material_id: jobData.material_id,
            feature_id: jobData.feature_id,
            operation_id: jobData.operation_id,
            operation_name: jobData.operation_name,
            dimensions: jobData.dimensions,
            total_time: jobData.total_time,
            total_cost: jobData.total_cost
        };
        
        // Update the local store with current form data
        updateJobData(selectedJobId, payload);
        
        console.log("💾 Saving job data:", { jobId: selectedJobId, ...payload });

        const response = await fetch(`/api/jobs/${selectedJobId}`, {
            method: 'PUT',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || 'Failed to save job');
        }
        
        console.log("✅ Job saved successfully!");
        showSuccessMessage('Job saved successfully!');
        
        // Refresh the job list to show updated data
        loadJobs();
    } catch (error) {
        console.error('Error saving job:', error);
        showError(`Failed to save job: ${error.message}`);
    }
}

// Load existing data when job is opened
async function loadJobDetails(jobId) {
    try {
        console.log(`🔄 Loading details for job ${jobId}...`);
        const response = await fetch(`/api/jobs/${jobId}`);
        if (!response.ok) throw new Error('Failed to load job data');

        const job = await response.json();
        console.log("📦 Loaded job from server:", job);

        // Store the loaded data in our state store
        const jobData = {
            name: job.name || `Job_${jobId}`,
            client_name: job.client_name || '',
            description: job.description || '',
            material_id: job.material_id || null,
            feature_id: job.feature_id || null,
            operation_id: job.operation_id || null,
            operation_name: job.operation_name || '',
            total_time: parseFloat(job.total_time) || 0,
            total_cost: parseFloat(job.total_cost) || 0,
            dimensions: job.dimensions || {},
            status: job.status || 'draft',
            created_at: job.created_at,
            updated_at: job.updated_at
        };
        
        // Update the local state
        updateJobData(jobId, jobData);

        // Restore UI values
        const nameInput = document.getElementById("jobName");
        const clientInput = document.getElementById("clientName");
        const descInput = document.getElementById("jobDescription");
        const materialSelect = document.getElementById("materialSelect");

        if (nameInput) nameInput.value = jobData.name;
        if (clientInput) clientInput.value = jobData.client_name;
        if (descInput) descInput.value = jobData.description;
        
        // Set material and trigger change event
        if (materialSelect && jobData.material_id) {
            materialSelect.value = jobData.material_id;
            materialSelect.dispatchEvent(new Event("change"));
        }

        // Restore feature after a short delay to allow material to load
        setTimeout(() => {
            const featureSelect = document.getElementById("featureSelect");
            if (featureSelect && jobData.feature_id) {
                featureSelect.value = jobData.feature_id;
                featureSelect.dispatchEvent(new Event("change"));
            }
        }, 400);

        // Restore operation and dimensions after feature loads
        setTimeout(() => {
            const operationSelect = document.getElementById("operationSelect");
            if (operationSelect && jobData.operation_id) {
                operationSelect.value = jobData.operation_id;
                operationSelect.dispatchEvent(new Event("change"));
            }

            // Restore dimensions
            if (jobData.dimensions) {
                Object.entries(jobData.dimensions).forEach(([key, val]) => {
                    const input = document.querySelector(`[name="${key}"]`);
                    if (input) input.value = val;
                });
            }

            // Restore calculated values
            if (jobData.total_time) {
                const timeEl = document.getElementById("totalTimeDisplay");
                if (timeEl) timeEl.textContent = `${jobData.total_time.toFixed(2)} min`;
            }
            if (jobData.total_cost) {
                const costEl = document.getElementById("totalCostDisplay");
                if (costEl) costEl.textContent = `₹${jobData.total_cost.toFixed(2)}`;
            }
        }, 700);
            
    } catch (error) {
        console.error('Error loading job details:', error);
        showError('Failed to load job details. Please refresh the page.');
    }
}

// Helper function to update the UI with job data
function updateJobUI(jobId, jobData) {
    if (!jobData) {
        console.log(`No data found for job ${jobId}`);
        return;
    }
    
    // Restore basic inputs
    if (document.getElementById("jobName")) document.getElementById("jobName").value = jobData.name || "";
    if (document.getElementById("clientName")) document.getElementById("clientName").value = jobData.client_name || "";
    if (document.getElementById("jobDescription")) document.getElementById("jobDescription").value = jobData.description || "";

    // Restore material dropdown and trigger change
    const materialSelect = document.getElementById("materialSelect");
    if (materialSelect && jobData.material_id) {
        materialSelect.value = jobData.material_id;
        materialSelect.dispatchEvent(new Event("change"));
    }

    // Wait for features to load, then select the right feature & operation
    setTimeout(() => {
        const featureSelect = document.getElementById("featureSelect");
        if (featureSelect && jobData.feature_id) {
            featureSelect.value = jobData.feature_id;
            featureSelect.dispatchEvent(new Event("change"));
        }
    }, 500);

    // Then set operation and dimensions
    setTimeout(() => {
        const operationSelect = document.getElementById("operationSelect");
        if (operationSelect && jobData.operation_id) {
            operationSelect.value = jobData.operation_id;
            operationSelect.dispatchEvent(new Event("change"));
        }

        // Restore dimensions (after UI loads)
        if (jobData.dimensions) {
            for (const [key, value] of Object.entries(jobData.dimensions)) {
                const input = document.querySelector(`input[name="${key}"]`);
                if (input) input.value = value;
            }
        }

        // Restore results using the correct element IDs
        if (jobData.total_time !== undefined) {
            const t = document.getElementById("totalTimeDisplay");
            if (t) t.textContent = `${jobData.total_time.toFixed(2)} min`;
        }
        if (jobData.total_cost !== undefined) {
            const c = document.getElementById("totalCostDisplay");
            if (c) c.textContent = `₹${jobData.total_cost.toFixed(2)}`;
        }
    }, 800);
}

// Global job selection tracker
let selectedJobId = null;

// Called when user clicks a job card
function selectJob(jobId) {
    selectedJobId = jobId;
    console.log("✅ Job selected:", selectedJobId);
    window.currentJobId = jobId;

    
    // Update UI to show active job
    document.querySelectorAll('.job-card').forEach(card => {
        card.classList.remove('ring-2', 'ring-blue-500');
        if (card.dataset.jobId === jobId.toString()) {
            card.classList.add('ring-2', 'ring-blue-500');
        }
    });
    
    // Open the job
    openJob(jobId);
}

// Open a job and load its details
function openJob(jobId) {
    if (!jobId) {
        console.error("❌ No job ID provided to openJob");
        return;
    }
    
    console.log("🔓 Opening job:", jobId);
    selectedJobId = jobId;
    
    // Show the main content area if it's hidden
    const mainContent = document.getElementById('mainContent');
    if (mainContent && mainContent.classList.contains('hidden')) {
        mainContent.classList.remove('hidden');
    }
    
    // Close any open part details
    document.querySelectorAll('.job-parts').forEach(part => {
        part.classList.add('hidden');
    });
    
    // Load job details from server first
    loadJobDetails(jobId);
    
    // Restore saved data if available
    const jobData = jobDataStore[jobId];
    if (!jobData) {
        console.log("ℹ️ No saved data found for job", jobId);
        return;
    }
    
    // Update job header
    const jobHeader = document.getElementById('jobHeader');
    if (jobHeader) {
        jobHeader.classList.remove('hidden');
        document.getElementById('jobHeaderName').textContent = `Job: ${jobData.name || 'Unnamed Job'}`;
        document.getElementById('jobHeaderClient').textContent = `Client: ${jobData.client_name || 'No client specified'}`;
        document.getElementById('jobHeaderDesc').textContent = `Description: ${jobData.description || 'No description'}`;
    }
    
    console.log("📂 Restoring job data:", jobData);
    
    // Restore basic inputs
    if (document.getElementById("jobName")) document.getElementById("jobName").value = jobData.name || "";
    if (document.getElementById("clientName")) document.getElementById("clientName").value = jobData.client_name || "";
    if (document.getElementById("jobDescription")) document.getElementById("jobDescription").value = jobData.description || "";

    // Restore material dropdown and trigger change
    const materialSelect = document.getElementById("materialSelect");
    if (materialSelect && jobData.material_id) {
        materialSelect.value = jobData.material_id;
        materialSelect.dispatchEvent(new Event("change"));
    }

    // Wait for features to load, then select the right feature & operation
    setTimeout(() => {
        const featureSelect = document.getElementById("featureSelect");
        if (featureSelect && jobData.feature_id) {
            featureSelect.value = jobData.feature_id;
            featureSelect.dispatchEvent(new Event("change"));
        }
    }, 500);

    // Then set operation and dimensions
    setTimeout(() => {
        const operationSelect = document.getElementById("operationSelect");
        if (operationSelect && jobData.operation_id) {
            operationSelect.value = jobData.operation_id;
            operationSelect.dispatchEvent(new Event("change"));
        }

        // Restore dimensions (after UI loads)
        if (jobData.dimensions) {
            for (const [key, value] of Object.entries(jobData.dimensions)) {
                const input = document.querySelector(`input[name="${key}"]`);
                if (input) input.value = value;
            }
        }

        // Restore results using the correct element IDs
        if (jobData.total_time !== undefined) {
            const t = document.getElementById("totalTimeDisplay");
            if (t) t.textContent = `${jobData.total_time.toFixed(2)} min`;
        }
        if (jobData.total_cost !== undefined) {
            const c = document.getElementById("totalCostDisplay");
            if (c) c.textContent = `₹${jobData.total_cost.toFixed(2)}`;
        }
    }, 800);
    
    // Update URL to reflect the open job
    window.history.pushState({ jobId }, `Job ${jobId}`, `?job=${jobId}`);
}

// Export functions to global scope
window.selectJob = selectJob;
window.saveCurrentJob = saveCurrentJob;
window.openJob = openJob;

// Initialize the jobs functionality
document.addEventListener('DOMContentLoaded', () => {
    console.log("📂 Loading jobs...");
    // Load jobs when the page loads
    loadJobs();
    
    // Initialize the calculator
    initializeLatheCalculator();
    
    // Add event listener for the refresh button
    const refreshButton = document.getElementById('refreshJobs');
    if (refreshButton) {
        refreshButton.addEventListener('click', loadJobs);
    }

    // Add event listener for the Save Job button
    const saveJobBtn = document.getElementById('saveJobBtn');
    if (saveJobBtn) {
        saveJobBtn.addEventListener('click', () => {
            if (!selectedJobId) {
                showError('No job selected. Please select a job first.');
                return;
            }
            console.log("💾 Saving job:", selectedJobId);
            saveCurrentJob(selectedJobId);
        });
    }
    
    // Add event listener for the create job form
    const createJobForm = document.getElementById('createJobForm');
    if (createJobForm) {
        createJobForm.addEventListener('submit', (e) => {
            e.preventDefault();
            createNewJob();
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('newJobModal');
        if (e.target === modal) {
            closeNewJobModal();
        }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeNewJobModal();
        }
    });
});
