/* ═══ Jewelitics — Main JavaScript ═══ */

// ─── Dark Mode Toggle ───
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    html.setAttribute('data-bs-theme', next); // Also switch Bootstrap 5's built-in theme
    localStorage.setItem('theme', next);

    const icon = document.getElementById('themeIcon');
    if (icon) {
        icon.className = next === 'dark'
            ? 'bi bi-sun-fill'
            : 'bi bi-moon-stars-fill';
    }
}

// Setup theme icon on load
document.addEventListener('DOMContentLoaded', function () {
    const saved = localStorage.getItem('theme') || 'light';
    const icon = document.getElementById('themeIcon');
    if (icon) {
        icon.className = saved === 'dark'
            ? 'bi bi-sun-fill'
            : 'bi bi-moon-stars-fill';
    }
});

// ─── Auto-dismiss alerts after 5 seconds ───
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });
});

// ─── Format currency ───
function formatCurrency(amount) {
    return '₹' + Number(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
}
