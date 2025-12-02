// Lógica de la aplicación web
console.log('app.js cargado correctamente');

let currentJobId = null;
let statusInterval = null;
let logsInterval = null;
let lastLogIndex = 0;
let terminalMinimized = false;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    try {
        const addRowBtn = document.getElementById('addRow');
        const clearTableBtn = document.getElementById('clearTable');
        const processBtn = document.getElementById('processBtn');
        const downloadAllBtn = document.getElementById('downloadAllBtn');
        const clearLogsBtn = document.getElementById('clearLogsBtn');
        const toggleTerminalBtn = document.getElementById('toggleTerminalBtn');
        
        // Modal elements
        const pasteExcelBtn = document.getElementById('pasteExcelBtn');
        const pasteModal = document.getElementById('pasteModal');
        const closePasteModalBtn = document.querySelector('.close-modal');
        const cancelPasteBtn = document.getElementById('cancelPasteBtn');
        const importExcelBtn = document.getElementById('importExcelBtn');
        
        if (addRowBtn) addRowBtn.addEventListener('click', () => addRow());
        if (clearTableBtn) clearTableBtn.addEventListener('click', clearTable);
        if (processBtn) processBtn.addEventListener('click', processAnalyses);
        if (downloadAllBtn) downloadAllBtn.addEventListener('click', downloadAll);
        if (clearLogsBtn) clearLogsBtn.addEventListener('click', clearLogs);
        if (toggleTerminalBtn) toggleTerminalBtn.addEventListener('click', toggleTerminal);
        
        // Modal listeners
        if (pasteExcelBtn) pasteExcelBtn.addEventListener('click', openPasteModal);
        if (closePasteModalBtn) closePasteModalBtn.addEventListener('click', closePasteModal);
        if (cancelPasteBtn) cancelPasteBtn.addEventListener('click', closePasteModal);
        if (importExcelBtn) importExcelBtn.addEventListener('click', importExcelData);
        if (pasteModal) {
            window.addEventListener('click', (e) => {
                if (e.target === pasteModal) closePasteModal();
            });
        }
        
        // Iniciar polling de logs
        startLogsPolling();
        
        console.log('Aplicación inicializada correctamente');
    } catch (error) {
        console.error('Error al inicializar aplicación:', error);
    }
});

// Agregar fila a la tabla
function addRow(data = null) {
    const tbody = document.getElementById('tableBody');
    const newRow = document.createElement('tr');
    
    const codigo_lab = data ? data.codigo_lab : '';
    const etapa = data ? data.etapa : '';
    const edad = data ? data.edad : '';
    const densidad = data ? data.densidad : '';
    const sombrio = data ? data.sombrio : '';

    // Helper para seleccionar opción
    const isSelected = (val, option) => val === option ? 'selected' : '';

    newRow.innerHTML = `
        <td><input type="number" class="table-input" data-field="codigo_lab" placeholder="Ej: 10766" min="1" value="${codigo_lab}"></td>
        <td>
            <select class="table-input" data-field="etapa">
                <option value="">Seleccione</option>
                <option value="CRECIMIENTO" ${isSelected(etapa, 'CRECIMIENTO')}>CRECIMIENTO</option>
                <option value="ZOCA" ${isSelected(etapa, 'ZOCA')}>ZOCA</option>
                <option value="PRODUCCION" ${isSelected(etapa, 'PRODUCCION')}>PRODUCCION</option>
            </select>
        </td>
        <td><input type="number" class="table-input" data-field="edad" placeholder="0" min="0" max="1200" value="${edad}"></td>
        <td><input type="number" class="table-input" data-field="densidad" placeholder="4444" min="2000" max="20000" value="${densidad}"></td>
        <td><input type="number" class="table-input" data-field="sombrio" placeholder="0" min="0" max="100" value="${sombrio}"></td>
        <td><button type="button" class="btn-remove" onclick="removeRow(this)">×</button></td>
    `;
    tbody.appendChild(newRow);
}

// Remover fila
function removeRow(button) {
    const tbody = document.getElementById('tableBody');
    if (tbody.children.length > 1) {
        button.closest('tr').remove();
    } else {
        alert('Debe haber al menos una fila en la tabla');
    }
}

// Limpiar tabla
function clearTable() {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';
    addRow(); // Agregar una fila vacía
}

