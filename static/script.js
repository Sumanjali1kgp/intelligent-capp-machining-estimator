import { calculateCostBreakdown } from './cost.js';
import { calculateTimeBreakdown } from './time.js';

const OVERHEAD_RATE = 0.4;

const PROCESS_FIELD_DEFS = {
    turning: [
        field('initial_diameter', 'Initial Diameter (mm)', 'number', 'Starting stock diameter before turning.', { min: 0.01, step: 0.01 }),
        field('final_diameter', 'Final Diameter (mm)', 'number', 'Target finished diameter after turning.', { min: 0.01, step: 0.01 }),
        field('length', 'Length of Cut (mm)', 'number', 'Axial distance the turning tool travels.', { min: 0.01, step: 0.01 }),
    ],
    facing: [
        field('diameter', 'Facing Diameter (mm)', 'number', 'Workpiece diameter at the face being machined.', { min: 0.01, step: 0.01 }),
        field('depth_of_cut', 'Depth of Cut (mm)', 'number', 'Axial material removed during facing.', { min: 0.01, step: 0.01 }),
    ],
    drilling: [
        field('diameter', 'Hole Diameter (mm)', 'number', 'Drill diameter used for the hole.', { min: 0.01, step: 0.01 }),
        field('depth', 'Hole Depth (mm)', 'number', 'Total drilling depth measured along the axis.', { min: 0.01, step: 0.01 }),
        field('peck_depth', 'Peck Depth (mm)', 'number', 'Optional drilling depth per peck cycle.', { min: 0.01, step: 0.01, optional: true }),
    ],
    boring: [
        field('initial_diameter', 'Initial Bore Diameter (mm)', 'number', 'Existing hole diameter before boring.', { min: 0.01, step: 0.01 }),
        field('final_diameter', 'Final Bore Diameter (mm)', 'number', 'Target bore diameter after boring.', { min: 0.01, step: 0.01 }),
        field('depth', 'Bore Depth (mm)', 'number', 'Length of the boring pass.', { min: 0.01, step: 0.01 }),
    ],
    reaming: [
        field('diameter', 'Hole Diameter (mm)', 'number', 'Finished diameter to be reamed.', { min: 0.01, step: 0.01 }),
        field('depth', 'Hole Depth (mm)', 'number', 'Depth of the hole to be reamed.', { min: 0.01, step: 0.01 }),
    ],
    grooving: [
        field('groove_width', 'Groove Width (mm)', 'number', 'Axial width of the groove.', { min: 0.01, step: 0.01 }),
        field('groove_depth', 'Groove Depth (mm)', 'number', 'Radial depth of the groove.', { min: 0.01, step: 0.01 }),
    ],
    threading: [
        field('diameter', 'Thread Diameter (mm)', 'number', 'Major diameter of the thread.', { min: 0.01, step: 0.01 }),
        field('length', 'Thread Length (mm)', 'number', 'Threaded length along the axis.', { min: 0.01, step: 0.01 }),
        field('pitch', 'Pitch (mm)', 'number', 'Thread pitch or lead per revolution.', { min: 0.01, step: 0.01 }),
        field('type', 'Thread Type', 'select', 'Choose whether the thread is internal or external.', {
            options: [
                { value: 'external', label: 'External' },
                { value: 'internal', label: 'Internal' },
            ],
        }),
    ],
    knurling: [
        field('length', 'Knurl Length (mm)', 'number', 'Length to be textured with the knurling tool.', { min: 0.01, step: 0.01 }),
        field('diameter', 'Workpiece Diameter (mm)', 'number', 'Current workpiece diameter at the knurl zone.', { min: 0.01, step: 0.01 }),
    ],
    parting: [
        field('diameter', 'Workpiece Diameter (mm)', 'number', 'Current workpiece diameter at the cut-off location.', { min: 0.01, step: 0.01 }),
        field('depth', 'Parting Depth (mm)', 'number', 'Radial depth to cut for the parting operation.', { min: 0.01, step: 0.01 }),
        field('width', 'Tool Width (mm)', 'number', 'Optional parting blade width.', { min: 0.01, step: 0.01, optional: true }),
    ],
    milling: [
        field('width', 'Cut Width (mm)', 'number', 'Width of the milling cut.', { min: 0.01, step: 0.01 }),
        field('length', 'Cut Length (mm)', 'number', 'Length of tool travel in the cut.', { min: 0.01, step: 0.01 }),
        field('depth', 'Depth per Pass (mm)', 'number', 'Depth removed in each milling pass.', { min: 0.01, step: 0.01 }),
        field('total_depth', 'Total Depth (mm)', 'number', 'Total material depth to remove.', { min: 0.01, step: 0.01, optional: true }),
        field('tool_diameter', 'Tool Diameter (mm)', 'number', 'Milling cutter diameter.', { min: 0.01, step: 0.01, optional: true }),
    ],
};

