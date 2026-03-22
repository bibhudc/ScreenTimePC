/* ── Category color mapping ──────────────────────────────── */
const CATEGORY_COLORS = {
    'Gaming':          '#e74c3c',
    'Homework/School': '#2ecc71',
    'Social Media':    '#e67e22',
    'Video/Streaming': '#9b59b6',
    'Productivity':    '#3498db',
    'Other':           '#95a5a6',
    'Idle':            '#636e72',
};

function getCategoryColor(cat) {
    return CATEGORY_COLORS[cat] || '#95a5a6';
}

function getCategoryClass(cat) {
    const map = {
        'Gaming': 'cat-gaming',
        'Homework/School': 'cat-homework',
        'Social Media': 'cat-social',
        'Video/Streaming': 'cat-video',
        'Productivity': 'cat-productivity',
        'Idle': 'cat-idle',
    };
    return map[cat] || 'cat-other';
}

/* ── Utilities ───────────────────────────────────────────── */
function formatDuration(secs) {
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/* ── Chart instances (for cleanup) ───────────────────────── */
let chartInstances = {};

function destroyChart(id) {
    if (chartInstances[id]) {
        chartInstances[id].destroy();
        delete chartInstances[id];
    }
}

/* ── Chart.js default config ─────────────────────────────── */
Chart.defaults.color = '#8b8fa3';
Chart.defaults.borderColor = '#2a2d3a';
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

/* ── Pie Chart: Category Breakdown ───────────────────────── */
function renderCategoryPie(canvasId, categories) {
    destroyChart(canvasId);
    const labels = Object.keys(categories);
    const data = Object.values(categories);
    const colors = labels.map(getCategoryColor);

    chartInstances[canvasId] = new Chart(document.getElementById(canvasId), {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 0,
                hoverOffset: 6,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'right', labels: { padding: 12, usePointStyle: true } },
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.label}: ${formatDuration(ctx.raw)}`
                    }
                }
            }
        }
    });
}

/* ── Bar Chart: Top Apps ─────────────────────────────────── */
function renderTopAppsBar(canvasId, apps) {
    destroyChart(canvasId);
    const labels = apps.map(a => a.app_name);
    const data = apps.map(a => a.total / 60); // minutes
    const colors = apps.map(a => getCategoryColor(a.category));

    chartInstances[canvasId] = new Chart(document.getElementById(canvasId), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderRadius: 4,
                barThickness: 22,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => `${formatDuration(ctx.raw * 60)}`
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'Minutes' }, grid: { display: false } },
                y: { grid: { display: false } }
            }
        }
    });
}

/* ── Bar Chart: Top Websites ─────────────────────────────── */
function renderTopWebsitesBar(canvasId, websites) {
    destroyChart(canvasId);

    if (!websites || websites.length === 0) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        ctx.fillStyle = '#8b8fa3';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No browser activity recorded', ctx.canvas.width / 2, 50);
        return;
    }

    const labels = websites.map(w => {
        const t = w.window_title || '';
        return t.length > 50 ? t.substring(0, 47) + '...' : t;
    });
    const data = websites.map(w => w.total / 60);
    const colors = websites.map(w => getCategoryColor(w.category));

    chartInstances[canvasId] = new Chart(document.getElementById(canvasId), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderRadius: 4,
                barThickness: 22,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => formatDuration(ctx.raw * 60)
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'Minutes' }, grid: { display: false } },
                y: { grid: { display: false } }
            }
        }
    });
}

/* ── Timeline Chart ──────────────────────────────────────── */
function renderTimeline(canvasId, timeline) {
    destroyChart(canvasId);

    if (!timeline || timeline.length === 0) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        ctx.fillStyle = '#8b8fa3';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No activity recorded', ctx.canvas.width / 2, 50);
        return;
    }

    // Group by category for stacked horizontal display
    const categories = [...new Set(timeline.map(t => t.category))];
    const datasets = categories.map(cat => {
        const segments = timeline.filter(t => t.category === cat).map(t => {
            const start = new Date(t.start_time);
            const end = new Date(t.end_time);
            return [start.getTime(), end.getTime()];
        });
        return {
            label: cat,
            data: segments.map(s => ({ x: s, y: 'Activity' })),
            backgroundColor: getCategoryColor(cat),
        };
    });

    // Simpler approach: horizontal bar segments
    const barData = timeline.map(t => ({
        start: new Date(t.start_time),
        end: new Date(t.end_time),
        category: t.category,
        app: t.app_name,
        title: t.window_title,
        duration: t.duration_seconds,
    }));

    // Use a single stacked bar
    const uniqueCats = [...new Set(barData.map(d => d.category))];
    const dsMap = {};
    uniqueCats.forEach(cat => {
        dsMap[cat] = {
            label: cat,
            data: [],
            backgroundColor: getCategoryColor(cat),
            borderSkipped: false,
            barThickness: 40,
        };
    });

    barData.forEach(d => {
        dsMap[d.category].data.push({
            x: [d.start.getTime(), d.end.getTime()],
            y: 'Activity',
        });
    });

    chartInstances[canvasId] = new Chart(document.getElementById(canvasId), {
        type: 'bar',
        data: {
            datasets: Object.values(dsMap),
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { usePointStyle: true, padding: 8, font: { size: 11 } } },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const raw = ctx.raw;
                            if (raw && raw.x) {
                                const start = new Date(raw.x[0]).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                                const end = new Date(raw.x[1]).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                                return `${ctx.dataset.label}: ${start} - ${end}`;
                            }
                            return ctx.dataset.label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    position: 'top',
                    ticks: {
                        callback: val => new Date(val).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                        maxTicksLimit: 12,
                    },
                    grid: { color: '#2a2d3a' }
                },
                y: { display: false }
            }
        }
    });
}

/* ── Trend Line Chart ────────────────────────────────────── */
function renderTrendLine(canvasId, totals) {
    destroyChart(canvasId);

    if (!totals || totals.length === 0) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        ctx.fillStyle = '#8b8fa3';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No trend data available', ctx.canvas.width / 2, 50);
        return;
    }

    // Group by date and category
    const dates = [...new Set(totals.map(t => t.date))].sort();
    const categories = [...new Set(totals.map(t => t.category))];

    const datasets = categories.map(cat => {
        const dataMap = {};
        totals.filter(t => t.category === cat).forEach(t => {
            dataMap[t.date] = t.total / 3600; // hours
        });
        return {
            label: cat,
            data: dates.map(d => dataMap[d] || 0),
            borderColor: getCategoryColor(cat),
            backgroundColor: getCategoryColor(cat) + '33',
            fill: true,
            tension: 0.3,
            pointRadius: 3,
        };
    });

    chartInstances[canvasId] = new Chart(document.getElementById(canvasId), {
        type: 'line',
        data: { labels: dates, datasets: datasets },
        options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'bottom', labels: { usePointStyle: true, padding: 10 } },
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.dataset.label}: ${ctx.raw.toFixed(1)}h`
                    }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: { title: { display: true, text: 'Hours' }, beginAtZero: true }
            }
        }
    });
}