// Validar datos antes de procesar
function validateData() {
    const year = document.getElementById('year').value;
    if (!year) {
        alert('Por favor seleccione el año del análisis');
        return false;
    }

    const rows = document.querySelectorAll('#tableBody tr');
    const analyses = [];

    for (let row of rows) {
        const codigo_lab = row.querySelector('[data-field="codigo_lab"]').value;
        const etapa = row.querySelector('[data-field="etapa"]').value;
        const edad = row.querySelector('[data-field="edad"]').value;
        const densidad = row.querySelector('[data-field="densidad"]').value;
        const sombrio = row.querySelector('[data-field="sombrio"]').value;

        // Validar que todos los campos estén llenos
        if (!codigo_lab || !etapa || edad === '' || densidad === '' || sombrio === '') {
            alert('Por favor complete todos los campos en todas las filas');
            return false;
        }

        // Validar valores numéricos
        if (isNaN(edad) || isNaN(densidad) || isNaN(sombrio)) {
            alert('Los campos numéricos deben contener solo números');
            return false;
        }

        analyses.push({
            codigo_lab: parseInt(codigo_lab),
            etapa: etapa,
            edad: parseInt(edad),
            densidad: parseInt(densidad),
            sombrio: parseInt(sombrio)
        });
    }

    if (analyses.length === 0) {
        alert('Debe agregar al menos un análisis');
        return false;
    }

    return { year: parseInt(year), analyses: analyses };
}

// Procesar análisis
async function processAnalyses() {
    const data = validateData();
    if (!data) return;

    // Deshabilitar botón
    const processBtn = document.getElementById('processBtn');
    processBtn.disabled = true;
    processBtn.textContent = 'Procesando...';

    try {
        // Crear AbortController para timeout de 20 segundos adicionales
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 20000); // 20 segundos adicionales
        
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Error al procesar');
        }

        currentJobId = result.job_id;
        // Mostrar sección de resultados
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'block';
            resultsSection.classList.add('show');
        }
        
        // Limpiar contenedor de resultados
        const resultsContainer = document.getElementById('resultsContainer');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
        }
        
        // Ocultar botón de descarga masiva inicialmente
        const downloadAllBtn = document.getElementById('downloadAllBtn');
        if (downloadAllBtn) {
            downloadAllBtn.style.display = 'none';
        }

        // Iniciar polling de estado
        startStatusPolling(currentJobId);

    } catch (error) {
        alert('Error: ' + error.message);
        processBtn.disabled = false;
        processBtn.textContent = 'Procesar Análisis';
    }
}

// Polling de estado
function startStatusPolling(jobId) {
    if (statusInterval) {
        clearInterval(statusInterval);
    }

    statusInterval = setInterval(async () => {
        try {
            // Timeout aumentado para peticiones de estado
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 20000); // 20 segundos adicionales
            
            const response = await fetch(`/api/status/${jobId}`, {
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            const status = await response.json();

            updateProgress(status);

            if (status.status === 'completed') {
                clearInterval(statusInterval);
                document.getElementById('processBtn').disabled = false;
                document.getElementById('processBtn').textContent = 'Procesar Análisis';
                document.getElementById('downloadAllBtn').style.display = 'inline-block';
            }
        } catch (error) {
            console.error('Error al obtener estado:', error);
        }
    }, 2000); // Poll cada 2 segundos
}

// Actualizar progreso
function updateProgress(status) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const resultsContainer = document.getElementById('resultsContainer');
    const resultsSection = document.getElementById('resultsSection');

    if (!resultsContainer || !progressFill || !progressText) {
        console.error('Elementos de resultados no encontrados');
        return;
    }

    // Asegurar que la sección de resultados esté visible
    if (resultsSection) {
        resultsSection.style.display = 'block';
        resultsSection.classList.add('show');
    }

    const percentage = status.total > 0 ? (status.completed / status.total) * 100 : 0;
    if (progressFill) {
        progressFill.style.width = percentage + '%';
        progressFill.textContent = `${status.completed} / ${status.total}`;
    }
    if (progressText) {
        progressText.textContent = `Procesando: ${status.completed} de ${status.total} análisis completados`;
    }

    // Mostrar resultados individuales
    if (status.results && status.results.length > 0) {
        resultsContainer.innerHTML = '';
        status.results.forEach(result => {
            const resultDiv = document.createElement('div');
            resultDiv.className = `result-item ${result.status}`;
            
            if (result.status === 'success') {
                resultDiv.innerHTML = `
                    <div>
                        <strong>Código Lab ${result.codigo_lab}:</strong> ${result.message}
                    </div>
                    <a href="/api/download/${result.filename}" class="download-link" download>Descargar PDF</a>
                `;
            } else {
                resultDiv.innerHTML = `
                    <div>
                        <strong>Código Lab ${result.codigo_lab}:</strong> ${result.message}
                    </div>
                `;
            }
            
            resultsContainer.appendChild(resultDiv);
        });
    } else {
        // Mostrar mensaje si no hay resultados aún
        resultsContainer.innerHTML = '<div class="terminal-line log-level-info">Esperando resultados...</div>';
    }
}

// Descargar todos los PDFs
function downloadAll() {
    if (!currentJobId) return;
    window.location.href = `/api/download-all/${currentJobId}`;
}

// Terminal de logs
function startLogsPolling() {
    if (logsInterval) {
        clearInterval(logsInterval);
    }
    
    // Obtener logs cada segundo
    logsInterval = setInterval(fetchLogs, 1000);
    // Obtener logs inmediatamente
    fetchLogs();
}