PROCESS_FIELD_DEFS['taper turning'] = PROCESS_FIELD_DEFS.turning;
PROCESS_FIELD_DEFS.contouring = PROCESS_FIELD_DEFS.turning;
PROCESS_FIELD_DEFS.chamfering = PROCESS_FIELD_DEFS.facing;

const OVERRIDE_FIELDS = [
    field('feed', 'Feed Override', 'number', 'Optional manual feed override sent to the calculator.', { min: 0.01, step: 0.01, optional: true }),
    field('spindle_speed', 'Spindle Speed Override', 'number', 'Optional manual spindle speed override sent to the calculator.', { min: 0.01, step: 0.01, optional: true }),
];

const state = {
    jobs: [],
    materials: [],
    features: [],
    featureOperations: {},
    currentJobId: null,
    selectedMaterialId: '',
    jobDraft: {
        name: '',
        clientName: '',
        description: '',
        partName: 'Primary Part',
    },
    manualTimes: {
        setup: 0,
        tool: 0,
        idle: 0,
        misc: 0,
    },
    costInputs: {
        materialCost: 0,
        laborRatePerHour: 0,
        toolCostPerUse: 0,
        miscCost: 0,
    },
    processes: [],
    summaries: {
        time: calculateTimeBreakdown(),
        cost: calculateCostBreakdown({ timeBreakdown: {} }),
    },
    charts: {
        cost: null,
    },
};

const dom = {};

document.addEventListener('DOMContentLoaded', () => {
    if (document.body.dataset.page !== 'lathe') {
        return;
    }

    cacheDom();
    bindEvents();
    initializeWorkspace();
});

async function initializeWorkspace() {
    try {
        showStatus('Loading workspace...', 'info');
        await Promise.all([loadJobs(), loadMaterials(), loadFeatures()]);
        recalculateSummaries();
        renderAll();
        showStatus('Workspace ready. Select a material and start building operations.', 'success');
    } catch (error) {
        console.error(error);
        showStatus(error.message || 'Failed to initialize workspace.', 'error');
    }
}

function cacheDom() {
    dom.statusBanner = document.getElementById('statusBanner');
    dom.jobNameInput = document.getElementById('jobNameInput');
    dom.clientNameInput = document.getElementById('clientNameInput');
    dom.partNameInput = document.getElementById('partNameInput');
    dom.jobDescriptionInput = document.getElementById('jobDescriptionInput');
    dom.materialSelect = document.getElementById('materialSelect');
    dom.jobsList = document.getElementById('jobsList');
    dom.processList = document.getElementById('processList');
    dom.selectedJobSummary = document.getElementById('selectedJobSummary');
    dom.addProcessBtn = document.getElementById('addProcessBtn');
    dom.refreshJobsBtn = document.getElementById('refreshJobsBtn');
    dom.saveJobBtn = document.getElementById('saveJobBtn');
    dom.duplicateCurrentJobBtn = document.getElementById('duplicateCurrentJobBtn');
    dom.resetWorkspaceBtn = document.getElementById('resetWorkspaceBtn');
    dom.exportShopBtn = document.getElementById('exportShopBtn');
    dom.exportCustomerBtn = document.getElementById('exportCustomerBtn');
    dom.manualSetupTime = document.getElementById('manualSetupTime');
    dom.manualToolTime = document.getElementById('manualToolTime');
    dom.manualIdleTime = document.getElementById('manualIdleTime');
    dom.manualMiscTime = document.getElementById('manualMiscTime');
    dom.materialCostInput = document.getElementById('materialCostInput');
    dom.laborRateInput = document.getElementById('laborRateInput');
    dom.toolCostInput = document.getElementById('toolCostInput');
    dom.miscCostInput = document.getElementById('miscCostInput');
    dom.costChart = document.getElementById('costChart');
}

