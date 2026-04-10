/**
 * HealthGuard AI — Dashboard Logic
 *
 * Loads prediction stats, renders Chart.js pie chart,
 * and manages the paginated history table.
 */

// ─── State ──────────────────────────────────────────────────────
let currentPage = 1;
let totalPages = 1;
let searchQuery = '';
let diseaseChart = null;

// ─── Initialize ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadHistory();

    // Search
    const searchInput = document.getElementById('search-input');
    let debounceTimer;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            searchQuery = searchInput.value.trim();
            currentPage = 1;
            loadHistory();
        }, 400);
    });
});

// ─── Stats ──────────────────────────────────────────────────────
async function loadStats() {
    try {
        const res = await fetch('/api/history/stats');
        const data = await res.json();

        document.getElementById('stat-total').textContent = data.total_predictions;
        document.getElementById('stat-confidence').textContent =
            data.avg_confidence ? data.avg_confidence.toFixed(1) + '%' : '—';
        document.getElementById('stat-24h').textContent = data.recent_predictions;
        document.getElementById('stat-recent').textContent =
            `${data.recent_predictions} in last 24h`;

        if (data.top_diseases.length > 0) {
            document.getElementById('stat-top-disease').textContent =
                data.top_diseases[0].disease;
            document.getElementById('stat-top-count').textContent =
                `${data.top_diseases[0].count} predictions`;
        }

        renderDiseaseChart(data.top_diseases);
        renderTopDiseasesList(data.top_diseases);
    } catch (err) {
        console.error('Failed to load stats:', err);
        document.getElementById('stat-total').textContent = '0';
        document.getElementById('stat-confidence').textContent = '—';
        document.getElementById('stat-24h').textContent = '0';
    }
}

// ─── Chart ──────────────────────────────────────────────────────
function renderDiseaseChart(topDiseases) {
    const canvas = document.getElementById('disease-chart');
    if (!canvas || topDiseases.length === 0) {
        canvas.parentElement.innerHTML =
            '<div class="empty-state"><div class="empty-state-icon">📊</div><p>No data to chart yet</p></div>';
        return;
    }

    const colors = [
        '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
        '#ec4899', '#f43f5e', '#f97316', '#eab308',
        '#22c55e', '#06b6d4'
    ];

    if (diseaseChart) diseaseChart.destroy();

    diseaseChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: topDiseases.map(d => d.disease),
            datasets: [{
                data: topDiseases.map(d => d.count),
                backgroundColor: colors.slice(0, topDiseases.length),
                borderColor: 'rgba(6, 7, 13, 0.8)',
                borderWidth: 2,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 11 },
                        padding: 12,
                        usePointStyle: true,
                        pointStyleWidth: 8,
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(13, 15, 26, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(255,255,255,0.08)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 10,
                }
            }
        }
    });
}

function renderTopDiseasesList(topDiseases) {
    const container = document.getElementById('top-diseases-list');
    if (topDiseases.length === 0) return;

    const total = topDiseases.reduce((s, d) => s + d.count, 0);

    container.innerHTML = topDiseases.slice(0, 8).map((d, i) => {
        const pct = ((d.count / total) * 100).toFixed(1);
        const colors = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
            '#ec4899', '#f43f5e', '#f97316', '#eab308'];
        return `
            <div class="prediction-row" style="padding: 0.6rem 0;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: ${colors[i]}; flex-shrink: 0;"></div>
                    <span class="prediction-row-name">${d.disease}</span>
                </div>
                <span class="prediction-row-conf" style="color: ${colors[i]};">${d.count} (${pct}%)</span>
            </div>
        `;
    }).join('');
}

// ─── History ────────────────────────────────────────────────────
async function loadHistory() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            limit: 15,
            search: searchQuery,
        });
        const res = await fetch(`/api/history?${params}`);
        const data = await res.json();

        totalPages = data.total_pages || 1;
        renderHistoryTable(data.predictions);
        renderPagination();
    } catch (err) {
        console.error('Failed to load history:', err);
        document.getElementById('history-tbody').innerHTML =
            '<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 2rem;">Could not load history</td></tr>';
    }
}

function renderHistoryTable(predictions) {
    const tbody = document.getElementById('history-tbody');

    if (predictions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    ${searchQuery ? 'No results matching "' + searchQuery + '"' : 'No predictions yet. Use the chatbot to make predictions!'}
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = predictions.map(p => {
        const confClass = p.confidence >= 70 ? 'conf-high' :
                          p.confidence >= 40 ? 'conf-medium' : 'conf-low';
        const symptoms = (p.symptoms || [])
            .slice(0, 3)
            .map(s => s.replace(/_/g, ' '))
            .join(', ');
        const extra = (p.symptoms || []).length > 3 ? ` +${p.symptoms.length - 3}` : '';
        const date = new Date(p.timestamp).toLocaleDateString('en-US', {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });

        return `
            <tr>
                <td style="color: var(--text-primary); font-weight: 500;">${p.disease}</td>
                <td><span class="conf-badge ${confClass}">${p.confidence.toFixed(1)}%</span></td>
                <td>${symptoms}${extra ? `<span style="color: var(--text-muted);">${extra}</span>` : ''}</td>
                <td style="color: var(--text-muted);">${date}</td>
            </tr>`;
    }).join('');
}

function renderPagination() {
    const container = document.getElementById('pagination');
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = `<button class="page-btn" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>← Prev</button>`;

    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || Math.abs(i - currentPage) <= 1) {
            html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
        } else if (Math.abs(i - currentPage) === 2) {
            html += `<span style="color: var(--text-muted);">…</span>`;
        }
    }

    html += `<button class="page-btn" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next →</button>`;
    container.innerHTML = html;
}

function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadHistory();
}