function fetchLogs() {
    // Timeout aumentado para peticiones de logs
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000); // 20 segundos adicionales
    
    fetch(`/api/logs?since=${lastLogIndex}`, {
        signal: controller.signal
    })
        .then(response => {
            clearTimeout(timeoutId);
            return response.json();
        })
        .then(data => {
            if (data.logs && data.logs.length > 0) {
                appendLogs(data.logs);
                lastLogIndex = data.next_index;
                // Auto-scroll al final si no está minimizado
                if (!terminalMinimized) {
                    scrollTerminalToBottom();
                }
            }
        })
        .catch(error => {
            console.error('Error al obtener logs:', error);
        });
}

function appendLogs(logs) {
    const terminalContent = document.getElementById('terminalContent');
    
    logs.forEach(log => {
        const line = document.createElement('div');
        line.className = `terminal-line ${log.level.toLowerCase()}`;
        
        const timestamp = document.createElement('span');
        timestamp.className = 'terminal-timestamp';
        timestamp.textContent = log.timestamp;
        
        const level = document.createElement('span');
        level.className = `terminal-level ${log.level}`;
        level.textContent = `[${log.level}]`;
        
        const message = document.createElement('span');
        message.textContent = log.message.replace(log.timestamp, '').replace(`- ${log.level} -`, '').trim();
        
        line.appendChild(timestamp);
        line.appendChild(level);
        line.appendChild(message);
        
        terminalContent.appendChild(line);
        
        // Limitar número de líneas visibles (mantener últimas 500)
        const lines = terminalContent.querySelectorAll('.terminal-line');
        if (lines.length > 500) {
            lines[0].remove();
        }
    });
}

function scrollTerminalToBottom() {
    const terminalContainer = document.getElementById('terminalContainer');
    terminalContainer.scrollTop = terminalContainer.scrollHeight;
}

function clearLogs() {
    if (confirm('¿Desea limpiar los logs de la terminal?')) {
        fetch('/api/logs/clear', { method: 'POST' })
            .then(() => {
                const terminalContent = document.getElementById('terminalContent');
                terminalContent.innerHTML = '<div class="terminal-line info">Logs limpiados.</div>';
                lastLogIndex = 0;
            })
            .catch(error => {
                console.error('Error al limpiar logs:', error);
            });
    }
}

function toggleTerminal() {
    const terminalContainer = document.getElementById('terminalContainer');
    const toggleBtn = document.getElementById('toggleTerminalBtn');
    
    terminalMinimized = !terminalMinimized;
    
    if (terminalMinimized) {
        terminalContainer.classList.add('terminal-minimized');
        toggleBtn.textContent = 'Maximizar';
    } else {
        terminalContainer.classList.remove('terminal-minimized');
        toggleBtn.textContent = 'Minimizar';
        scrollTerminalToBottom();
    }
}

// Funciones para el modal de Excel
function openPasteModal() {
    const modal = document.getElementById('pasteModal');
    if (modal) {
        modal.style.display = 'block';
        document.getElementById('excelPasteArea').value = '';
        document.getElementById('excelPasteArea').focus();
    }
}

function closePasteModal() {
    const modal = document.getElementById('pasteModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function importExcelData() {
    const text = document.getElementById('excelPasteArea').value;
    if (!text.trim()) {
        alert('Por favor pegue los datos primero');
        return;
    }

    const lines = text.split(/\r?\n/);
    let importedCount = 0;
    const tbody = document.getElementById('tableBody');
    
    // Si la tabla tiene solo una fila vacía, limpiarla
    const rows = tbody.querySelectorAll('tr');
    if (rows.length === 1) {
        const firstRowInputs = rows[0].querySelectorAll('input');
        let isEmpty = true;
        firstRowInputs.forEach(input => {
            if (input.value) isEmpty = false;
        });
        if (isEmpty) tbody.innerHTML = '';
    }

    lines.forEach(line => {
        if (!line.trim()) return;
        
        const columns = line.split('\t');
        
        // Verificar si es una línea de encabezado (si la primera columna no es número)
        if (isNaN(parseInt(columns[0]))) {
            return; // Saltar encabezado
        }

        // Esperamos al menos 5 columnas: No. Lab, ETAPA, EDAD, DENSIDAD, SOMBRIO
        if (columns.length >= 5) {
            const data = {
                codigo_lab: columns[0].trim(),
                etapa: columns[1].trim().toUpperCase(),
                edad: columns[2].trim(),
                densidad: columns[3].trim(),
                sombrio: columns[4].trim()
            };
            
            // Normalizar etapa si viene como número o texto diferente
            // El select espera: CRECIMIENTO, ZOCA, PRODUCCION
            // Mapeo básico si es necesario, aunque el ejemplo muestra texto exacto
            
            addRow(data);
            importedCount++;
        }
    });

    if (importedCount > 0) {
        closePasteModal();
        // alert(`Se importaron ${importedCount} filas correctamente.`);
    } else {
        alert('No se pudieron importar datos. Verifique el formato (copie y pegue desde Excel).');
    }
}

