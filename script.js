// Haal data van de Worker API
const API_URL = 'https://baakie-dashboard.a-verboon.workers.dev/api/spaces';

async function loadData() {
    const table = document.getElementById('tableContainer');
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error('HTTP error! status: ' + response.status);
        const data = await response.json();
        
        document.getElementById('timestamp').textContent = 'Laatste update: ' + new Date().toLocaleString('nl-NL');
        
        let total = 0, online = 0, degraded = 0, offline = 0;
        let html = '<table><thead><tr><th>Space</th><th>Status</th><th>Response</th></tr></thead><tbody>';
        
        for (const [name, info] of Object.entries(data)) {
            total++;
            const status = info.status || 'unknown';
            if (status === 'online') online++;
            else if (status === 'degraded') degraded++;
            else offline++;
            
            const dotClass = status === 'online' ? 'online' : status === 'degraded' ? 'degraded' : 'offline';
            const responseTime = info.response_time ? info.response_time + 'ms' : '-';
            
            html += '<tr>' +
                '<td><strong>' + name + '</strong></td>' +
                '<td><span class="badge ' + status + '"><span class="status-dot ' + dotClass + '"></span>' + status + '</span></td>' +
                '<td>' + responseTime + '</td>' +
            '</tr>';
        }
        html += '</tbody></table>';
        
        document.getElementById('total').textContent = total;
        document.getElementById('online').textContent = online;
        document.getElementById('degraded').textContent = degraded;
        document.getElementById('offline').textContent = offline;
        table.innerHTML = html;
    } catch (error) {
        table.innerHTML = '<div class="error">❌ Fout bij laden: ' + error.message + '</div>';
    }
}

loadData();
setInterval(loadData, 30000);