/* ── Sessions Table (paginated) ──────────────────────────── */
function renderSessionsTable(data) {
    const tbody = document.getElementById('sessions-body');
    const info = document.getElementById('sessions-info');
    const pagination = document.getElementById('sessions-pagination');
    if (!tbody) return;

    const sessions = data.sessions || [];
    const total = data.total || 0;
    const page = data.page || 1;
    const pages = data.pages || 1;
    const perPage = data.per_page || 50;

    // Info line
    if (info) {
        if (total === 0) {
            info.textContent = 'No sessions found';
        } else {
            const from = (page - 1) * perPage + 1;
            const to = Math.min(page * perPage, total);
            info.textContent = `Showing ${from}–${to} of ${total} sessions`;
        }
    }

    if (sessions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#8b8fa3;padding:2rem;">No sessions recorded</td></tr>';
        if (pagination) pagination.innerHTML = '';
        return;
    }

    tbody.innerHTML = sessions.map(s => {
        const dateStr = s.start_time.substring(0, 10);
        const start = (s.start_time.split('T')[1] || s.start_time.substring(11)).substring(0, 5);
        const end = (s.end_time.split('T')[1] || s.end_time.substring(11)).substring(0, 5);
        const catClass = getCategoryClass(s.category);
        return `<tr>
            <td>${dateStr}</td>
            <td>${start} - ${end}</td>
            <td>${formatDuration(s.duration_seconds)}</td>
            <td>${escapeHtml(s.app_name)}</td>
            <td class="title-cell">${escapeHtml(s.window_title || '')}</td>
            <td><a href="/details/${encodeURIComponent(s.category)}?date=${dateStr}" class="cat-badge ${catClass}">${escapeHtml(s.category)}</a></td>
        </tr>`;
    }).join('');

    // Pagination controls
    if (pagination) {
        if (pages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        let html = '';
        html += `<button class="btn btn-sm" onclick="loadSessions(1)" ${page === 1 ? 'disabled' : ''}>&laquo;</button>`;
        html += `<button class="btn btn-sm" onclick="loadSessions(${page - 1})" ${page === 1 ? 'disabled' : ''}>&lsaquo; Prev</button>`;

        // Show page numbers around current page
        const startPage = Math.max(1, page - 2);
        const endPage = Math.min(pages, page + 2);
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="btn btn-sm ${i === page ? 'btn-active' : ''}" onclick="loadSessions(${i})">${i}</button>`;
        }

        html += `<button class="btn btn-sm" onclick="loadSessions(${page + 1})" ${page === pages ? 'disabled' : ''}> Next &rsaquo;</button>`;
        html += `<button class="btn btn-sm" onclick="loadSessions(${pages})" ${page === pages ? 'disabled' : ''}>&raquo;</button>`;
        pagination.innerHTML = html;
    }
}

async function loadSessions(page = 1) {
    const startDate = document.getElementById('session-start').value;
    const endDate = document.getElementById('session-end').value;
    try {
        const res = await fetch(`/api/sessions?start_date=${startDate}&end_date=${endDate}&page=${page}&per_page=50`);
        const data = await res.json();
        renderSessionsTable(data);
    } catch (err) {
        console.error('Failed to load sessions:', err);
    }
}

/* ── Load All Data ───────────────────────────────────────── */
async function loadAllData(date) {
    try {
        const [summaryRes, appsRes, websitesRes, timelineRes] = await Promise.all([
            fetch(`/api/summary?date=${date}`),
            fetch(`/api/top-apps?date=${date}`),
            fetch(`/api/top-websites?date=${date}`),
            fetch(`/api/timeline?date=${date}`),
        ]);

        const summary = await summaryRes.json();
        const apps = await appsRes.json();
        const websites = await websitesRes.json();
        const timeline = await timelineRes.json();

        // Stats
        document.getElementById('total-active').textContent = formatDuration(summary.total_active || 0);
        document.getElementById('total-idle').textContent = formatDuration(summary.total_idle || 0);

        const cats = summary.categories || {};
        const topCat = Object.entries(cats).sort((a, b) => b[1] - a[1])[0];
        document.getElementById('top-category').textContent = topCat ? topCat[0] : '--';

        // Charts
        renderCategoryPie('category-pie', cats);
        renderTopAppsBar('top-apps-bar', apps.apps || []);
        renderTopWebsitesBar('top-websites-bar', websites.websites || []);
        renderTimeline('timeline-chart', timeline.timeline || []);

        // Sync session date filters and load first page
        const sessionStart = document.getElementById('session-start');
        const sessionEnd = document.getElementById('session-end');
        if (sessionStart) sessionStart.value = date;
        if (sessionEnd) sessionEnd.value = date;
        loadSessions(1);

    } catch (err) {
        console.error('Failed to load dashboard data:', err);
    }
}

async function loadTrends() {
    const daysSelect = document.getElementById('trend-days');
    const days = daysSelect ? daysSelect.value : 30;
    try {
        const res = await fetch(`/api/trends?days=${days}`);
        const data = await res.json();
        renderTrendLine('trend-line', data.totals || []);
    } catch (err) {
        console.error('Failed to load trends:', err);
    }
}
