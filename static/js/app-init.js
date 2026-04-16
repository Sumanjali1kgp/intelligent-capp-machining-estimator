// app-init.js - Initialize application modules and set up event listeners

// Import modules
Promise.all([
    import('/static/pdf-export.js'),
    import('/static/time.js'),
    import('/static/cost.js')
]).then(([pdfExport, time, cost]) => {
    // Make functions globally available
    window.exportToPDF = pdfExport.exportToPDF;
    window.calculateAndDisplayTimes = time.calculateAndDisplayTimes;
    window.calculateAndDisplayCosts = cost.calculateAndDisplayCosts;
    window.updateToolTime = time.updateToolTime;
    window.updateMiscTime = time.updateMiscTime;
    window.updateSetupTime = time.updateSetupTime;
    window.calculateOperationTime = time.calculateOperationTime;
    
    console.log('All modules loaded and initialized');
    
    // Set up event listeners for time inputs
    function setupTimeInputs() {
        const toolTimeInput = document.getElementById('toolTimeInput');
        const miscInput = document.getElementById('miscInput');
        const setupTimeInput = document.getElementById('setupTimeInput');
        
        if (toolTimeInput) {
            toolTimeInput.addEventListener('input', () => {
                time.updateToolTime();
                time.calculateAndDisplayTimes();
            });
        }
        
        if (miscInput) {
            miscInput.addEventListener('input', () => {
                time.updateMiscTime();
                time.calculateAndDisplayTimes();
            });
        }
        
        if (setupTimeInput) {
            setupTimeInput.addEventListener('input', () => {
                time.updateSetupTime();
                time.calculateAndDisplayTimes();
            });
        }
    }
    
    // Run setup when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupTimeInputs);
    } else {
        setupTimeInputs();
    }
}).catch(error => {
    console.error('Error loading modules:', error);
});
