function setTheme(theme) {
	document.documentElement.setAttribute('data-theme', theme);
	localStorage.setItem('theme', theme);
	const icon = document.getElementById('themeIcon');
	if (icon) {
		icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
	}
}

function getPreferredTheme() {
	const stored = localStorage.getItem('theme');
	if (stored) return stored;
	return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function toggleTheme() {
	const current = document.documentElement.getAttribute('data-theme') || getPreferredTheme();
	setTheme(current === 'dark' ? 'light' : 'dark');
}

document.addEventListener('DOMContentLoaded', function() {
	setTheme(getPreferredTheme());
	const btn = document.getElementById('themeToggle');
	if (btn) {
		btn.addEventListener('click', toggleTheme);
	}
	window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
		if (!localStorage.getItem('theme')) {
			setTheme(e.matches ? 'dark' : 'light');
		}
	});
});

function formatSize(bytes) {
	if (!bytes || bytes < 1) return '0 B';
	const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
	const i = Math.floor(Math.log(bytes) / Math.log(1024));
	return (bytes / 1024 ** i).toFixed(1) + ' ' + units[i];
}

function formatPeriod(p) {
	const mapping = window.APP_CONFIG.mapping;
	if (p === "all") return mapping["all"];
	if (p.endsWith("min")) return p.slice(0, -3) + " " + mapping["min"];
	if (p.endsWith("h")) return p.slice(0, -1) + " " + mapping["h"];
	if (p.endsWith("d")) return p.slice(0, -1) + " " + mapping["d"];
	if (p.endsWith("m")) return p.slice(0, -1) + " " + mapping["m"];
	return p;
}

const periods = window.APP_CONFIG.periods;
let currentPeriod = periods[0];

let trafficChart = new Chart(document.getElementById('trafficChart'), {
	type: 'line', data: { labels: [], datasets: [{ label: 'Dane pobrane', borderColor: 'rgba(75, 192, 192, 1)', backgroundColor: 'rgba(75, 192, 192, 0.2)', tension: 0.1 }, { label: 'Dane wysłane', borderColor: 'rgba(255, 99, 132, 1)', backgroundColor: 'rgba(255, 99, 132, 0.2)', tension: 0.1 }] },
	options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { callback: v => formatSize(v) } } }, plugins: { tooltip: { callbacks: { label: ctx => formatSize(ctx.parsed.y) } } } }
});

let dailyChart = new Chart(document.getElementById('dailyChart'), {
	type: 'bar', data: { labels: [], datasets: [{ label: 'Łączny transfer', data: [], backgroundColor: 'rgba(54, 162, 235, 0.5)' }] },
	options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { callback: v => formatSize(v) } } }, plugins: { tooltip: { callbacks: { label: ctx => formatSize(ctx.parsed.y) } } } }
});

let monthlyChart = new Chart(document.getElementById('monthlyChart'), {
	type: 'bar', data: { labels: [], datasets: [{ label: 'Łączny transfer', data: [], backgroundColor: 'rgba(153, 102, 255, 0.5)' }] },
	options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { callback: v => formatSize(v) } } }, plugins: { tooltip: { callbacks: { label: ctx => formatSize(ctx.parsed.y) } } } }
});

function showLoader(id) { document.getElementById(id).style.display = 'flex'; }
function hideLoader(id) { document.getElementById(id).style.display = 'none'; }

function updatePeriodData(period) {
	showLoader('statsTableLoader');
	showLoader('trafficChartLoader');
	Promise.all([
		fetch(`/api/summary/${period}`).then(res => res.json()).then(data => {
			document.querySelector('#statsTable tbody').innerHTML = `<tr><td>${formatPeriod(period)}</td><td>${formatSize(data.rx_bytes)}</td><td>${formatSize(data.tx_bytes)}</td><td>${formatSize(data.rx_bytes + data.tx_bytes)}</td><td>${(data.rx_packets + data.tx_packets).toLocaleString('pl-PL')}</td><td>${(data.avg_rx_mbps + data.avg_tx_mbps).toFixed(2)}</td></tr>`;
			hideLoader('statsTableLoader');
		}),
		fetch(`/api/chart/${period}`).then(res => res.json()).then(data => {
			trafficChart.data.labels = data.labels;
			trafficChart.data.datasets[0].data = data.rx_data;
			trafficChart.data.datasets[1].data = data.tx_data;
			trafficChart.update();
			hideLoader('trafficChartLoader');
		})
	]);
}

