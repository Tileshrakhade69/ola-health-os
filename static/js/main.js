/**
 * OLA Health OS - Global JavaScript Utilities & Navigation
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle
    const sidebar = document.querySelector('.app-sidebar');
    const mobileToggle = document.getElementById('mobile-sidebar-toggle');
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // 2. Database Status Check
    fetchDbStatus();
});

// Toast notification helper
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? '✓' : (type === 'error' ? '⚠' : 'ℹ');
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Fetch database status for topbar badge
async function fetchDbStatus() {
    try {
        const res = await fetch('/api/db-status');
        const data = await res.json();
        const badge = document.getElementById('db-status-badge');
        if (badge) {
            badge.innerText = data.engine;
            badge.className = data.is_demo_mode ? 'badge badge-info' : 'badge badge-success';
            badge.title = `Location: ${data.location} | Active Admissions: ${data.total_admissions}`;
        }
    } catch (err) {
        console.warn('DB status fetch failed:', err);
    }
}
