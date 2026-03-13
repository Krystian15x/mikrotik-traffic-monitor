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