function bindEvents() {
    dom.jobNameInput.addEventListener('input', (event) => {
        state.jobDraft.name = event.target.value;
        renderJobSummary();
    });
    dom.clientNameInput.addEventListener('input', (event) => {
        state.jobDraft.clientName = event.target.value;
        renderJobSummary();
    });
    dom.partNameInput.addEventListener('input', (event) => {
        state.jobDraft.partName = event.target.value;
    });
    dom.jobDescriptionInput.addEventListener('input', (event) => {
        state.jobDraft.description = event.target.value;
        renderJobSummary();
    });
    dom.materialSelect.addEventListener('change', onMaterialChanged);
    dom.addProcessBtn.addEventListener('click', addProcessCard);
    dom.refreshJobsBtn.addEventListener('click', async () => {
        await loadJobs();
        renderJobsList();
        showStatus('Saved jobs refreshed.', 'success');
    });
    dom.saveJobBtn.addEventListener('click', persistCurrentJob);
    dom.duplicateCurrentJobBtn.addEventListener('click', () => duplicateJob(state.currentJobId));
    dom.resetWorkspaceBtn.addEventListener('click', resetWorkspace);
    dom.exportShopBtn.addEventListener('click', () => exportPdf('shop'));
    dom.exportCustomerBtn.addEventListener('click', () => exportPdf('customer'));

    bindNumericInput(dom.manualSetupTime, 'setup', state.manualTimes);
    bindNumericInput(dom.manualToolTime, 'tool', state.manualTimes);
    bindNumericInput(dom.manualIdleTime, 'idle', state.manualTimes);
    bindNumericInput(dom.manualMiscTime, 'misc', state.manualTimes);
    bindNumericInput(dom.materialCostInput, 'materialCost', state.costInputs);
    bindNumericInput(dom.laborRateInput, 'laborRatePerHour', state.costInputs);
    bindNumericInput(dom.toolCostInput, 'toolCostPerUse', state.costInputs);
    bindNumericInput(dom.miscCostInput, 'miscCost', state.costInputs);

    dom.jobsList.addEventListener('click', handleJobsListClick);
    dom.processList.addEventListener('click', handleProcessListClick);
    dom.processList.addEventListener('change', handleProcessListChange);
    dom.processList.addEventListener('input', handleProcessListInput);
}

function bindNumericInput(element, key, target) {
    element.addEventListener('input', (event) => {
        target[key] = toNumber(event.target.value);
        recalculateSummaries();
        renderSummaries();
    });
}

async function loadJobs() {
    state.jobs = await fetchJson('/api/jobs');
}

async function loadMaterials() {
    state.materials = await fetchJson('/api/materials');
    renderMaterialOptions();
}

async function loadFeatures() {
    state.features = await fetchJson('/api/features');
}

async function loadFeatureOperations(featureId) {
    if (!featureId || state.featureOperations[featureId]) {
        return state.featureOperations[featureId] || [];
    }

    const operations = await fetchJson(`/api/feature_operations/${featureId}`);
    state.featureOperations[featureId] = operations;
    return operations;
}

function renderAll() {
    syncFormInputs();
    renderMaterialOptions();
    renderJobSummary();
    renderJobsList();
    renderProcessList();
    renderSummaries();
    renderExportState();
}

function renderMaterialOptions() {
    const options = ['<option value="">Select material</option>'];
    state.materials.forEach((material) => {
        options.push(
            `<option value="${material.material_id}" ${String(state.selectedMaterialId) === String(material.material_id) ? 'selected' : ''}>
                ${escapeHtml(material.material_name)}
            </option>`
        );
    });
    dom.materialSelect.innerHTML = options.join('');
    dom.addProcessBtn.disabled = !state.selectedMaterialId;
}

function renderJobSummary() {
    if (!state.currentJobId && !state.jobDraft.name.trim()) {
        dom.selectedJobSummary.innerHTML = '<p class="summary-empty">No saved job is currently loaded. Start a new one or open an existing job.</p>';
        return;
    }

    const label = state.currentJobId ? `Job #${state.currentJobId}` : 'Unsaved Job';
    dom.selectedJobSummary.innerHTML = `
        <h4>${escapeHtml(label)}: ${escapeHtml(state.jobDraft.name || 'Untitled')}</h4>
        <p>${escapeHtml(state.jobDraft.clientName || 'No client specified')}</p>
        <p>${escapeHtml(state.jobDraft.description || 'No description yet.')}</p>
    `;
}

function renderJobsList() {
    if (state.jobs.length === 0) {
        dom.jobsList.innerHTML = '<p class="summary-empty">No jobs saved yet.</p>';
        return;
    }

    dom.jobsList.innerHTML = state.jobs.map((job) => `
        <article class="job-card ${job.id === state.currentJobId ? 'active' : ''}">
            <div class="job-card-header">
                <div>
                    <h4>${escapeHtml(job.name)}</h4>
                    <p class="job-meta">${escapeHtml(job.client_name || 'No client')} | ${job.part_count || 0} parts | ${formatCurrency(job.total_cost || 0)}</p>
                </div>
                <div class="job-card-actions">
                    <button type="button" class="inline-btn" data-action="open-job" data-job-id="${job.id}">Open</button>
                    <button type="button" class="inline-btn" data-action="duplicate-job" data-job-id="${job.id}">Duplicate</button>
                    <button type="button" class="inline-btn danger" data-action="delete-job" data-job-id="${job.id}">Delete</button>
                </div>
            </div>
        </article>
    `).join('');
}

