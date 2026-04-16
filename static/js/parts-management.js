// Parts Management Module
class PartsManager {
    constructor(jobId) {
        this.jobId = jobId;
        this.partsContainer = document.getElementById('parts-container');
        this.initializeEventListeners();
        this.loadParts();
    }

    initializeEventListeners() {
        // Add part button
        document.getElementById('add-part-btn').addEventListener('click', () => this.showAddPartModal());
        
        // Modal save buttons
        document.getElementById('save-part-btn').addEventListener('click', () => this.savePart());
        document.getElementById('save-operation-btn').addEventListener('click', () => this.saveOperation());
        
        // Close modal buttons
        document.querySelectorAll('[data-dismiss="modal"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const modalId = btn.closest('.modal').id;
                this.closeModal(modalId);
            });
        });
    }

    async loadParts() {
        try {
            this.showLoading(true);
            const response = await fetch(`/api/jobs/${this.jobId}/parts`);
            const parts = await response.json();
            this.renderParts(parts);
        } catch (error) {
            console.error('Error loading parts:', error);
            this.showToast('Error loading parts', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    renderParts(parts) {
        this.partsContainer.innerHTML = '';
        
        if (parts.length === 0) {
            this.partsContainer.innerHTML = `
                <div class="alert alert-info">
                    No parts found. Click 'Add Part' to get started.
                </div>
            `;
            return;
        }

        parts.forEach(part => {
            const partElement = this.createPartElement(part);
            this.partsContainer.appendChild(partElement);
        });
    }

    createPartElement(part) {
        const partElement = document.createElement('div');
        partElement.className = 'card mb-3';
        partElement.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">${part.name}</h5>
                <div>
                    <button class="btn btn-sm btn-outline-primary calculate-part" data-part-id="${part.id}">
                        Calculate
                    </button>
                    <button class="btn btn-sm btn-outline-secondary edit-part" data-part-id="${part.id}">
                        Edit
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-part" data-part-id="${part.id}">
                        Delete
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div class="row mb-2">
                    <div class="col-md-4"><strong>Material Cost:</strong> ₹${part.material_cost?.toFixed(2) || '0.00'}</div>
                    <div class="col-md-4"><strong>Total Time:</strong> ${part.total_time?.toFixed(2) || '0.00'} min</div>
                    <div class="col-md-4"><strong>Total Cost:</strong> ₹${part.total_cost?.toFixed(2) || '0.00'}</div>
                </div>
                <div class="operations-container" id="operations-${part.id}">
                    <!-- Operations will be loaded here -->
                </div>
                <button class="btn btn-sm btn-outline-primary mt-2 add-operation" data-part-id="${part.id}">
                    + Add Operation
                </button>
            </div>
        `;

        // Add event listeners
        partElement.querySelector('.calculate-part').addEventListener('click', (e) => this.calculatePart(e));
        partElement.querySelector('.edit-part').addEventListener('click', () => this.editPart(part));
        partElement.querySelector('.delete-part').addEventListener('click', () => this.deletePart(part.id));
        partElement.querySelector('.add-operation').addEventListener('click', (e) => this.showAddOperationModal(e));
        
        // Load operations for this part
        this.loadOperations(part.id);
        
        return partElement;
    }

    showAddPartModal(part = null) {
        const modal = document.getElementById('partModal');
        const form = document.getElementById('part-form');
        
        if (part) {
            // Edit mode
            document.getElementById('part-id').value = part.id;
            document.getElementById('part-name').value = part.name;
            document.getElementById('material-cost').value = part.material_cost || '';
            document.getElementById('modal-part-title').textContent = 'Edit Part';
        } else {
            // Add mode
            form.reset();
            document.getElementById('modal-part-title').textContent = 'Add New Part';
        }
        
        $(modal).modal('show');
    }

    async savePart() {
        const form = document.getElementById('part-form');
        const partId = document.getElementById('part-id').value;
        const isEdit = !!partId;
        
        const partData = {
            name: document.getElementById('part-name').value,
            material_cost: parseFloat(document.getElementById('material-cost').value) || 0
        };

        try {
            this.showLoading(true);
            let response;
            
            if (isEdit) {
                response = await fetch(`/api/parts/${partId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(partData)
                });
            } else {
                response = await fetch(`/api/jobs/${this.jobId}/parts`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(partData)
                });
            }

            if (!response.ok) {
                throw new Error('Failed to save part');
            }

            this.closeModal('partModal');
            this.showToast(`Part ${isEdit ? 'updated' : 'added'} successfully`, 'success');
            this.loadParts();
        } catch (error) {
            console.error('Error saving part:', error);
            this.showToast(`Error ${isEdit ? 'updating' : 'adding'} part`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async deletePart(partId) {
        if (!confirm('Are you sure you want to delete this part? All operations will also be deleted.')) {
            return;
        }

        try {
            this.showLoading(true);
            const response = await fetch(`/api/parts/${partId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete part');
            }

            this.showToast('Part deleted successfully', 'success');
            this.loadParts();
        } catch (error) {
            console.error('Error deleting part:', error);
            this.showToast('Error deleting part', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async calculatePart(event) {
        const partId = typeof event === 'object' ? event.target.dataset.partId : event;
        try {
            this.showLoading(true);
            const response = await fetch(`/api/parts/${partId}/calculate`);
            const result = await response.json();
            
            if (response.ok) {
                // Update the display with new calculations
                const partElement = document.querySelector(`.card [data-part-id="${partId}"]`).closest('.card');
                if (partElement) {
                    partElement.querySelector('.total-time').textContent = result.total_time.toFixed(2);
                    partElement.querySelector('.total-cost').textContent = result.total_cost.toFixed(2);
                }
                
                // Update operations list if needed
                this.loadOperations(partId);
                
                this.showToast('Part calculations updated', 'success');
            } else {
                throw new Error(result.message || 'Failed to calculate');
            }
        } catch (error) {
            console.error('Error calculating part:', error);
            this.showToast('Error calculating part', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // Operation related methods
    async loadOperations(partId) {
        try {
            const response = await fetch(`/api/parts/${partId}/operations`);
            const operations = await response.json();
            this.renderOperations(partId, operations);
        } catch (error) {
            console.error('Error loading operations:', error);
        }
    }

    renderOperations(partId, operations) {
        const container = document.getElementById(`operations-${partId}`);
        if (!container) return;

        if (!operations || operations.length === 0) {
            container.innerHTML = '<div class="text-muted">No operations yet. Add one to get started.</div>';
            return;
        }

        let html = `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Operation</th>
                            <th>Type</th>
                            <th>Time (min)</th>
                            <th>Machining Cost</th>
                            <th>Tooling Cost</th>
                            <th>Total</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        operations.forEach(op => {
            const total = (op.machining_cost || 0) + (op.tooling_cost || 0);
            html += `
                <tr data-operation-id="${op.id}">
                    <td>${op.name}</td>
                    <td>${op.type}</td>
                    <td>${op.machining_time?.toFixed(2) || '0.00'}</td>
                    <td>₹${op.machining_cost?.toFixed(2) || '0.00'}</td>
                    <td>₹${op.tooling_cost?.toFixed(2) || '0.00'}</td>
                    <td>₹${total.toFixed(2)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary edit-operation" 
                                data-operation-id="${op.id}">
                            Edit
                        </button>
                        <button class="btn btn-sm btn-outline-danger delete-operation" 
                                data-operation-id="${op.id}">
                            Delete
                        </button>
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = html;

        // Add event listeners for operation actions
        container.querySelectorAll('.edit-operation').forEach(btn => {
            btn.addEventListener('click', (e) => this.editOperation(e));
        });
        
        container.querySelectorAll('.delete-operation').forEach(btn => {
            btn.addEventListener('click', (e) => this.deleteOperation(e));
        });
    }

    showAddOperationModal(event) {
        const partId = event.target.dataset.partId;
        const modal = document.getElementById('operationModal');
        const form = document.getElementById('operation-form');
        
        // Store the part ID for later use
        form.dataset.partId = partId;
        
        // Reset form and show modal
        form.reset();
        document.getElementById('modal-operation-title').textContent = 'Add New Operation';
        $(modal).modal('show');
    }

    async saveOperation() {
        const form = document.getElementById('operation-form');
        const operationId = document.getElementById('operation-id').value;
        const partId = form.dataset.partId;
        const isEdit = !!operationId;
        
        const operationData = {
            name: document.getElementById('operation-name').value,
            type: document.getElementById('operation-type').value,
            machining_time: parseFloat(document.getElementById('machining-time').value) || 0,
            machining_cost: parseFloat(document.getElementById('machining-cost').value) || 0,
            tooling_cost: parseFloat(document.getElementById('tooling-cost').value) || 0
        };

        try {
            this.showLoading(true);
            let response;
            
            if (isEdit) {
                response = await fetch(`/api/operations/${operationId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(operationData)
                });
            } else {
                response = await fetch(`/api/parts/${partId}/operations`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(operationData)
                });
            }

            if (!response.ok) {
                throw new Error('Failed to save operation');
            }

            this.closeModal('operationModal');
            this.showToast(`Operation ${isEdit ? 'updated' : 'added'} successfully`, 'success');
            
            // Reload the operations for this part
            this.loadOperations(partId);
            
            // Recalculate part totals
            this.calculatePart({ target: { dataset: { partId } } });
        } catch (error) {
            console.error('Error saving operation:', error);
            this.showToast(`Error ${isEdit ? 'updating' : 'adding'} operation`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async deleteOperation(event) {
        const operationId = event.target.dataset.operationId;
        const partId = event.target.closest('.operations-container').id.replace('operations-', '');
        
        if (!confirm('Are you sure you want to delete this operation?')) {
            return;
        }

        try {
            this.showLoading(true);
            const response = await fetch(`/api/operations/${operationId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete operation');
            }

            this.showToast('Operation deleted successfully', 'success');
            
            // Reload operations and recalculate part
            this.loadOperations(partId);
            this.calculatePart({ target: { dataset: { partId } } });
        } catch (error) {
            console.error('Error deleting operation:', error);
            this.showToast('Error deleting operation', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // Utility methods
    showLoading(show) {
        const loader = document.getElementById('loading-indicator');
        if (loader) {
            loader.style.display = show ? 'block' : 'none';
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            } else {
                // Fallback if no Bootstrap modal instance exists
                const modalElement = bootstrap.Modal.getOrCreateInstance(modal);
                modalElement.hide();
            }
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;
        
        const toastId = `toast-${Date.now()}`;
        const bgClass = type === 'success' ? 'bg-success' :
                        type === 'error' ? 'bg-danger' :
                        'bg-info';
                        
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0 mb-2" 
                 role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                            data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        const toastEl = new bootstrap.Toast(document.getElementById(toastId));
        toastEl.show();
        
        // Auto-remove toast after it's hidden
        document.getElementById(toastId).addEventListener('hidden.bs.toast', function () {
            this.remove();
        });
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    }
}

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const jobId = document.body.dataset.jobId;
    if (jobId) {
        window.partsManager = new PartsManager(jobId);
    }
});