function updateFixedData() {
	showLoader('topStatsLoader');
	showLoader('totalStatsLoader');
	showLoader('dailyChartLoader');
	showLoader('monthlyChartLoader');
	Promise.all([
		fetch('/api/summary/24h').then(res => res.json()).then(data => {
			const totalMbps = data.avg_rx_mbps + data.avg_tx_mbps;
			document.getElementById('total24h').innerText = formatSize(data.rx_bytes + data.tx_bytes);
			document.getElementById('rx24h').innerText = formatSize(data.rx_bytes);
			document.getElementById('tx24h').innerText = formatSize(data.tx_bytes);
			document.getElementById('speed24h').innerText = `${totalMbps.toFixed(2)} Mbps (${(totalMbps * 0.125).toFixed(2)} MB/s)`;
			hideLoader('topStatsLoader');
		}),
		fetch('/api/summary/total').then(res => res.json()).then(data => {
			document.getElementById('averageRxMbps').innerText = data.avg_rx_mbps;
			document.getElementById('averageTxMbps').innerText = data.avg_tx_mbps;
			document.getElementById('averageAllMbps').innerText = (data.avg_rx_mbps + data.avg_tx_mbps).toFixed(2);
			document.getElementById('totalRx').innerText = formatSize(data.rx_bytes);
			document.getElementById('totalTx').innerText = formatSize(data.tx_bytes);
			document.getElementById('totalAll').innerText = formatSize(data.rx_bytes+ data.tx_bytes);
			document.getElementById('totalRxCount').innerText = data.rx_packets.toLocaleString();
			document.getElementById('totalTxCount').innerText = data.tx_packets.toLocaleString();
			document.getElementById('totalAllCount').innerText = (data.rx_packets + data.tx_packets).toLocaleString();
			hideLoader('totalStatsLoader');
		}),
		fetch('/api/daily').then(res => res.json()).then(data => {
			dailyChart.data.labels = data.map(d => d.date);
			dailyChart.data.datasets[0].data = data.map(d => d.total_bytes);
			dailyChart.update();
			hideLoader('dailyChartLoader');
		}),
		fetch('/api/monthly').then(res => res.json()).then(data => {
			monthlyChart.data.labels = data.map(m => m.month);
			monthlyChart.data.datasets[0].data = data.map(m => m.total_bytes);
			monthlyChart.update();
			hideLoader('monthlyChartLoader');
		})
	]);
}

document.querySelectorAll('.period-tab').forEach(tab => {
	tab.addEventListener('click', e => {
		e.preventDefault();
		document.querySelectorAll('.period-tab').forEach(t => t.classList.remove('active'));
		tab.classList.add('active');
		currentPeriod = tab.dataset.period;
		updatePeriodData(currentPeriod);
	});
});

document.querySelector('.period-tab').classList.add('active');
updatePeriodData(currentPeriod);
updateFixedData();

setInterval(() => {
	updatePeriodData(currentPeriod);
	updateFixedData();
}, 60000);

document.getElementById('generateStatement').addEventListener('click', () => {
	const start = document.getElementById('startDate').value;
	const end = document.getElementById('endDate').value;
	if (!start || !end) {
		alert('Proszę wybrać daty rozpoczęcia i zakończenia.');
		return;
	}
	if (new Date(start) > new Date(end)) {
		alert('Data początkowa nie może być późniejsza niż data końcowa.');
		return;
	}
	showLoader('statementModalLoader');
	fetch('/api/statement', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ start, end })
	})
	.then(res => {
		if (!res.ok) {
			throw new Error(`Błąd serwera: ${res.status}`);
		}
		return res.text();
	})
	.then(html => {
		const newWindow = window.open('', '_blank');
		newWindow.document.write(html);
		newWindow.document.close();
		bootstrap.Modal.getInstance(document.getElementById('statementModal')).hide();
	})
	.catch(err => {
		alert('Wystąpił błąd podczas generowania wyciągu.');
	})
	.finally(() => hideLoader('statementModalLoader'));
});

document.querySelector('.btn.btn-secondary[data-bs-dismiss="modal"]').addEventListener('click', () => {
	document.querySelector('button[data-bs-target="#statementModal"]').focus();
	bootstrap.Modal.getInstance(document.getElementById('statementModal')).hide();
});

const startDate = document.getElementById('startDate'),
	endDate = document.getElementById('endDate'),
	timeRange = document.getElementById('timeRange');
	timeRange.appendChild(new Option("Niestandardowy", "custom"));
	document.querySelectorAll('.period-tab').forEach(tab=>{
	if (/^\d+/.test(tab.dataset.period)) {
		timeRange.appendChild(new Option(tab.textContent.trim(), tab.dataset.period));
	}
});

timeRange.addEventListener('change', e=>{
	const period = e.target.value;
	startDate.value = endDate.value = '';
	if (period === 'custom') return;
	const match = /^(\d+)(min|h|d|m)$/.exec(period);
	if (!match) return;
	const ms = { min: 60000, h: 3600000, d: 86400000, m: 2592000000 };
	startDate.value = new Date(Date.now() - parseInt(match[1]) * ms[match[2]]).toISOString().slice(0, 16);
	endDate.value = new Date().toISOString().slice(0, 16);
});