function renderProcessList() {
    if (state.processes.length === 0) {
        dom.processList.innerHTML = `
            <div class="empty-process-state">
                <h4>No process cards yet</h4>
                <p>Add a material and create your first operation card to begin calculations.</p>
            </div>
        `;
        return;
    }

    dom.processList.innerHTML = state.processes.map(renderProcessCard).join('');
}

function renderProcessCard(process, index) {
    const operationOptions = getOperationOptions(process);
    const selectedOperationLabel = process.operationName || 'Select operation';
    const fieldDefs = PROCESS_FIELD_DEFS[process.operationType] || [];

    return `
        <article class="process-card" data-process-id="${process.id}">
            <div class="process-card-header">
                <div>
                    <p class="section-kicker">Process ${index + 1}</p>
                    <h4>${escapeHtml(selectedOperationLabel)}</h4>
                </div>
                <div class="process-actions">
                    <button type="button" class="inline-btn" data-action="calculate-process" data-process-id="${process.id}">Calculate</button>
                    <button type="button" class="inline-btn danger" data-action="remove-process" data-process-id="${process.id}">Remove</button>
                </div>
            </div>

            <div class="process-grid">
                ${renderSelectField(
                    process.id,
                    'feature',
                    'Feature',
                    state.features.map((featureItem) => ({
                        value: featureItem.feature_id,
                        label: featureItem.feature_name,
                    })),
                    process.featureId,
                    'Select the geometric feature that drives the operation choice.'
                )}
                ${renderSelectField(
                    process.id,
                    'operation',
                    'Operation',
                    operationOptions,
                    process.operationId,
                    'Only operations supported by the active calculation API are listed.'
                )}
                ${fieldDefs.map((definition) => renderInputField(process.id, definition, process.fields[definition.key])).join('')}
                ${OVERRIDE_FIELDS.map((definition) => renderInputField(process.id, definition, process.fields[definition.key])).join('')}
            </div>

            ${renderProcessResult(process)}
        </article>
    `;
}

function renderProcessResult(process) {
    if (process.error) {
        return `
            <div class="process-result error">
                <h5>Validation / Calculation Issue</h5>
                <p>${escapeHtml(process.error)}</p>
            </div>
        `;
    }

    if (!process.result) {
        return `
            <div class="process-result">
                <h5>Awaiting calculation</h5>
                <p>Complete the required fields, then calculate this process card.</p>
            </div>
        `;
    }
    const warnings = Array.isArray(process.result.warnings) ? process.result.warnings : [];

    
    return `
        <div class="process-result">
            <h5>Calculated Output</h5>
            <div class="result-summary">
                <div><strong>Time:</strong> ${formatMinutes(process.result.total_time_minutes || 0)}</div>
                <div><strong>Cost:</strong> ${formatCurrency(process.result.cost || 0)}</div>
            </div>
            ${warnings.length ? `<ul>${warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join('')}</ul>` : ''}
        </div>
    
        



    `;
}




function renderSummaries() {
    const time = state.summaries.time;
    const cost = state.summaries.cost;

    setText('machiningTime', formatMinutes(time.machiningTime));
    setText('idleTime', formatMinutes(time.idleTime));
    setText('setupTime', formatMinutes(time.setupTime));
    setText('toolTime', formatMinutes(time.toolTime));
    setText('miscTime', formatMinutes(time.miscTime));
    setText('totalTime', formatMinutes(time.totalTime));

    setText('materialCost', formatCurrency(cost.materialCost));
    setText('setupIdleCost', formatCurrency(cost.setupIdleCost));
    setText('machiningCost', formatCurrency(cost.machiningCost));
    setText('toolingCost', formatCurrency(cost.toolingCost));
    setText('miscCost', formatCurrency(cost.miscCost));
    setText('totalRawCost', formatCurrency(cost.totalRawCost));
    setText('overheadCost', formatCurrency(cost.overheadCost));
    setText('finalCost', formatCurrency(cost.finalCost));
    renderCostChart(cost);
}

function renderExportState() {
    const canExport = Boolean(state.currentJobId);
    dom.duplicateCurrentJobBtn.disabled = !canExport;
    dom.exportShopBtn.disabled = !canExport;
    dom.exportCustomerBtn.disabled = !canExport;
}

