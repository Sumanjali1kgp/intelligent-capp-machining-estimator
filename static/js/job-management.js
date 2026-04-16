// Job Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the jobs list when the page loads
    loadJobs();
    
    // Add event listeners
    const refreshBtn = document.getElementById('refreshJobsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadJobs);
    }
    
    // Handle new job form submission
    const newJobForm = document.getElementById('newJobForm');
    if (newJobForm) {
        newJobForm.addEventListener('submit', handleNewJobSubmit);
    }
    
    // Close modal when clicking outside
    const modal = document.getElementById('newJobModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeNewJobModal();
            }
        });
    }
});

// Load and display jobs
async function loadJobs() {
    const jobsList = document.getElementById('jobsList');
    const emptyState = document.getElementById('emptyState');
    
    if (!jobsList) return;
    
    try {
        // Show loading state
        jobsList.innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <div class="spinner mx-auto mb-3"></div>
                <p>Loading jobs...</p>
            </div>
        `;
        
        if (emptyState) emptyState.classList.add('hidden');
        
        // Fetch jobs from the API
        const response = await fetch('/api/jobs');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const jobs = await response.json();
        
        // Update the UI
        if (jobs.length === 0) {
            // Show empty state
            jobsList.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }
        
        // Hide empty state if it's visible
        if (emptyState) emptyState.classList.add('hidden');
        
        // Render jobs
        // In the loadJobs function, update the job card HTML to include the delete button
        jobsList.innerHTML = jobs.map(job => `
            <div class="job-card border border-gray-200 rounded-lg overflow-hidden">
                <div class="job-header p-4 bg-gray-50 border-b border-gray-200 cursor-pointer" 
                     onclick="toggleJobParts(${job.id}, this)">
                    <div class="flex justify-between items-center">
                        <div>
                            <h3 class="text-lg font-medium text-gray-900">${escapeHtml(job.name)}</h3>
                            <p class="text-sm text-gray-500">
                                Created: ${formatDate(job.created_at)}
                                ${job.parts && job.parts.length > 0 
                                    ? `• ${job.parts.length} ${job.parts.length === 1 ? 'Part' : 'Parts'}` 
                                    : ''}
                            </p>
                        </div>
                        <div class="flex items-center space-x-2">
                            <button onclick="event.stopPropagation(); deleteJob(${job.id})" 
                                    class="text-red-500 hover:text-red-700 p-1" 
                                    title="Delete Job">
                                <i class="fas fa-trash"></i>
                            </button>
                            <div class="text-gray-400 transform transition-transform duration-200">
                                <i class="fas fa-chevron-down"></i>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="job-parts hidden">
                    <div class="p-4 bg-white border-t border-gray-100">
                        ${job.parts && job.parts.length > 0 
                            ? renderPartsList(job.parts, job.id) 
                            : '<p class="text-sm text-gray-500 text-center py-2">No parts added yet</p>'}
                        
                        <div class="mt-4">
                            <button onclick="event.stopPropagation(); showAddPartForm(${job.id})" 
                                    class="text-sm text-blue-600 hover:text-blue-800 flex items-center">
                                <i class="fas fa-plus mr-1"></i> Add Part
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading jobs:', error);
        jobsList.innerHTML = `
            <div class="bg-red-50 border-l-4 border-red-400 p-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <i class="fas fa-exclamation-circle text-red-400"></i>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm text-red-700">
                            Failed to load jobs. Please try again later.
                            <button onclick="loadJobs()" class="text-red-600 hover:text-red-500 font-medium ml-1">
                                Retry
                            </button>
                        </p>
                    </div>
                </div>
            </div>
        `;
    }
}

// Toggle job parts visibility
function toggleJobParts(jobId, headerElement) {
    const jobCard = headerElement.closest('.job-card');
    const partsContainer = jobCard.querySelector('.job-parts');
    const icon = headerElement.querySelector('i');
    
    // Toggle the parts container
    partsContainer.classList.toggle('hidden');
    
    // Rotate the chevron icon
    icon.classList.toggle('transform');
    icon.classList.toggle('rotate-180');
    
    // If we're showing the parts and they haven't been loaded yet, load them
    if (!partsContainer.classList.contains('hidden') && !partsContainer.hasAttribute('data-loaded')) {
        loadJobParts(jobId, partsContainer);
    }
}

