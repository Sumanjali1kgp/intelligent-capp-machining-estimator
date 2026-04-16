// jsPDF and autoTable are loaded globally in lathe.html

const PDF_TERMS = `Terms & Conditions:
1. This is a computer-generated estimate and valid for 30 days.
2. Prices may vary based on raw material availability and market conditions.
3. Delivery timeline is estimated and subject to workshop schedule.
4. Final dimensions and specifications must be confirmed before production.`;

// Format date as DD/MM/YY
function formatDate(date = new Date()) {
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = String(d.getFullYear()).slice(-2);
    return `${day}/${month}/${year}`;
}

/**
 * Prompt customer details before generating PDF
 */
function getCustomerDetails() {
    const name = prompt("Enter Customer Name:");
    const project = prompt("Enter Project Name / Description:");
    const orderId = `ORD-${Date.now()}`;
    return { name: name || 'N/A', project: project || 'N/A', orderId };
}

// Make exportToPDF available globally
window.exportToPDF = async function(type = 'customer') {
    const { jsPDF } = window.jspdf.jsPDF ? window.jspdf : { jsPDF: window.jspdf };
    if (!jsPDF) {
        alert("PDF library not loaded.");
        return;
    }

    const doc = new jsPDF();
    const date = formatDate();
    const title = type === 'shop' 
        ? 'CWISS - Workshop Operation Sheet' 
        : 'CWISS - Quotation for Machining Services';

    // Get customer details for customer PDF
    const customerDetails = type === 'customer' ? getCustomerDetails() : null;
    
    // Get all cost values from the page
    const getNumericValue = (id) => {
        const el = document.getElementById(id);
        return el ? parseFloat(el.textContent.replace(/[^0-9.-]+/g, '')) || 0 : 0;
    };

    // Get time values
    const machiningTime = document.getElementById('machiningTime')?.textContent || '0.00';
    const setupTime = document.getElementById('setupTime')?.textContent || '0.00';
    const idleTime = document.getElementById('idleTime')?.textContent || '0.00';
    const totalTime = document.getElementById('totalTime')?.textContent || '0.00';

    // Get cost values
    const materialCost = getNumericValue('materialCost');
    const laborCost = getNumericValue('laborCost');
    const machineCost = getNumericValue('machineCost');
    const toolingCost = getNumericValue('toolingCost');
    const setupIdleCost = getNumericValue('setupIdleCost');
    const overheadCost = getNumericValue('overheadCost');
    const finalCost = document.getElementById('finalCost')?.textContent || '₹0.00';
    
    // Calculate non-productive cost (material + setup & idle)
    const nonProductiveCost = materialCost + setupIdleCost;

    // Header with logo and title
    doc.setFontSize(20);
    doc.setTextColor(0, 0, 0);
    doc.setFont('helvetica', 'bold');
    doc.text('CWISS', 20, 20);
    
    doc.setFontSize(14);
    doc.setTextColor(100);
    doc.setFont('helvetica', 'normal');
    doc.text('Central Workshop & Instrument Service Section', 20, 28);
    doc.text('Indian Institute of Technology Kharagpur', 20, 34);
    
    // Document title and date
    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.text(title, 105, 20, { align: 'center' });
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(`Date: ${date}`, 190, 20, { align: 'right' });
    doc.text(`Quotation #: ${customerDetails?.orderId || 'N/A'}`, 190, 25, { align: 'right' });

    // Customer details for customer PDF
    if (type === 'customer' && customerDetails) {
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.text('Customer Details', 20, 55);
        doc.setFont('helvetica', 'normal');
        doc.text(`Name: ${customerDetails.name}`, 20, 62);
        doc.text(`Project: ${customerDetails.project}`, 20, 69);
    }

    // Add content based on PDF type
    if (type === 'customer') {
        let currentY = customerDetails ? 85 : 60;
        
        // Add material information
        const materialSelect = document.getElementById('materialSelect');
        const selectedMaterial = materialSelect ? materialSelect.options[materialSelect.selectedIndex]?.text : 'Not Specified';
        
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('Material:', 20, currentY);
        doc.setFont('helvetica', 'normal');
        doc.text(selectedMaterial, 50, currentY);
        currentY += 10;
        
        // Add operations list
        const operationEntries = Array.from(document.querySelectorAll('.operation-entry'));
        if (operationEntries.length > 0) {
            doc.setFontSize(12);
            doc.setFont('helvetica', 'bold');
            doc.text('Operations:', 20, currentY);
            currentY += 8;
            
            doc.setFont('helvetica', 'normal');
            operationEntries.forEach((entry, index) => {
                const operationName = entry.querySelector('.operation-title')?.textContent || `Operation ${index + 1}`;
                const timeInput = entry.querySelector('input[type="text"][readonly]');
                const time = timeInput ? timeInput.value + ' min' : '';
                
                doc.text(`• ${operationName} ${time}`, 25, currentY);
                currentY += 6;
                
                // Add some space after each operation
                if (index < operationEntries.length - 1) {
                    currentY += 2;
                }
            });
            
            currentY += 10; // Extra space before cost table
        }
        
        // Cost summary for customer
        doc.autoTable({
            startY: currentY,
            head: [
                [
                    { content: 'DESCRIPTION', styles: { fontStyle: 'bold', textColor: [255, 255, 255], fillColor: [0, 51, 102] }},
                    { content: 'AMOUNT (₹)', styles: { fontStyle: 'bold', textColor: [255, 255, 255], fillColor: [0, 51, 102], halign: 'right' }}
                ]
            ],
            body: [
                [
                    { content: 'Material & Setup', styles: { fontStyle: 'bold' }},
                    { content: `₹${nonProductiveCost.toFixed(2)}`, styles: { halign: 'right' }}
                ],
                [
                    { content: 'Machining', styles: { fontStyle: 'bold' }},
                    { content: `₹${machineCost.toFixed(2)}`, styles: { halign: 'right' }}
                ],
                [
                    { content: 'Tooling', styles: { fontStyle: 'bold' }},
                    { content: `₹${toolingCost.toFixed(2)}`, styles: { halign: 'right' }}
                ],
                [
                    { content: 'Overhead (40%)', styles: { fontStyle: 'bold' }},
                    { content: `₹${overheadCost.toFixed(2)}`, styles: { halign: 'right' }}
                ],
                [
                    { content: 'TOTAL ESTIMATED COST', styles: { fontStyle: 'bold' }},
                    { content: finalCost, styles: { fontStyle: 'bold', halign: 'right' }}
                ]
            ],
            theme: 'grid',
            headStyles: { 
                fillColor: [0, 51, 102],
                textColor: [255, 255, 255],
                fontStyle: 'bold',
                halign: 'left'
            },
            columnStyles: {
                0: { cellWidth: 'auto' },
                1: { cellWidth: 50, halign: 'right' }
            },
            styles: { 
                fontSize: 11,
                cellPadding: 4,
                lineWidth: 0.5,
                cellPadding: 5
            },
            margin: { top: 10 }
        });

        // Add terms and conditions
        doc.setFontSize(9);
        doc.setFont('helvetica', 'bold');
        doc.text('Terms & Conditions:', 14, doc.lastAutoTable.finalY + 15);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        const splitTerms = doc.splitTextToSize(PDF_TERMS, 180);
        doc.text(splitTerms, 20, doc.lastAutoTable.finalY + 20);
        
        // Add footer
        doc.setFontSize(8);
        doc.setTextColor(100);
        doc.text('Thank you for choosing CWISS - IIT Kharagpur', 105, 280, { align: 'center' });

    } else if (type === 'shop') {
        // Get all operation entries
        const operationEntries = Array.from(document.querySelectorAll('.operation-entry'));
        
        // Helper function to format parameter label
        const formatLabel = (label) => {
            if (!label) return '';
            // Remove units in parentheses and trim
            return label.replace(/\([^)]*\)/g, '').trim();
        };

        // Prepare operations data for the table
        const operationsData = [];
        
        operationEntries.forEach((entry, index) => {
            const operationName = entry.querySelector('.operation-title')?.textContent || `Operation ${index + 1}`;
            const timeInput = entry.querySelector('input[type="text"][readonly]');
            const time = timeInput ? parseFloat(timeInput.value).toFixed(2) + ' min' : 'N/A';
            
            // Get all input groups and their labels
            const paramGroups = [];
            const formGroups = entry.querySelectorAll('.form-group:not(.time-group)');
            
            formGroups.forEach(group => {
                const label = group.querySelector('label');
                const input = group.querySelector('input:not([type="hidden"])');
                
                if (input && input.value && label?.textContent) {
                    const paramName = formatLabel(label.textContent);
                    const unitMatch = label.textContent.match(/\(([^)]+)\)/);
                    const unit = unitMatch ? unitMatch[1] : '';
                    
                    paramGroups.push({
                        name: paramName,
                        value: input.value,
                        unit: unit
                    });
                }
            });
            
            // Format parameters for display
            const params = [];
            paramGroups.forEach(param => {
                if (param.unit) {
                    params.push(`${param.name} = ${param.value} ${param.unit}`);
                } else {
                    params.push(`${param.name} = ${param.value}`);
                }
            });
            
            operationsData.push({
                name: operationName,
                time: time,
                params: params,
                rawParams: paramGroups
            });
        });

        // Operations table
        doc.setFontSize(14);
        doc.setTextColor(0, 0, 0);
        doc.setFont('helvetica', 'bold');
        doc.text('Operations Summary', 14, 50);

        // Operations details table
        doc.autoTable({
            startY: 60,
            head: [
                [
                    { content: 'Operation', styles: { fontStyle: 'bold', textColor: [255, 255, 255], fillColor: [0, 51, 102] }},
                    { content: 'Parameters', styles: { fontStyle: 'bold', textColor: [255, 255, 255], fillColor: [0, 51, 102] }},
                    { content: 'Time (min)', styles: { fontStyle: 'bold', textColor: [255, 255, 255], fillColor: [0, 51, 102], halign: 'center' }}
                ]
            ],
            body: operationsData.flatMap((op, idx) => {
                // First row: Operation name and time
                const rows = [
                    [
                        { content: op.name, styles: { fontStyle: 'bold', fillColor: [240, 240, 240] }},
                        { content: op.params[0] || 'No parameters', styles: { fontSize: 9, fillColor: [255, 255, 255] }},
                        { content: op.time, styles: { halign: 'center', fillColor: [240, 240, 240] }}
                    ]
                ];
                
                // Additional rows for remaining parameters
                for (let i = 1; i < op.params.length; i++) {
                    rows.push([
                        { content: '', styles: { fillColor: [255, 255, 255] }},
                        { content: op.params[i], styles: { fontSize: 9, fillColor: [255, 255, 255] }},
                        { content: '', styles: { fillColor: [255, 255, 255] }}
                    ]);
                }
                
                // Add a small gap after each operation
                if (idx < operationsData.length - 1) {
                    rows.push([
                        { content: '', border: [false, false, false, false] },
                        { content: '', border: [false, false, false, false] },
                        { content: '', border: [false, false, false, false] }
                    ]);
                }
                
                return rows;
            }),
            theme: 'grid',
            styles: { 
                fontSize: 9,
                cellPadding: 3,
                lineWidth: 0.2,
                overflow: 'linebreak',
                cellWidth: 'wrap',
                lineColor: [220, 220, 220]
            },
            columnStyles: {
                0: { cellWidth: 45, minCellHeight: 10, cellPadding: { top: 2, right: 2, bottom: 2, left: 2 } },
                1: { cellWidth: 'auto', minCellHeight: 10, cellPadding: { top: 2, right: 2, bottom: 2, left: 4 } },
                2: { cellWidth: 25, halign: 'center', minCellHeight: 10, cellPadding: { top: 2, right: 2, bottom: 2, left: 2 } }
            },
            headStyles: {
                fillColor: [0, 51, 102],
                textColor: [255, 255, 255],
                fontStyle: 'bold',
                lineWidth: 0.3
            },
            alternateRowStyles: {
                fillColor: [248, 248, 248]
            }
        });

        // Time summary table
        doc.autoTable({
            startY: doc.lastAutoTable.finalY + 10,
            head: [
                [
                    { content: 'Time Summary', colSpan: 2, styles: { 
                        fontStyle: 'bold', 
                        textColor: [255, 255, 255], 
                        fillColor: [0, 51, 102],
                        halign: 'center'
                    }}
                ],
                [
                    { content: 'Component', styles: { fontStyle: 'bold', textColor: [255, 255, 255], fillColor: [0, 51, 102] }},
                    { content: 'Minutes', styles: { fontStyle: 'bold', textColor: [255, 255, 255], fillColor: [0, 51, 102], halign: 'center' }}
                ]
            ],
            body: [
                ['Machining Time', { content: machiningTime, styles: { halign: 'center' }}],
                ['Setup Time', { content: setupTime, styles: { halign: 'center' }}],
                ['Idle Time', { content: idleTime, styles: { halign: 'center' }}],
                [
                    { content: 'Total Time', styles: { 
                        fontStyle: 'bold',
                        fillColor: [240, 240, 240]
                    }}, 
                    { 
                        content: totalTime, 
                        styles: { 
                            fontStyle: 'bold', 
                            halign: 'center',
                            fillColor: [240, 240, 240]
                        }
                    }
                ]
            ],
            theme: 'grid',
            styles: { 
                fontSize: 10,
                cellPadding: 3,
                lineWidth: 0.3,
                lineColor: [220, 220, 220]
            },
            columnStyles: {
                0: { cellWidth: 'auto', cellPadding: { left: 8, top: 3, right: 3, bottom: 3 } },
                1: { cellWidth: 40, halign: 'center', cellPadding: { left: 3, top: 3, right: 8, bottom: 3 } }
            },
            headStyles: {
                fillColor: [0, 51, 102],
                textColor: [255, 255, 255],
                fontStyle: 'bold',
                lineWidth: 0.3
            }
        });

        // Cost details for shop
        doc.autoTable({
            startY: doc.lastAutoTable.finalY + 10,
            head: [['Cost Component', 'Amount (₹)']],
            body: [
                ['Material Cost', materialCost],
                ['Labor Cost', laborCost],
                ['Machine Cost', machineCost],
                ['Overhead', overheadCost],
                [{ content: 'Total Cost', styles: { fontStyle: 'bold' }}, 
                 { content: finalCost, styles: { fontStyle: 'bold' }}]
            ],
            theme: 'grid',
            headStyles: { fillColor: [41, 128, 185] },
            styles: { fontSize: 10 }
        });
    }

    // Save the PDF with a professional filename
    const formattedDate = new Date().toISOString().split('T')[0].replace(/-/g, '');
    const fileName = type === 'customer' 
        ? `CWISS_Quote_${customerDetails?.orderId || formattedDate}.pdf`
        : `CWISS_Worksheet_${formattedDate}.pdf`;
    
    doc.save(fileName);
}