function syncFormInputs() {
    dom.jobNameInput.value = state.jobDraft.name;
    dom.clientNameInput.value = state.jobDraft.clientName;
    dom.jobDescriptionInput.value = state.jobDraft.description;
    dom.partNameInput.value = state.jobDraft.partName;
    dom.manualSetupTime.value = state.manualTimes.setup;
    dom.manualToolTime.value = state.manualTimes.tool;
    dom.manualIdleTime.value = state.manualTimes.idle;
    dom.manualMiscTime.value = state.manualTimes.misc;
    dom.materialCostInput.value = state.costInputs.materialCost;
    dom.laborRateInput.value = state.costInputs.laborRatePerHour;
    dom.toolCostInput.value = state.costInputs.toolCostPerUse;
    dom.miscCostInput.value = state.costInputs.miscCost;
}

function onMaterialChanged(event) {
    state.selectedMaterialId = event.target.value;
    state.processes = state.processes.map((process) => ({
        ...process,
        result: null,
        error: '',
    }));
    recalculateSummaries();
    renderAll();
}

function addProcessCard() {
    if (!state.selectedMaterialId) {
        showStatus('Select a material before adding process cards.', 'error');
        return;
    }

    state.processes.push(createBlankProcess());
    renderProcessList();
}

function createBlankProcess() {
    return {
        id: `process-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        featureId: '',
        operationId: '',
        operationName: '',
        operationType: '',
        fields: {},
        result: null,
        error: '',
    };
}

async function handleJobsListClick(event) {
    const action = event.target.dataset.action;
    const jobId = event.target.dataset.jobId;
    if (!action || !jobId) {
        return;
    }

    if (action === 'open-job') {
        await loadJobIntoWorkspace(jobId);
        return;
    }

    if (action === 'duplicate-job') {
        await duplicateJob(jobId);
        return;
    }

    if (action === 'delete-job') {
        await deleteJob(jobId);
    }
}

async function handleProcessListClick(event) {
    const action = event.target.dataset.action;
    const processId = event.target.dataset.processId;
    if (!action || !processId) {
        return;
    }

    if (action === 'remove-process') {
        state.processes = state.processes.filter((process) => process.id !== processId);
        recalculateSummaries();
        renderAll();
        return;
    }

    if (action === 'calculate-process') {
        await calculateProcess(processId);
    }
}

async function handleProcessListChange(event) {
    const processId = event.target.dataset.processId;
    const fieldKey = event.target.dataset.fieldKey;
    if (!processId || !fieldKey) {
        return;
    }

    const process = findProcess(processId);
    if (!process) {
        return;
    }

    if (fieldKey === 'feature') {
        process.featureId = event.target.value;
        process.operationId = '';
        process.operationName = '';
        process.operationType = '';
        process.fields = {};
        process.result = null;
        process.error = '';
        if (process.featureId) {
            await loadFeatureOperations(process.featureId);
        }
        renderProcessList();
        recalculateSummaries();
        renderSummaries();
        return;
    }

    if (fieldKey === 'operation') {
        const options = getOperationOptions(process);
        const selected = options.find((option) => String(option.value) === String(event.target.value));
        process.operationId = event.target.value;
        process.operationName = selected?.label || '';
        process.operationType = normalizeOperationName(selected?.label || '');
        process.fields = {};
        process.result = null;
        process.error = '';
        renderProcessList();
        recalculateSummaries();
        renderSummaries();
        return;
    }

    process.fields[fieldKey] = event.target.value;
    process.result = null;
    process.error = '';
    recalculateSummaries();
    renderSummaries();
}

function handleProcessListInput(event) {
    const processId = event.target.dataset.processId;
    const fieldKey = event.target.dataset.fieldKey;
    if (!processId || !fieldKey || fieldKey === 'feature' || fieldKey === 'operation') {
        return;
    }

    const process = findProcess(processId);
    if (!process) {
        return;
    }

    process.fields[fieldKey] = event.target.value;
}

async function calculateProcess(processId) {
    const process = findProcess(processId);
    if (!process) {
        return;
    }

    const validationMessage = validateProcess(process);
    if (validationMessage) {
        process.error = validationMessage;
        process.result = null;
        renderProcessList();
        recalculateSummaries();
        renderSummaries();
        return;
    }

    process.error = '';
    const payload = buildCalculationPayload(process);

    try {
        const response = await fetchJson('/api/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        process.result = response.data || {};
        process.result.total_time_minutes = toNumber(response.time, process.result.total_time_minutes);
        recalculateSummaries();
        renderAll();
        showStatus(`${process.operationName} calculated successfully.`, 'success');
    } catch (error) {
        process.result = null;
        process.error = error.message || 'Calculation failed.';
        renderProcessList();
        recalculateSummaries();
        renderSummaries();
        showStatus(process.error, 'error');
    }
}

function validateProcess(process) {
    if (!state.selectedMaterialId) {
        return 'Select a material before calculating a process.';
    }
    if (!process.featureId) {
        return 'Select a feature for this process.';
    }
    if (!process.operationId || !process.operationType) {
        return 'Select an operation for this process.';
    }

    const definitions = PROCESS_FIELD_DEFS[process.operationType] || [];
    for (const definition of definitions) {
        const rawValue = process.fields[definition.key];
        if (!definition.optional && (rawValue === undefined || rawValue === '')) {
            return `${definition.label} is required.`;
        }
        if (definition.type === 'number' && rawValue !== undefined && rawValue !== '') {
            if (toNumber(rawValue, NaN) <= 0) {
                return `${definition.label} must be greater than zero.`;
            }
        }
    }

    const initialDiameter = toNumber(process.fields.initial_diameter, NaN);
    const finalDiameter = toNumber(process.fields.final_diameter, NaN);

    if (process.operationType === 'turning' && !(initialDiameter > finalDiameter)) {
        return 'Turning requires the initial diameter to be larger than the final diameter.';
    }

    if (process.operationType === 'boring' && !(finalDiameter > initialDiameter)) {
        return 'Boring requires the final diameter to be larger than the initial diameter.';
    }

    if (process.operationType === 'turning') {
        const Di = initialDiameter;
        const Df = finalDiameter;
        const doc = toNumber(process.fields.depth_of_cut, NaN);

        if (!isNaN(Di) && !isNaN(Df) && !isNaN(doc)) {
            const radialReduction = (Di - Df) / 2;
            const passes = radialReduction / doc;

            if (passes > 10) {
                return 'Too many passes required. Consider increasing depth of cut.';
            }
        }
    }
    if (process.operationType === 'drilling') {
        const holeDepth = toNumber(process.fields.depth, NaN);
        const peckDepth = toNumber(process.fields.peck_depth, NaN);

        if (peckDepth >= holeDepth) {
            return 'Peck depth must be smaller than the total hole depth.';
        }
    }

    return '';
}

function buildCalculationPayload(process) {
    const dimensions = {};
    Object.entries(process.fields).forEach(([key, value]) => {
        if (value === '' || value === undefined) {
            return;
        }

        const definition = [...(PROCESS_FIELD_DEFS[process.operationType] || []), ...OVERRIDE_FIELDS]
            .find((fieldDef) => fieldDef.key === key);

        if (definition?.type === 'number') {
            dimensions[key] = toNumber(value);
        } else {
            dimensions[key] = value;
        }
    });

    return {
        material_id: Number(state.selectedMaterialId),
        operation_id: Number(process.operationId),
        operation_name: process.operationType,
        dimensions,
        feed: dimensions.feed,
        spindle_speed: dimensions.spindle_speed,
    };
}

async function persistCurrentJob() {
    if (!state.jobDraft.name.trim()) {
        showStatus('Job name is required before saving.', 'error');
        return;
    }

    if (!state.selectedMaterialId) {
        showStatus('Select a material before saving the job.', 'error');
        return;
    }

    try {
        let jobId = state.currentJobId;
        if (!jobId) {
            const createdJob = await fetchJson('/api/jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: state.jobDraft.name,
                    client_name: state.jobDraft.clientName,
                    description: state.jobDraft.description,
                }),
            });
            jobId = createdJob.id;
            state.currentJobId = jobId;
        }

        const time = state.summaries.time;
        const cost = state.summaries.cost;
        const payload = {
            name: state.jobDraft.name,
            client_name: state.jobDraft.clientName,
            description: state.jobDraft.description,
            material_id: Number(state.selectedMaterialId),
            total_time: time.totalTime,
            total_machining_time: time.machiningTime,
            total_setup_time: time.setupTime,
            total_tool_time: time.toolTime,
            total_idle_time: time.idleTime,
            total_misc_time: time.miscTime,
            total_cost: cost.finalCost,
            material_cost: cost.materialCost,
            machining_cost: cost.machiningCost,
            tooling_cost: cost.toolingCost,
            setup_idle_cost: cost.setupIdleCost,
            misc_cost: cost.miscCost,
            overhead_cost: cost.overheadCost,
            dimensions: {
                process_count: state.processes.length,
                source: 'lathe_workspace',
            },
            parts: [
                {
                    name: state.jobDraft.partName || 'Primary Part',
                    quantity: 1,
                    material_id: Number(state.selectedMaterialId),
                    operations: state.processes
                        .filter((process) => process.operationId)
                        .map((process, index) => ({
                            operation_id: Number(process.operationId),
                            sequence: index + 1,
                            machining_time: toNumber(process.result?.total_time_minutes),
                            machining_cost: toNumber(process.result?.cost),
                            tooling_cost: 0,
                            parameters: {
                                ...process.fields,
                                feature_id: process.featureId,
                                operation_name: process.operationName,
                                operation_type: process.operationType,
                            },
                        })),
                },
            ],
        };

        await fetchJson(`/api/jobs/${jobId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        await loadJobs();
        renderAll();
        showStatus(`Job ${state.jobDraft.name} saved successfully.`, 'success');
    } catch (error) {
        console.error(error);
        showStatus(error.message || 'Failed to save job.', 'error');
    }
}

async function duplicateJob(jobId) {
    if (!jobId) {
        showStatus('Open or save a job before duplicating it.', 'error');
        return;
    }

    try {
        const job = await fetchJson(`/api/jobs/${jobId}`);
        const duplicateName = buildDuplicateName(job.name || 'Copied Job');

        const createdJob = await fetchJson('/api/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: duplicateName,
                client_name: job.client_name,
                description: job.description,
            }),
        });

        await fetchJson(`/api/jobs/${createdJob.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...job,
                name: duplicateName,
                parts: job.parts || [],
            }),
        });

        await loadJobs();
        await loadJobIntoWorkspace(createdJob.id);
        showStatus(`Duplicated ${job.name} as ${duplicateName}.`, 'success');
    } catch (error) {
        console.error(error);
        showStatus(error.message || 'Failed to duplicate job.', 'error');
    }
}

async function loadJobIntoWorkspace(jobId) {
    try {
        const job = await fetchJson(`/api/jobs/${jobId}`);
        state.currentJobId = job.id;
        state.selectedMaterialId = job.material_id ? String(job.material_id) : '';
        state.jobDraft = {
            name: job.name || '',
            clientName: job.client_name || '',
            description: job.description || '',
            partName: job.parts?.[0]?.name || 'Primary Part',
        };

        state.processes = (job.parts?.[0]?.operations || []).map((operation, index) => ({
            id: `loaded-${job.id}-${index + 1}`,
            featureId: String(operation.parameters?.feature_id || ''),
            operationId: String(operation.operation_id || ''),
            operationName: operation.parameters?.operation_name || operation.operation_name || '',
            operationType: normalizeOperationName(operation.parameters?.operation_type || operation.operation_name || ''),
            fields: filterProcessFields(operation.parameters || {}),
            result: {
                total_time_minutes: toNumber(operation.machining_time),
                cost: toNumber(operation.machining_cost) + toNumber(operation.tooling_cost),
                warnings: [],
            },
            error: '',
        }));

        const featureLoads = state.processes
            .map((process) => process.featureId)
            .filter(Boolean)
            .map((featureId) => loadFeatureOperations(featureId));
        await Promise.all(featureLoads);

        recalculateSummaries();
        renderAll();
        showStatus(`Loaded job ${job.name}.`, 'success');
    } catch (error) {
        console.error(error);
        showStatus(error.message || 'Failed to load the selected job.', 'error');
    }
}

async function deleteJob(jobId) {
    try {
        await fetchJson(`/api/jobs/${jobId}`, { method: 'DELETE' });
        if (Number(jobId) === state.currentJobId) {
            resetWorkspace(false);
        }
        await loadJobs();
        renderJobsList();
        showStatus('Job deleted successfully.', 'success');
    } catch (error) {
        console.error(error);
        showStatus(error.message || 'Failed to delete job.', 'error');
    }
}

function resetWorkspace(showFeedback = true) {
    state.currentJobId = null;
    state.selectedMaterialId = '';
    state.jobDraft = {
        name: '',
        clientName: '',
        description: '',
        partName: 'Primary Part',
    };
    state.manualTimes = { setup: 0, tool: 0, idle: 0, misc: 0 };
    state.costInputs = { materialCost: 0, laborRatePerHour: 0, toolCostPerUse: 0, miscCost: 0 };
    state.processes = [];
    recalculateSummaries();
    renderAll();
    if (showFeedback) {
        showStatus('Workspace reset. You can start a fresh job now.', 'info');
    }
}

function renderCostChart(cost) {
    if (!dom.costChart || typeof window.Chart === 'undefined') {
        return;
    }

    const chartData = [
        toNumber(cost.machiningCost),
        toNumber(cost.setupIdleCost),
        toNumber(cost.toolingCost),
        toNumber(cost.overheadCost),
        toNumber(cost.materialCost),
        toNumber(cost.miscCost),
    ];

    if (state.charts.cost) {
        state.charts.cost.destroy();
    }

    state.charts.cost = new window.Chart(dom.costChart, {
        type: 'pie',
        data: {
            labels: ['Machining', 'Setup + Idle', 'Tooling', 'Overhead', 'Material', 'Misc'],
            datasets: [{
                data: chartData,
                backgroundColor: ['#1f6db7', '#f0a34a', '#7ab585', '#d96f62', '#6b4f9b', '#9aa5b1'],
                borderColor: '#ffffff',
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 14,
                    },
                },
            },
        },
    });
}

function buildDuplicateName(name) {
    if (!name) {
        return 'Copied Job';
    }
    if (/\(Copy \d+\)$/.test(name)) {
        const match = name.match(/\(Copy (\d+)\)$/);
        const next = Number(match?.[1] || 1) + 1;
        return name.replace(/\(Copy \d+\)$/, `(Copy ${next})`);
    }
    if (/\(Copy\)$/.test(name)) {
        return name.replace(/\(Copy\)$/, '(Copy 2)');
    }
    return `${name} (Copy)`;
}

function recalculateSummaries() {
    state.summaries.time = calculateTimeBreakdown({
        processes: state.processes,
        manualSetup: state.manualTimes.setup,
        manualTool: state.manualTimes.tool,
        manualIdle: state.manualTimes.idle,
        manualMisc: state.manualTimes.misc,
    });

    state.summaries.cost = calculateCostBreakdown({
        materialCost: state.costInputs.materialCost,
        laborRatePerHour: state.costInputs.laborRatePerHour,
        toolCostPerUse: state.costInputs.toolCostPerUse,
        miscCost: state.costInputs.miscCost,
        timeBreakdown: state.summaries.time,
        overheadRate: OVERHEAD_RATE,
    });
}

function exportPdf(reportType) {
    if (!state.currentJobId) {
        showStatus('Save the job before exporting a PDF.', 'error');
        return;
    }

    const url = reportType === 'shop'
        ? `/pdf/shop_floor/${state.currentJobId}`
        : `/pdf/customer/${state.currentJobId}`;
    window.open(url, '_blank');
}

function showStatus(message, type = 'info') {
    dom.statusBanner.textContent = message;
    dom.statusBanner.className = `status-banner status-${type}`;
}

function setText(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

function getOperationOptions(process) {
    const options = (process.featureId && state.featureOperations[process.featureId]) || [];
    const normalizedOptions = options.map((operation) => ({
        value: String(operation.operation_id),
        label: operation.operation_name,
    }));

    if (process.operationId && !normalizedOptions.some((option) => option.value === String(process.operationId))) {
        normalizedOptions.unshift({
            value: String(process.operationId),
            label: process.operationName || 'Current operation',
        });
    }

    return normalizedOptions;
}

function renderSelectField(processId, fieldKey, label, options, selectedValue, helpText) {
    const renderedOptions = ['<option value="">Select</option>']
        .concat(options.map((option) => `
            <option value="${escapeHtml(option.value)}" ${String(option.value) === String(selectedValue) ? 'selected' : ''}>
                ${escapeHtml(option.label)}
            </option>
        `))
        .join('');

    return `
        <label class="field-group">
            <span>${escapeHtml(label)} <span class="field-help" title="${escapeHtml(helpText)}">?</span></span>
            <select data-process-id="${processId}" data-field-key="${fieldKey}">
                ${renderedOptions}
            </select>
        </label>
    `;
}

function renderInputField(processId, definition, value) {
    if (definition.type === 'select') {
        return renderSelectField(processId, definition.key, definition.label, definition.options, value, definition.help);
    }

    return `
        <label class="field-group">
            <span>${escapeHtml(definition.label)} <span class="field-help" title="${escapeHtml(definition.help)}">?</span></span>
            <input
                type="${definition.type}"
                data-process-id="${processId}"
                data-field-key="${definition.key}"
                value="${escapeAttribute(value ?? '')}"
                ${definition.min !== undefined ? `min="${definition.min}"` : ''}
                ${definition.step !== undefined ? `step="${definition.step}"` : ''}
            >
        </label>
    `;
}

function field(key, label, type, help, options = {}) {
    return { key, label, type, help, ...options };
}

function findProcess(processId) {
    return state.processes.find((process) => process.id === processId);
}

function filterProcessFields(fields) {
    return Object.fromEntries(
        Object.entries(fields).filter(([key]) => (
            key !== 'feature_id' &&
            key !== 'operation_name' &&
            key !== 'operation_type'
        ))
    );
}

function normalizeOperationName(name) {
    return (name || '').trim().toLowerCase();
}

function toNumber(value, defaultValue = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : defaultValue;
}

function formatMinutes(value) {
    return `${toNumber(value).toFixed(2)} min`;
}

function formatCurrency(value) {
    return `INR ${toNumber(value).toFixed(2)}`;
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function escapeAttribute(value) {
    return escapeHtml(value).replace(/`/g, '&#96;');
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    let data = null;
    try {
        data = await response.json();
    } catch (_error) {
        data = null;
    }

    if (!response.ok) {
        throw new Error(data?.message || data?.error || `Request failed: ${response.status}`);
    }

    return data;
}
