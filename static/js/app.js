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
        
        if (addRowBtn) addRowBtn.addEventListener('click', addRow);
        if (clearTableBtn) clearTableBtn.addEventListener('click', clearTable);
        if (processBtn) processBtn.addEventListener('click', processAnalyses);
        if (downloadAllBtn) downloadAllBtn.addEventListener('click', downloadAll);
        if (clearLogsBtn) clearLogsBtn.addEventListener('click', clearLogs);
        if (toggleTerminalBtn) toggleTerminalBtn.addEventListener('click', toggleTerminal);
        
        // Iniciar polling de logs
        startLogsPolling();
        
        console.log('Aplicación inicializada correctamente');
    } catch (error) {
        console.error('Error al inicializar aplicación:', error);
    }
});

// Agregar fila a la tabla
function addRow() {
    const tbody = document.getElementById('tableBody');
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
        <td><input type="number" class="table-input" data-field="codigo_lab" placeholder="Ej: 10766" min="1"></td>
        <td>
            <select class="table-input" data-field="etapa">
                <option value="">Seleccione</option>
                <option value="CRECIMIENTO">CRECIMIENTO</option>
                <option value="ZOCA">ZOCA</option>
                <option value="PRODUCCION">PRODUCCION</option>
            </select>
        </td>
        <td><input type="number" class="table-input" data-field="edad" placeholder="0" min="0" max="1200"></td>
        <td><input type="number" class="table-input" data-field="densidad" placeholder="4444" min="2000" max="20000"></td>
        <td><input type="number" class="table-input" data-field="sombrio" placeholder="0" min="0" max="100"></td>
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
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Error al procesar');
        }

        currentJobId = result.job_id;
        document.getElementById('resultsSection').style.display = 'block';
        document.getElementById('resultsContainer').innerHTML = '';
        document.getElementById('downloadAllBtn').style.display = 'none';

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
            const response = await fetch(`/api/status/${jobId}`);
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

    const percentage = status.total > 0 ? (status.completed / status.total) * 100 : 0;
    progressFill.style.width = percentage + '%';
    progressFill.textContent = `${status.completed} / ${status.total}`;
    progressText.textContent = `Procesando: ${status.completed} de ${status.total} análisis completados`;

    // Mostrar resultados
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
    fetch(`/api/logs?since=${lastLogIndex}`)
        .then(response => response.json())
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

