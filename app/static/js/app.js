// ============================================================
// VetOnlineCRM — Frontend Application
// ============================================================

let currentDoctor = null;
let currentPetId = null;
let currentIntakeId = null;
let calendarWeekStart = null;
let allTemplates = [];
let selectedCategoryId = null;

// ============ INIT ============
document.addEventListener('DOMContentLoaded', async () => {
    await loadCurrentUser();
    loadDashboard();
    loadTheme();
});

async function loadCurrentUser() {
    try {
        const resp = await fetch('/api/auth/me');
        if (!resp.ok) {
            window.location.href = '/login';
            return;
        }
        currentDoctor = await resp.json();
        document.getElementById('userName').textContent = currentDoctor.full_name;
        document.getElementById('headerUserName').textContent = currentDoctor.full_name;
        if (currentDoctor.is_admin) {
            const adminSection = document.getElementById('adminSection');
            if (adminSection) adminSection.style.display = 'block';
        }
    } catch (e) {
        window.location.href = '/login';
    }
}

// ============ NAVIGATION ============
function navigate(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const pageEl = document.getElementById('page-' + page);
    if (pageEl) pageEl.classList.add('active');

    const navEl = document.querySelector(`.nav-item[data-page="${page}"]`);
    if (navEl) navEl.classList.add('active');

    // Close mobile sidebar
    document.getElementById('sidebar').classList.remove('open');

    // Load data for page
    switch (page) {
        case 'dashboard': loadDashboard(); break;
        case 'patients': loadOwners(); loadPets(); break;
        case 'calendar': loadCalendar(); break;
        case 'visits': loadVisits(); break;
        case 'templates': loadCategories(); loadTemplates(); break;
        case 'questionnaires': loadQuestionnaires(); loadIntakes(); break;
        case 'reminders': loadReminders(); break;
        case 'settings': loadSettings(); break;
    }
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// ============ THEME ============
function loadTheme() {
    const theme = localStorage.getItem('vetcrm_theme') || 'light';
    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const isDark = document.body.classList.contains('dark-theme');
    localStorage.setItem('vetcrm_theme', isDark ? 'dark' : 'light');
}

// ============ TOAST ============
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + type + ' show';
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ============ MODALS ============
function showModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

// Close modal on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// ============ LOGOUT ============
async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login';
}

// ============ GLOBAL SEARCH ============
let searchTimeout = null;
async function handleGlobalSearch(query) {
    const resultsEl = document.getElementById('searchResults');

    if (!query || query.length < 2) {
        resultsEl.classList.remove('active');
        return;
    }

    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
        try {
            const resp = await fetch(`/api/patients/search?q=${encodeURIComponent(query)}`);
            const data = await resp.json();

            let html = '';

            if (data.owners && data.owners.length > 0) {
                html += '<div style="padding:8px 15px;font-size:12px;color:#888;background:#f5f5f5">Владельцы</div>';
                data.owners.forEach(o => {
                    html += `<div class="search-result-item" onclick="openOwnerPets(${o.id})">
                        <div class="name">👤 ${o.full_name}</div>
                        <div class="info">${o.phone || ''}</div>
                    </div>`;
                });
            }

            if (data.pets && data.pets.length > 0) {
                html += '<div style="padding:8px 15px;font-size:12px;color:#888;background:#f5f5f5">Питомцы</div>';
                data.pets.forEach(p => {
                    html += `<div class="search-result-item" onclick="openPetCard(${p.id})">
                        <div class="name">🐾 ${p.name} (${p.species})</div>
                        <div class="info">${p.owner_name} ${p.breed ? '• ' + p.breed : ''}</div>
                    </div>`;
                });
            }

            if (!html) {
                html = '<div class="search-result-item"><div class="info">Ничего не найдено</div></div>';
            }

            resultsEl.innerHTML = html;
            resultsEl.classList.add('active');
        } catch (e) {
            console.error(e);
        }
    }, 300);
}

// Hide search results on click outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-box')) {
        document.getElementById('searchResults').classList.remove('active');
    }
});

function openOwnerPets(ownerId) {
    document.getElementById('searchResults').classList.remove('active');
    document.getElementById('globalSearch').value = '';
    navigate('patients');
    // TODO: filter by owner
}

// ============ DASHBOARD ============
async function loadDashboard() {
    try {
        const resp = await fetch('/api/dashboard');
        const data = await resp.json();

        document.getElementById('statOwners').textContent = data.stats.total_owners;
        document.getElementById('statPets').textContent = data.stats.total_pets;
        document.getElementById('statVisits').textContent = data.stats.total_visits;
        document.getElementById('statToday').textContent = data.stats.today_visits;
        document.getElementById('statIntakes').textContent = data.stats.new_intakes;
        document.getElementById('statWeek').textContent = data.stats.week_visits;

        // Upcoming
        const upcomingEl = document.getElementById('upcomingList');
        if (data.upcoming && data.upcoming.length > 0) {
            upcomingEl.innerHTML = data.upcoming.map(u => `
                <div class="upcoming-item">
                    <div>
                        <span class="time">${u.date} ${u.hour}:00</span>
                        <span class="patient"> — ${u.pet_name} (${u.pet_species})</span>
                    </div>
                    <div class="info">${u.owner_name} ${u.owner_phone}</div>
                </div>
            `).join('');
        } else {
            upcomingEl.innerHTML = '<p class="empty-text">Нет предстоящих приёмов</p>';
        }

        // Reminders
        const remindersEl = document.getElementById('todayReminders');
        if (data.reminders && data.reminders.length > 0) {
            remindersEl.innerHTML = data.reminders.map(r => `
                <div class="reminder-item">
                    <div>
                        <span class="reminder-title">${r.title}</span>
                        <span class="reminder-type">${r.reminder_type}</span>
                    </div>
                    <div class="info">${r.description || ''}</div>
                </div>
            `).join('');
        } else {
            remindersEl.innerHTML = '<p class="empty-text">Нет напоминаний на сегодня</p>';
        }
    } catch (e) {
        console.error('Dashboard error:', e);
    }
}