// Load parts for a specific job
async function loadJobParts(jobId, container) {
    if (!jobId || !container) return;
    
    try {
        // Show loading state
        const partsContent = container.querySelector('> div');
        const originalContent = partsContent.innerHTML;
        partsContent.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner mx-auto"></div>
                <p class="text-sm text-gray-500 mt-2">Loading parts...</p>
            </div>
        `;
        
        const response = await fetch(`/api/jobs/${jobId}/parts`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const parts = await response.json();
        
        // Mark as loaded
        container.setAttribute('data-loaded', 'true');
        
        // Update the parts list
        if (parts.length === 0) {
            partsContent.innerHTML = `
                <p class="text-sm text-gray-500 text-center py-2">No parts added yet</p>
                <div class="mt-4">
                    <button onclick="event.stopPropagation(); showAddPartForm(${jobId})" 
                            class="text-sm text-blue-600 hover:text-blue-800 flex items-center">
                        <i class="fas fa-plus mr-1"></i> Add Part
                    </button>
                </div>
            `;
        } else {
            partsContent.innerHTML = `
                ${renderPartsList(parts, jobId)}
                <div class="mt-4">
                    <button onclick="event.stopPropagation(); showAddPartForm(${jobId})" 
                            class="text-sm text-blue-600 hover:text-blue-800 flex items-center">
                        <i class="fas fa-plus mr-1"></i> Add Part
                    </button>
                </div>
            `;
        }
        
    } catch (error) {
        console.error(`Error loading parts for job ${jobId}:`, error);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-50 border-l-4 border-red-400 p-4 mb-4';
        errorDiv.innerHTML = `
            <div class="flex">
                <div class="flex-shrink-0">
                    <i class="fas fa-exclamation-circle text-red-400"></i>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-red-700">
                        Failed to load parts. 
                        <button onclick="loadJobParts(${jobId}, this.closest('.job-parts'))" 
                                class="text-red-600 hover:text-red-500 font-medium ml-1">
                            Retry
                        </button>
                    </p>
                </div>
            </div>
        `;
        
        container.innerHTML = '';
        container.appendChild(errorDiv);
    }
}

// Render parts list HTML
// Render parts list HTML
function renderPartsList(parts, jobId) {
    return `
        <ul class="space-y-2">
            ${parts.map(part => `
                <li class="part-item p-3 border border-gray-200 rounded-md hover:bg-gray-50">
                    <div class="flex justify-between items-center">
                        <div>
                            <h4 class="font-medium text-gray-900">${escapeHtml(part.name)}</h4>
                            <p class="text-sm text-gray-500">
                                Material Cost: ${formatCurrency(part.material_cost)}
                                ${part.operations && part.operations.length > 0 
                                    ? `• ${part.operations.length} ${part.operations.length === 1 ? 'Operation' : 'Operations'}` 
                                    : ''}
                            </p>
                        </div>
                        <div class="flex space-x-2">
                            <button onclick="event.stopPropagation(); showPartDetails(${jobId}, ${part.id})" 
                                    class="text-blue-600 hover:text-blue-800 p-1 rounded-full hover:bg-blue-50"
                                    title="View Details">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button onclick="event.stopPropagation(); showAddOperationForm(${jobId}, ${part.id})" 
                                    class="text-green-600 hover:text-green-800 p-1 rounded-full hover:bg-green-50"
                                    title="Add Operation">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                </li>
            `).join('')}
        </ul>
    `;
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
        // Reset the form
        const form = document.getElementById('newJobForm');
        if (form) form.reset();
    }
}

// Handle new job form submission
async function handleNewJobSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const jobName = form.jobName.value.trim();
    const submitBtn = form.querySelector('button[type="submit"]');
    const submitBtnText = submitBtn.innerHTML;
    
    if (!jobName) {
        showError('Please enter a job name');
        return;
    }
    
    try {
        // Update button state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Creating...';
        
        // Create the job
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
        
        // Close the modal and refresh the jobs list
        closeNewJobModal();
        showSuccess('Job created successfully!');
        loadJobs();
        
    } catch (error) {
        console.error('Error creating job:', error);
        showError(error.message || 'Failed to create job. Please try again.');
    } finally {
        // Reset button state
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = submitBtnText;
        }
    }
}
// Add this function to job-management.js
async function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job and all its parts?')) {
        return;
    }

    try {
        const response = await fetch(`/api/jobs/${jobId}`, {
            method: 'DELETE',
        });

        if (!response.ok) {
            throw new Error('Failed to delete job');
        }

        // Show success message and refresh the jobs list
        showSuccess('Job deleted successfully');
        loadJobs();
    } catch (error) {
        console.error('Error deleting job:', error);
        showError('Failed to delete job. Please try again.');
    }
}
// Show add part form (placeholder function)
// Show add part form
function showAddPartForm(jobId) {
    const partName = prompt('Enter part name:');
    if (!partName) return;

    // In a real implementation, you would make an API call to create the part
    // For now, we'll just show a message
    alert(`Part "${partName}" will be added to job ${jobId} in the next step.`);
    console.log('Adding part:', { jobId, partName });
    
    // Here you would typically make an API call to create the part
    // Example:
    /*
    fetch(`/api/jobs/${jobId}/parts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: partName })
    })
    .then(response => response.json())
    .then(part => {
        showSuccess('Part added successfully');
        loadJobs(); // Refresh the jobs list
    })
    .catch(error => {
        console.error('Error adding part:', error);
        showError('Failed to add part');
    });
    */
}
// Show part details (placeholder function)
function showPartDetails(jobId, partId) {
    // This will be implemented in a separate step
    console.log('Show part details:', { jobId, partId });
    alert('Part details functionality will be implemented in the next step.');
}

// Show add operation form (placeholder function)
// Show add operation form
function showAddOperationForm(jobId, partId) {
    // In a real implementation, you would show a modal with a form
    // For now, we'll just show a message
    alert(`Operation form for part ${partId} in job ${jobId} will be implemented in the next step.`);
    console.log('Showing operation form for:', { jobId, partId });
    
    // Here you would typically show a modal with a form to add an operation
    // Then make an API call to create the operation
}

// Helper function to format dates
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Helper function to format currency
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '$0.00';
    
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(amount);
}

// Helper function to escape HTML
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Show success message
function showSuccess(message) {
    // This could be replaced with a more sophisticated notification system
    alert(`Success: ${message}`);
}

// Show error message
function showError(message) {
    // This could be replaced with a more sophisticated notification system
    alert(`Error: ${message}`);
}

// Make functions available globally
// Make functions available globally
window.toggleJobParts = toggleJobParts;
window.showAddPartForm = showAddPartForm;
window.showPartDetails = showPartDetails;
window.showAddOperationForm = showAddOperationForm;
window.showNewJobModal = showNewJobModal;
window.closeNewJobModal = closeNewJobModal;
window.loadJobParts = loadJobParts;
window.deleteJob = deleteJob;  // Add this line