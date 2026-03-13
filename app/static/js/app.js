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

// ============ OWNERS ============
async function loadOwners(search = '') {
    try {
        const resp = await fetch(`/api/patients/owners?search=${encodeURIComponent(search)}`);
        const owners = await resp.json();
        const el = document.getElementById('ownersList');

        if (owners.length === 0) {
            el.innerHTML = '<div class="empty-state"><div class="empty-icon">👥</div><div class="empty-title">Нет владельцев</div><div class="empty-desc">Добавьте первого владельца</div></div>';
            return;
        }

        el.innerHTML = owners.map(o => `
            <div class="data-card" onclick="openOwnerPets(${o.id})">
                <div class="data-card-info">
                    <div class="title">👤 ${o.full_name}</div>
                    <div class="subtitle">${o.phone || 'Нет телефона'} ${o.email ? '• ' + o.email : ''}</div>
                    <div class="details">${o.messenger ? '💬 ' + o.messenger : ''} • Питомцев: ${o.pets ? o.pets.length : 0}</div>
                </div>
                <div class="data-card-actions">
                    <button onclick="event.stopPropagation(); editOwner(${o.id})" title="Редактировать">✏️</button>
                    <button onclick="event.stopPropagation(); deleteOwner(${o.id})" title="Удалить">🗑️</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Load owners error:', e);
    }
}

async function saveOwner() {
    const editId = document.getElementById('ownerEditId').value;
    const data = {
        full_name: document.getElementById('ownerName').value,
        phone: document.getElementById('ownerPhone').value,
        email: document.getElementById('ownerEmail').value,
        messenger: document.getElementById('ownerMessenger').value,
        notes: document.getElementById('ownerNotes').value
    };

    if (!data.full_name) {
        showToast('ФИО обязательно', 'error');
        return;
    }

    try {
        const url = editId ? `/api/patients/owners/${editId}` : '/api/patients/owners';
        const method = editId ? 'PUT' : 'POST';
        const resp = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (resp.ok) {
            showToast(editId ? 'Владелец обновлён' : 'Владелец добавлен');
            closeModal('ownerModal');
            clearOwnerForm();
            loadOwners();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Ошибка', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

async function editOwner(id) {
    try {
        const resp = await fetch(`/api/patients/owners?search=`);
        const owners = await resp.json();
        const owner = owners.find(o => o.id === id);
        if (!owner) return;

        document.getElementById('ownerEditId').value = owner.id;
        document.getElementById('ownerName').value = owner.full_name;
        document.getElementById('ownerPhone').value = owner.phone || '';
        document.getElementById('ownerEmail').value = owner.email || '';
        document.getElementById('ownerMessenger').value = owner.messenger || '';
        document.getElementById('ownerNotes').value = owner.notes || '';
        document.getElementById('ownerModalTitle').textContent = 'Редактировать владельца';
        showModal('ownerModal');
    } catch (e) {
        showToast('Ошибка загрузки', 'error');
    }
}

async function deleteOwner(id) {
    if (!confirm('Удалить владельца и всех его питомцев?')) return;
    try {
        const resp = await fetch(`/api/patients/owners/${id}`, { method: 'DELETE' });
        if (resp.ok) {
            showToast('Владелец удалён');
            loadOwners();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Ошибка', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

function clearOwnerForm() {
    document.getElementById('ownerEditId').value = '';
    document.getElementById('ownerName').value = '';
    document.getElementById('ownerPhone').value = '';
    document.getElementById('ownerEmail').value = '';
    document.getElementById('ownerMessenger').value = '';
    document.getElementById('ownerNotes').value = '';
    document.getElementById('ownerModalTitle').textContent = 'Новый владелец';
}

// ============ PETS ============
async function loadPets(search = '') {
    try {
        const resp = await fetch(`/api/patients/pets?search=${encodeURIComponent(search)}`);
        const pets = await resp.json();
        const el = document.getElementById('petsList');

        if (pets.length === 0) {
            el.innerHTML = '<div class="empty-state"><div class="empty-icon">🐾</div><div class="empty-title">Нет питомцев</div><div class="empty-desc">Добавьте первого питомца</div></div>';
            return;
        }

        el.innerHTML = pets.map(p => `
            <div class="data-card" onclick="openPetCard(${p.id})">
                <div class="data-card-info">
                    <div class="title">${p.species === 'Кошка' ? '🐱' : '🐶'} ${p.name}</div>
                    <div class="subtitle">${p.species} ${p.breed ? '• ' + p.breed : ''} ${p.age ? '• ' + p.age : ''}</div>
                    <div class="details">Владелец: ${p.owner.full_name} ${p.owner.phone ? '• ' + p.owner.phone : ''}</div>
                </div>
                <div class="data-card-actions">
                    <button onclick="event.stopPropagation(); editPet(${p.id})" title="Редактировать">✏️</button>
                    <button onclick="event.stopPropagation(); deletePet(${p.id})" title="Удалить">🗑️</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Load pets error:', e);
    }
}

async function savePet() {
    const editId = document.getElementById('petEditId').value;
    const data = {
        owner_id: parseInt(document.getElementById('petOwnerSelect').value),
        name: document.getElementById('petName').value,
        species: document.getElementById('petSpecies').value,
        breed: document.getElementById('petBreed').value,
        age: document.getElementById('petAge').value,
        weight: parseFloat(document.getElementById('petWeight').value) || null,
        sex: document.getElementById('petSex').value,
        chip_number: document.getElementById('petChip').value,
        notes: document.getElementById('petNotes').value
    };

    if (!data.owner_id || !data.name || !data.species) {
        showToast('Заполните обязательные поля', 'error');
        return;
    }

    try {
        const url = editId ? `/api/patients/pets/${editId}` : '/api/patients/pets';
        const method = editId ? 'PUT' : 'POST';
        const resp = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (resp.ok) {
            showToast(editId ? 'Питомец обновлён' : 'Питомец добавлен');
            closeModal('petModal');
            clearPetForm();
            loadPets();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Ошибка', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

async function editPet(id) {
    try {
        const resp = await fetch(`/api/patients/pets/${id}`);
        if (!resp.ok) return;
        const pet = await resp.json();

        await loadOwnerSelect();
        document.getElementById('petEditId').value = pet.id;
        document.getElementById('petOwnerSelect').value = pet.owner.id;
        document.getElementById('petName').value = pet.name;
        document.getElementById('petSpecies').value = pet.species;
        document.getElementById('petBreed').value = pet.breed || '';
        document.getElementById('petAge').value = pet.age || '';
        document.getElementById('petWeight').value = pet.weight || '';
        document.getElementById('petSex').value = pet.sex || '';
        document.getElementById('petChip').value = pet.chip_number || '';
        document.getElementById('petNotes').value = pet.notes || '';
        document.getElementById('petModalTitle').textContent = 'Редактировать питомца';
        showModal('petModal');
    } catch (e) {
        showToast('Ошибка загрузки', 'error');
    }
}

async function deletePet(id) {
    if (!confirm('Удалить питомца?')) return;
    try {
        const resp = await fetch(`/api/patients/pets/${id}`, { method: 'DELETE' });
        if (resp.ok) {
            showToast('Питомец удалён');
            loadPets();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Ошибка', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

function clearPetForm() {
    document.getElementById('petEditId').value = '';
    document.getElementById('petName').value = '';
    document.getElementById('petSpecies').value = '';
    document.getElementById('petBreed').value = '';
    document.getElementById('petAge').value = '';
    document.getElementById('petWeight').value = '';
    document.getElementById('petSex').value = '';
    document.getElementById('petChip').value = '';
    document.getElementById('petNotes').value = '';
    document.getElementById('petModalTitle').textContent = 'Новый питомец';
}

async function loadOwnerSelect() {
    try {
        const resp = await fetch('/api/patients/owners');
        const owners = await resp.json();
        const selects = ['petOwnerSelect'];
        selects.forEach(selectId => {
            const el = document.getElementById(selectId);
            if (el) {
                el.innerHTML = '<option value="">Выберите владельца...</option>' +
                    owners.map(o => `<option value="${o.id}">${o.full_name} ${o.phone ? '(' + o.phone + ')' : ''}</option>`).join('');
            }
        });
    } catch (e) {
        console.error(e);
    }
}

// Patient tabs
function switchPatientTab(tab) {
    document.querySelectorAll('#page-patients .tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('ownersTab').classList.remove('active');
    document.getElementById('petsTab').classList.remove('active');

    if (tab === 'owners') {
        document.querySelectorAll('#page-patients .tab-btn')[0].classList.add('active');
        document.getElementById('ownersTab').classList.add('active');
    } else {
        document.querySelectorAll('#page-patients .tab-btn')[1].classList.add('active');
        document.getElementById('petsTab').classList.add('active');
    }
}

function searchPatients(query) {
    const isOwners = document.getElementById('ownersTab').classList.contains('active');
    if (isOwners) {
        loadOwners(query);
    } else {
        loadPets(query);
    }
}

// Override showModal for pet modal to load owners
const originalShowModal = showModal;
showModal = function(id) {
    if (id === 'petModal') {
        loadOwnerSelect();
        if (!document.getElementById('petEditId').value) {
            clearPetForm();
        }
    }
    if (id === 'ownerModal' && !document.getElementById('ownerEditId').value) {
        clearOwnerForm();
    }
    originalShowModal(id);
};

// ============ PET CARD ============
async function openPetCard(petId) {
    currentPetId = petId;
    document.getElementById('searchResults').classList.remove('active');
    document.getElementById('globalSearch').value = '';

    try {
        const resp = await fetch(`/api/patients/pets/${petId}`);
        if (!resp.ok) {
            showToast('Питомец не найден', 'error');
            return;
        }
        const pet = await resp.json();

        document.getElementById('petCardTitle').textContent = `${pet.name} — карточка`;

        // Pet info
        document.getElementById('petCardInfo').innerHTML = `
            <div class="pet-name">${pet.species === 'Кошка' ? '🐱' : '🐶'} ${pet.name}</div>
            <div class="pet-species">${pet.species} ${pet.breed ? '• ' + pet.breed : ''}</div>
            <div class="info-row"><span class="label">Возраст</span><span class="value">${pet.age || '—'}</span></div>
            <div class="info-row"><span class="label">Вес</span><span class="value">${pet.weight ? pet.weight + ' кг' : '—'}</span></div>
            <div class="info-row"><span class="label">Пол</span><span class="value">${pet.sex || '—'}</span></div>
            <div class="info-row"><span class="label">Чип</span><span class="value">${pet.chip_number || '—'}</span></div>
            <div class="info-row"><span class="label">Заметки</span><span class="value">${pet.notes || '—'}</span></div>
            <hr style="margin:15px 0;border-color:#f0f0f0">
            <div class="info-row"><span class="label">Владелец</span><span class="value">${pet.owner.full_name}</span></div>
            <div class="info-row"><span class="label">Телефон</span><span class="value">${pet.owner.phone || '—'}</span></div>
            <div class="info-row"><span class="label">Email</span><span class="value">${pet.owner.email || '—'}</span></div>
            <div class="info-row"><span class="label">Мессенджер</span><span class="value">${pet.owner.messenger || '—'}</span></div>
        `;

        // Visits history
        const visitsEl = document.getElementById('petVisitsList');
        if (pet.visits && pet.visits.length > 0) {
            visitsEl.innerHTML = pet.visits.map(v => `
                <div class="data-card" onclick="openVisit(${v.id})">
                    <div class="data-card-info">
                        <div class="title">
                            ${v.visit_date ? new Date(v.visit_date).toLocaleDateString('ru-RU') : ''}
                            <span class="badge badge-${v.status}">${statusLabel(v.status)}</span>
                            <span class="badge badge-${v.visit_type}">${typeLabel(v.visit_type)}</span>
                        </div>
                        <div class="subtitle">${v.anamnesis ? v.anamnesis.substring(0, 100) + '...' : 'Без описания'}</div>
                        <div class="details">${v.weight ? 'Вес: ' + v.weight + ' кг' : ''} ${v.recommendations ? '• Есть рекомендации' : ''}</div>
                    </div>
                </div>
            `).join('');
        } else {
            visitsEl.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-title">Нет приёмов</div></div>';
        }

        // Files
        const filesEl = document.getElementById('petFilesList');
        if (pet.files && pet.files.length > 0) {
            filesEl.innerHTML = pet.files.map(f => `
                <div class="file-item">
                    <span class="file-icon">${fileIcon(f.file_type)}</span>
                    <span class="file-name">${f.original_name}</span>
                    <div class="file-actions">
                        <button onclick="downloadFile(${f.id})" title="Скачать">⬇️</button>
                        <button onclick="deleteFile(${f.id})" title="Удалить">🗑️</button>
                    </div>
                </div>
            `).join('');
        } else {
            filesEl.innerHTML = '<div class="empty-state"><div class="empty-icon">📎</div><div class="empty-title">Нет файлов</div></div>';
        }

        // Show pet card page
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.getElementById('page-petcard').classList.add('active');
    } catch (e) {
        showToast('Ошибка загрузки карточки', 'error');
        console.error(e);
    }
}

function switchPetCardTab(tab) {
    document.querySelectorAll('#page-petcard .pet-tabs .tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('petHistoryTab').classList.remove('active');
    document.getElementById('petFilesTab').classList.remove('active');

    if (tab === 'history') {
        document.querySelectorAll('#page-petcard .pet-tabs .tab-btn')[0].classList.add('active');
        document.getElementById('petHistoryTab').classList.add('active');
    } else {
        document.querySelectorAll('#page-petcard .pet-tabs .tab-btn')[1].classList.add('active');
        document.getElementById('petFilesTab').classList.add('active');
    }
}

function showNewVisitForPet() {
    clearVisitForm();
    loadPetSelect().then(() => {
        document.getElementById('visitPetSelect').value = currentPetId;
        showModal('visitModal');
    });
}

// ============ FILES ============
function uploadFileToPet() {
    document.getElementById('petFileInput').click();
}

async function handlePetFileUpload(event) {
    const files = event.target.files;
    if (!files.length) return;

    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('pet_id', currentPetId);

        try {
            const resp = await fetch('/api/files/upload', {
                method: 'POST',
                body: formData
            });
            if (resp.ok) {
                showToast(`Файл "${file.name}" загружен`);
            } else {
                const err = await resp.json();
                showToast(err.detail || 'Ошибка загрузки', 'error');
            }
        } catch (e) {
            showToast('Ошибка сети', 'error');
        }
    }

    event.target.value = '';
    openPetCard(currentPetId);
}

function downloadFile(fileId) {
    window.open(`/api/files/download/${fileId}`, '_blank');
}

async function deleteFile(fileId) {
    if (!confirm('Удалить файл?')) return;
    try {
        const resp = await fetch(`/api/files/${fileId}`, { method: 'DELETE' });
        if (resp.ok) {
            showToast('Файл удалён');
            openPetCard(currentPetId);
        }
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}

function downloadEpicrisis(format) {
    if (!currentPetId) return;
    window.open(`/api/documents/epicrisis/${currentPetId}/${format}`, '_blank');
}

// ============ HELPERS ============
function statusLabel(status) {
    const map = { scheduled: 'Запланирован', completed: 'Завершён', cancelled: 'Отменён' };
    return map[status] || status;
}

function typeLabel(type) {
    const map = { primary: 'Первичный', follow_up: 'Повторный' };
    return map[type] || type;
}

function fileIcon(type) {
    const map = { image: '🖼️', video: '🎥', document: '📄' };
    return map[type] || '📎';
}

function formatDate(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    return d.toLocaleDateString('ru-RU') + ' ' + d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
}

// ============ VISITS ============
async function loadVisits() {
    try {
        const status = document.getElementById('visitStatusFilter').value;
        const type = document.getElementById('visitTypeFilter').value;
        let url = '/api/visits?';
        if (status) url += `status=${status}&`;
        if (type) url += `visit_type=${type}&`;

        const resp = await fetch(url);
        const visits = await resp.json();
        const el = document.getElementById('visitsList');

        if (visits.length === 0) {
            el.innerHTML = '<div class="empty-state"><div class="empty-icon">💊</div><div class="empty-title">Нет приёмов</div><div class="empty-desc">Создайте первый приём</div></div>';
            return;
        }

        el.innerHTML = visits.map(v => `
            <div class="data-card" onclick="openVisit(${v.id})">
                <div class="data-card-info">
                    <div class="title">
                        ${v.pet.name} (${v.pet.species})
                        <span class="badge badge-${v.status}">${statusLabel(v.status)}</span>
                        <span class="badge badge-${v.visit_type}">${typeLabel(v.visit_type)}</span>
                    </div>
                    <div class="subtitle">${v.owner.full_name} • ${v.visit_date ? formatDate(v.visit_date) : ''}</div>
                    <div class="details">${v.anamnesis ? v.anamnesis.substring(0, 80) + '...' : ''}</div>
                </div>
                <div class="data-card-actions">
                    <button onclick="event.stopPropagation(); deleteVisit(${v.id})" title="Удалить">🗑️</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Load visits error:', e);
    }
}

async function loadPetSelect() {
    try {
        const resp = await fetch('/api/patients/pets');
        const pets = await resp.json();
        const selects = ['visitPetSelect', 'slotPetSelect'];
        selects.forEach(selectId => {
            const el = document.getElementById(selectId);
            if (el) {
                const emptyOption = selectId === 'slotPetSelect' ?
                    '<option value="">— Свободный слот —</option>' :
                    '<option value="">Выберите питомца...</option>';
                el.innerHTML = emptyOption +
                    pets.map(p => `<option value="${p.id}">${p.name} (${p.species}) — ${p.owner.full_name}</option>`).join('');
            }
        });
    } catch (e) {
        console.error(e);
    }
}

async function openVisit(visitId) {
    try {
        const resp = await fetch(`/api/visits/${visitId}`);
        if (!resp.ok) return;
        const v = await resp.json();

        await loadPetSelect();

        document.getElementById('visitEditId').value = v.id;
        document.getElementById('visitPetSelect').value = v.pet.id;
        document.getElementById('visitType').value = v.visit_type;
        document.getElementById('visitStatus').value = v.status;
        document.getElementById('visitWeight').value = v.weight || '';
        document.getElementById('visitTemp').value = v.temperature || '';
        document.getElementById('visitAnamnesis').value = v.anamnesis || '';
        document.getElementById('visitRecommendations').value = v.recommendations || '';
        document.getElementById('visitNotes').value = v.notes || '';

        if (v.visit_date) {
            const dt = new Date(v.visit_date);
            const local = new Date(dt.getTime() - dt.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
            document.getElementById('visitDate').value = local;
        }

        // Show header info
        document.getElementById('visitHeaderInfo').innerHTML = `
            <strong>${v.pet.name}</strong> (${v.pet.species} ${v.pet.breed || ''}) —
            Владелец: ${v.owner.full_name} ${v.owner.phone || ''}
        `;

        // Show doc buttons
        document.getElementById('btnVisitPdf').style.display = 'inline-flex';
        document.getElementById('btnVisitDocx').style.display = 'inline-flex';
        document.getElementById('visitModalTitle').textContent = 'Редактировать приём';

        showModal('visitModal');
    } catch (e) {
        showToast('Ошибка загрузки приёма', 'error');
    }
}

async function saveVisit() {
    const editId = document.getElementById('visitEditId').value;
    const data = {
        pet_id: parseInt(document.getElementById('visitPetSelect').value),
        visit_type: document.getElementById('visitType').value,
        status: document.getElementById('visitStatus').value,
        weight: parseFloat(document.getElementById('visitWeight').value) || null,
        temperature: parseFloat(document.getElementById('visitTemp').value) || null,
        anamnesis: document.getElementById('visitAnamnesis').value,
        recommendations: document.getElementById('visitRecommendations').value,
        notes: document.getElementById('visitNotes').value,
        visit_date: document.getElementById('visitDate').value || null
    };

    if (!data.pet_id) {
        showToast('Выберите питомца', 'error');
        return;
    }

    try {
        const url = editId ? `/api/visits/${editId}` : '/api/visits';
        const method = editId ? 'PUT' : 'POST';
        const resp = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (resp.ok) {
            showToast(editId ? 'Приём обновлён' : 'Приём создан');
            closeModal('visitModal');
            clearVisitForm();
            loadVisits();
            if (currentPetId) openPetCard(currentPetId);
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Ошибка', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

async function deleteVisit(id) {
    if (!confirm('Удалить приём?')) return;
    try {
        const resp = await fetch(`/api/visits/${id}`, { method: 'DELETE' });
        if (resp.ok) {
            showToast('Приём удалён');
            loadVisits();
        }
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}

function clearVisitForm() {
    document.getElementById('visitEditId').value = '';
    document.getElementById('visitType').value = 'primary';
    document.getElementById('visitStatus').value = 'scheduled';
    document.getElementById('visitWeight').value = '';
    document.getElementById('visitTemp').value = '';
    document.getElementById('visitAnamnesis').value = '';
    document.getElementById('visitRecommendations').value = '';
    document.getElementById('visitNotes').value = '';
    document.getElementById('visitDate').value = '';
    document.getElementById('visitHeaderInfo').innerHTML = '';
    document.getElementById('btnVisitPdf').style.display = 'none';
    document.getElementById('btnVisitDocx').style.display = 'none';
    document.getElementById('visitModalTitle').textContent = 'Новый приём';
}

function onVisitPetChange() {
    // Could load pet info here
}

function downloadVisitDoc(format) {
    const visitId = document.getElementById('visitEditId').value;
    if (!visitId) return;
    window.open(`/api/documents/visit/${visitId}/${format}`, '_blank');
}

// ============ CALENDAR ============
function getMonday(d) {
    const date = new Date(d);
    const day = date.getDay();
    const diff = date.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(date.setDate(diff));
}

function formatDateStr(d) {
    return d.toISOString().split('T')[0];
}

const dayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

async function loadCalendar() {
    if (!calendarWeekStart) {
        calendarWeekStart = getMonday(new Date());
    }

    const weekEnd = new Date(calendarWeekStart);
    weekEnd.setDate(weekEnd.getDate() + 6);

    document.getElementById('calendarTitle').textContent =
        `${calendarWeekStart.getDate()} ${monthNames[calendarWeekStart.getMonth()]} — ${weekEnd.getDate()} ${monthNames[weekEnd.getMonth()]} ${weekEnd.getFullYear()}`;

    try {
        const resp = await fetch(`/api/calendar?week=${formatDateStr(calendarWeekStart)}`);
        const data = await resp.json();

        const workStart = data.work_start || 9;
        const workEnd = data.work_end || 21;

        // Build slots map
        const slotsMap = {};
        data.slots.forEach(s => {
            const key = `${s.date}_${s.hour}`;
            slotsMap[key] = s;
        });

        const today = new Date().toISOString().split('T')[0];

        // Header
        let html = '<div class="calendar-header-row">';
        html += '<div class="calendar-header-cell time-col">Время</div>';
        for (let d = 0; d < 7; d++) {
            const date = new Date(calendarWeekStart);
            date.setDate(date.getDate() + d);
            const dateStr = formatDateStr(date);
            const isToday = dateStr === today;
            html += `<div class="calendar-header-cell ${isToday ? 'today' : ''}">
                <div class="day-name">${dayNames[d]}</div>
                <div class="day-num">${date.getDate()}</div>
            </div>`;
        }
        html += '</div>';

        // Body
        html += '<div class="calendar-body">';
        for (let h = workStart; h < workEnd; h++) {
            html += '<div class="calendar-row">';
            html += `<div class="calendar-time">${h}:00</div>`;

            for (let d = 0; d < 7; d++) {
                const date = new Date(calendarWeekStart);
                date.setDate(date.getDate() + d);
                const dateStr = formatDateStr(date);
                const key = `${dateStr}_${h}`;
                const slot = slotsMap[key];

                if (slot) {
                    const statusClass = slot.status === 'completed' ? 'slot-completed' :
                                       slot.status === 'cancelled' ? 'slot-cancelled' : '';
                    html += `<div class="calendar-cell has-slot" onclick="openSlot('${dateStr}', ${h}, ${slot.id})">`;
                    if (slot.pet) {
                        html += `<div class="calendar-slot ${statusClass}">
                            <div class="slot-pet">${slot.pet.name}</div>
                            <div class="slot-owner">${slot.pet.owner_name}</div>
                        </div>`;
                    } else {
                        html += `<div class="calendar-slot slot-free">Свободно</div>`;
                    }
                    html += '</div>';
                } else {
                    html += `<div class="calendar-cell" onclick="openSlot('${dateStr}', ${h}, null)"></div>`;
                }
            }
            html += '</div>';
        }
        html += '</div>';

        document.getElementById('calendarGrid').innerHTML = html;
    } catch (e) {
        console.error('Calendar error:', e);
    }
}

function calendarPrev() {
    calendarWeekStart.setDate(calendarWeekStart.getDate() - 7);
    loadCalendar();
}

function calendarNext() {
    calendarWeekStart.setDate(calendarWeekStart.getDate() + 7);
    loadCalendar();
}

function calendarToday() {
    calendarWeekStart = getMonday(new Date());
    loadCalendar();
}

async function openSlot(dateStr, hour, slotId) {
    await loadPetSelect();

    document.getElementById('slotDate').value = dateStr;
    document.getElementById('slotHour').value = hour;
    document.getElementById('slotModalTitle').textContent = `${dateStr} — ${hour}:00`;

    if (slotId) {
        document.getElementById('slotEditId').value = slotId;
        document.getElementById('btnDeleteSlot').style.display = 'inline-flex';

        // Find slot data from calendar
        try {
            const resp = await fetch(`/api/calendar?week=${dateStr}`);
            const data = await resp.json();
            const slot = data.slots.find(s => s.id === slotId);
            if (slot) {
                document.getElementById('slotPetSelect').value = slot.pet ? slot.pet.id : '';
                document.getElementById('slotNotes').value = slot.notes || '';
            }
        } catch (e) {}
    } else {
        document.getElementById('slotEditId').value = '';
        document.getElementById('slotPetSelect').value = '';
        document.getElementById('slotNotes').value = '';
        document.getElementById('btnDeleteSlot').style.display = 'none';
    }

    showModal('calendarSlotModal');
}

async function saveSlot() {
    const editId = document.getElementById('slotEditId').value;
    const data = {
        date: document.getElementById('slotDate').value,
        hour: parseInt(document.getElementById('slotHour').value),
        pet_id: parseInt(document.getElementById('slotPetSelect').value) || null,
        notes: document.getElementById('slotNotes').value
    };

    try {
        const url = editId ? `/api/calendar/${editId}` : '/api/calendar';
        const method = editId ? 'PUT' : 'POST';
        const resp = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (resp.ok) {
            showToast(editId ? 'Запись обновлена' : 'Запись создана');
            closeModal('calendarSlotModal');
            loadCalendar();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Ошибка', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

async function deleteSlot() {
    const slotId = document.getElementById('slotEditId').value;
    if (!slotId) return;
    if (!confirm('Удалить запись?')) return;

    try {
        const resp = await fetch(`/api/calendar/${slotId}`, { method: 'DELETE' });
        if (resp.ok) {
            showToast('Запись удалена');
            closeModal('calendarSlotModal');
            loadCalendar();
        }
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}

// ============ TEMPLATES ============
async function loadCategories() {
    try {
        const resp = await fetch('/api/templates/categories');
        const categories = await resp.json();

        const el = document.getElementById('categoriesList');
        let html = `<div class="category-item ${!selectedCategoryId ? 'active' : ''}" onclick="filterByCategory(null)">📁 Все шаблоны</div>`;
        html += categories.map(c => `
            <div class="category-item ${selectedCategoryId === c.id ? 'active' : ''}" onclick="filterByCategory(${c.id})">
                📂 ${c.name} <span style="color:#aaa;font-size:12px">(${c.templates_count})</span>
            </div>
        `).join('');
        el.innerHTML = html;

        // Update category selects
        const catSelects = ['templateCategory', 'categoryParent'];
        catSelects.forEach(selectId => {
            const sel = document.getElementById(selectId);
            if (sel) {
                sel.innerHTML = '<option value="">Без категории</option>' +
                    categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
            }
        });
    } catch (e) {
        console.error(e);
    }
}

function filterByCategory(categoryId) {
    selectedCategoryId = categoryId;
    loadCategories();
    loadTemplates();
}

async function loadTemplates(search = '') {
    try {
        let url = '/api/templates?';
        if (selectedCategoryId) url += `category_id=${selectedCategoryId}&`;
        if (search) url += `search=${encodeURIComponent(search)}&`;

        const resp = await fetch(url);
        allTemplates = await resp.json();
        const el = document.getElementById('templatesList');

        if (allTemplates.length === 0) {
            el.innerHTML = '<div class="empty-state"><div class="empty-icon">📝</div><div class="empty-title">Нет шаблонов</div></div>';
            return;
        }

        el.innerHTML = allTemplates.map(t => `
            <div class="template-card" onclick="editTemplate(${t.id})">
                <div class="template-title">${t.title}</div>
                <div class="template-preview">${t.content.substring(0, 100)}...</div>
                <div style="margin-top:8px">
                    <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteTemplate(${t.id})">🗑️</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}

function searchTemplates(query) {
    loadTemplates(query);
}

async function saveTemplate() {
    const editId = document.getElementById('templateEditId').value;
    const data = {
        category_id: parseInt(document.getElementById('templateCategory').value) || null,
        title: document.getElementById('templateTitle').value,
        content: document.getElementById('templateContent').value
    };

    if (!data.title || !data.content) {
        showToast('Название и содержание обязательны', 'error');
        return;
    }

    try {
        const url = editId ? `/api/templates/${editId}` : '/api/templates';
        const method = editId ? 'PUT' : 'POST';
        const resp = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (resp.ok) {
            showToast(editId ? 'Шаблон обновлён' : 'Шаблон создан');
            closeModal('templateModal');
            clearTemplateForm();
            loadTemplates();
            loadCategories();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Ошибка', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

async function editTemplate(id) {
    const template = allTemplates.find(t => t.id === id);
    if (!template) return;

    document.getElementById('templateEditId').value = template.id;
    document.getElementById('templateCategory').value = template.category_id || '';
    document.getElementById('templateTitle').value = template.title;
    document.getElementById('templateContent').value = template.content;
    document.getElementById('templateModalTitle').textContent = 'Редактировать шаблон';
    showModal('templateModal');
}

async function deleteTemplate(id) {
    if (!confirm('Удалить шаблон?')) return;
    try {
        const resp = await fetch(`/api/templates/${id}`, { method: 'DELETE' });
        if (resp.ok) {
            showToast('Шаблон удалён');
            loadTemplates();
            loadCategories();
        }
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}

function clearTemplateForm() {
    document.getElementById('templateEditId').value = '';
    document.getElementById('templateCategory').value = '';
    document.getElementById('templateTitle').value = '';
    document.getElementById('templateContent').value = '';
    document.getElementById('templateModalTitle').textContent = 'Новый шаблон';
}

// Template selector (in visit modal)
async function showTemplateSelector() {
    try {
        const resp = await fetch('/api/templates');
        allTemplates = await resp.json();
        renderTemplateSelector(allTemplates);
        showModal('templateSelectorModal');
    } catch (e) {
        showToast('Ошибка загрузки шаблонов', 'error');
    }
}

function renderTemplateSelector(templates) {
    const el = document.getElementById('templateSelectorList');
    if (templates.length === 0) {
        el.innerHTML = '<div class="empty-state"><div class="empty-title">Нет шаблонов</div></div>';
        return;
    }
    el.innerHTML = templates.map(t => `
        <div class="template-selector-item" onclick="insertTemplate(${t.id})">
            <div class="ts-title">${t.title}</div>
            <div class="ts-preview">${t.content.substring(0, 80)}...</div>
        </div>
    `).join('');
}

function filterTemplateSelector(query) {
    const filtered = allTemplates.filter(t =>
        t.title.toLowerCase().includes(query.toLowerCase()) ||
        t.content.toLowerCase().includes(query.toLowerCase())
    );
    renderTemplateSelector(filtered);
}

function insertTemplate(id) {
    const template = allTemplates.find(t => t.id === id);
    if (!template) return;

    const textarea = document.getElementById('visitRecommendations');
    const current = textarea.value;
    textarea.value = current ? current + '\n\n' + template.content : template.content;

    closeModal('templateSelectorModal');
    showToast('Шаблон вставлен');
}

// ============ CATEGORIES ============
async function saveCategory() {
    const editId = document.getElementById('categoryEditId').value;
    const data = {
        name: document.getElementById('categoryName').value,
        parent_id: parseInt(document.getElementById('categoryParent').value) || null
    };

    if (!data.name) {
        showToast('Название обязательно', 'error');
        return;
    }

    try {
        const url = editId ? `/api/templates/categories/${editId}` : '/api/templates/categories';
        const method = editId ? 'PUT' : 'POST';
        const resp = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (resp.ok) {
            showToast(editId ? 'Категория обновлена' : 'Категория создана');
            closeModal('categoryModal');
            document.getElementById('categoryEditId').value = '';
            document.getElementById('categoryName').value = '';
            loadCategories();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Ошибка', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

// ============ QUESTIONNAIRES ============
async function loadQuestionnaires() {
    try {
        const resp = await fetch('/api/questionnaires');
        const questionnaires = await resp.json();
        const el = document.getElementById('questionnairesList');

        if (questionnaires.length === 0) {
            el.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-title">Нет опросников</div><div class="empty-desc">Создайте опросник для клиентов</div></div>';
            return;
        }

        el.innerHTML = questionnaires.map(q => `
            <div class="data-card">
                <div class="data-card-info">
                    <div class="title">📋 ${q.title}</div>
                    <div class="subtitle">${q.description || ''} • Полей: ${q.fields_count}</div>
                    <div class="details">
                        ${q.is_active ? '🟢 Активен' : '🔴 Деактивирован'}
                        • Создан: ${q.created_at ? new Date(q.created_at).toLocaleDateString('ru-RU') : ''}
                    </div>
                    <div class="link-display">
                        <input type="text" value="${window.location.origin}/intake/${q.public_link}" readonly id="link_${q.id}">
                        <button onclick="copyLink('link_${q.id}')">📋 Копировать</button>
                    </div>
                </div>
                <div class="data-card-actions">
                    <button onclick="event.stopPropagation(); toggleQuestionnaire(${q.id}, ${!q.is_active})" title="${q.is_active ? 'Деактивировать' : 'Активировать'}">${q.is_active ? '⏸️' : '▶️'}</button>
                    <button onclick="event.stopPropagation(); deleteQuestionnaire(${q.id})" title="Удалить">🗑️</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}

function copyLink(inputId) {
    const input = document.getElementById(inputId);
    input.select();
    document.execCommand('copy');
    showToast('Ссылка скопирована!');
}

async function saveQuestionnaire() {
    const data = {
        title: document.getElementById('questionnaireName').value,
        description: document.getElementById('questionnaireDesc').value,
        fields: []
    };

    if (!data.title) {
        showToast('Название обязательно', 'error');
        return;
    }

    // Собираем кастомные поля
    document.querySelectorAll('#questionnaireFields .q-field-row').forEach((row, i) => {
        const label = row.querySelector('.q-field-label').value;
        const type = row.querySelector('.q-field-type').value;
        const required = row.querySelector('.q-field-required').checked;
        if (label) {
            data.fields.push({
                field_name: `custom_${i}`,
                field_label: label,
                field_type: type,
                is_required: required,
                sort_order: 100 + i
            });
        }
    });

    try {
        const resp = await fetch('/api/questionnaires', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (resp.ok) {
            showToast('Опросник создан');
            closeModal('questionnaireModal');
            document.getElementById('questionnaireName').value = '';
            document.getElementById('questionnaireDesc').value = '';
            document.getElementById('questionnaireFields').innerHTML = '';
            loadQuestionnaires();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Ошибка', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

function addQuestionnaireField() {
    const container = document.getElementById('questionnaireFields');
    const row = document.createElement('div');
    row.className = 'q-field-row';
    row.innerHTML = `
        <input type="text" class="q-field-label" placeholder="Название поля">
        <select class="q-field-type">
            <option value="text">Текст</option>
            <option value="textarea">Многострочный</option>
            <option value="number">Число</option>
            <option value="select">Выпадающий</option>
        </select>
        <label><input type="checkbox" class="q-field-required"> Обяз.</label>
        <button class="q-field-remove" onclick="this.parentElement.remove()">✕</button>
    `;
    container.appendChild(row);
}

async function toggleQuestionnaire(id, active) {
    try {
        const resp = await fetch(`/api/questionnaires/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: active })
        });
        if (resp.ok) {
            showToast(active ? 'Опросник активирован' : 'Опросник деактивирован');
            loadQuestionnaires();
        }
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}

async function deleteQuestionnaire(id) {
    if (!confirm('Удалить опросник?')) return;
    try {
        const resp = await fetch(`/api/questionnaires/${id}`, { method: 'DELETE' });
        if (resp.ok) {
            showToast('Опросник удалён');
            loadQuestionnaires();
        }
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}

function switchQTab(tab) {
    document.querySelectorAll('#page-questionnaires .tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('qFormsTab').classList.remove('active');
    document.getElementById('qResponsesTab').classList.remove('active');

    if (tab === 'forms') {
        document.querySelectorAll('#page-questionnaires .tab-btn')[0].classList.add('active');
        document.getElementById('qFormsTab').classList.add('active');
    } else {
        document.querySelectorAll('#page-questionnaires .tab-btn')[1].classList.add('active');
        document.getElementById('qResponsesTab').classList.add('active');
        loadIntakes();
    }
}

// ============ INTAKES ============
async function loadIntakes() {
    try {
        const resp = await fetch('/api/intake');
        const intakes = await resp.json();
        const el = document.getElementById('intakesList');

        if (intakes.length === 0) {
            el.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-title">Нет заполненных анкет</div></div>';
            return;
        }

        el.innerHTML = intakes.map(i => `
            <div class="data-card" onclick="viewIntake(${i.id})">
                <div class="data-card-info">
                    <div class="title">
                        ${i.pet_name} (${i.pet_species})
                        <span class="badge badge-${i.status}">${intakeStatusLabel(i.status)}</span>
                    </div>
                    <div class="subtitle">Владелец: ${i.owner_name} • ${i.owner_phone || ''}</div>
                    <div class="details">${i.created_at ? formatDate(i.created_at) : ''} • ${i.questionnaire_title}</div>
                </div>
                <div class="data-card-actions">
                    <button onclick="event.stopPropagation(); deleteIntake(${i.id})" title="Удалить">🗑️</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}

function intakeStatusLabel(status) {
    const map = { new: 'Новая', reviewed: 'Просмотрена', converted: 'Конвертирована' };
    return map[status] || status;
}

async function viewIntake(id) {
    currentIntakeId = id;
    try {
        const resp = await fetch(`/api/intake/${id}`);
        if (!resp.ok) return;
        const intake = await resp.json();

        let html = '<div class="intake-detail">';
        html += '<div class="intake-section"><h4>👤 Владелец</h4>';
        html += `<div class="intake-row"><span class="intake-label">ФИО</span><span class="intake-value">${intake.owner_name}</span></div>`;
        html += `<div class="intake-row"><span class="intake-label">Телефон</span><span class="intake-value">${intake.owner_phone || '—'}</span></div>`;
        html += `<div class="intake-row"><span class="intake-label">Email</span><span class="intake-value">${intake.owner_email || '—'}</span></div>`;
        html += '</div>';

        html += '<div class="intake-section"><h4>🐾 Питомец</h4>';
        html += `<div class="intake-row"><span class="intake-label">Кличка</span><span class="intake-value">${intake.pet_name}</span></div>`;
        html += `<div class="intake-row"><span class="intake-label">Вид</span><span class="intake-value">${intake.pet_species}</span></div>`;
        html += `<div class="intake-row"><span class="intake-label">Порода</span><span class="intake-value">${intake.pet_breed || '—'}</span></div>`;
        html += `<div class="intake-row"><span class="intake-label">Возраст</span><span class="intake-value">${intake.pet_age || '—'}</span></div>`;
        html += '</div>';

        if (intake.answers && intake.answers.length > 0) {
            html += '<div class="intake-section"><h4>📝 Ответы</h4>';
            intake.answers.forEach(a => {
                html += `<div class="intake-row"><span class="intake-label">${a.field_name}</span><span class="intake-value">${a.value || '—'}</span></div>`;
            });
            html += '</div>';
        }

        html += '</div>';

        document.getElementById('intakeViewBody').innerHTML = html;

        // Show/hide convert button
        const btnConvert = document.getElementById('btnConvertIntake');
        if (intake.status === 'converted') {
            btnConvert.style.display = 'none';
        } else {
            btnConvert.style.display = 'inline-flex';
        }

        // Mark as reviewed
        if (intake.status === 'new') {
            await fetch(`/api/intake/${id}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'reviewed' })
            });
        }

        showModal('intakeViewModal');
    } catch (e) {
        showToast('Ошибка загрузки', 'error');
    }
}

async function convertIntake() {
    if (!currentIntakeId) return;
    try {
        const resp = await fetch(`/api/intake/${currentIntakeId}/convert`, { method: 'POST' });
        if (resp.ok) {
            const data = await resp.json();
            showToast(`Создан пациент: ${data.pet.name}`);
            closeModal('intakeViewModal');
            loadIntakes();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Ошибка', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

async function deleteIntake(id) {
    if (!confirm('Удалить анкету?')) return;
    try {
        const resp = await fetch(`/api/intake/${id}`, { method: 'DELETE' });
        if (resp.ok) {
            showToast('Анкета удалена');
            loadIntakes();
        }
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}

// ============ REMINDERS ============
async function loadReminders() {
    try {
        const date = document.getElementById('reminderDateFilter').value;
        const isDone = document.getElementById('reminderDoneFilter').value;
        let url = '/api/reminders?';
        if (date) url += `date=${date}&`;
        if (isDone !== '') url += `is_done=${isDone}&`;

        const resp = await fetch(url);
        const reminders = await resp.json();
        const el = document.getElementById('remindersList');

        if (reminders.length === 0) {
            el.innerHTML = '<div class="empty-state"><div class="empty-icon">🔔</div><div class="empty-title">Нет напоминаний</div></div>';
            return;
        }

        el.innerHTML = reminders.map(r => `
            <div class="data-card" style="${r.is_done ? 'opacity:0.6' : ''}">
                <div class="data-card-info">
                    <div class="title">
                        ${r.is_done ? '✅' : '🔔'} ${r.title}
                        <span class="badge badge-${r.reminder_type}">${reminderTypeLabel(r.reminder_type)}</span>
                    </div>
                    <div class="subtitle">${r.description || ''}</div>
                    <div class="details">${r.remind_date ? formatDate(r.remind_date) : ''}</div>
                </div>
                <div class="data-card-actions">
                    ${!r.is_done ? `<button onclick="event.stopPropagation(); markReminderDone(${r.id})" title="Выполнено">✅</button>` : ''}
                    <button onclick="event.stopPropagation(); editReminder(${r.id}, '${r.title}', '${(r.description || '').replace(/'/g, "\\'")}', '${r.remind_date || ''}', '${r.reminder_type}')" title="Редактировать">✏️</button>
                    <button onclick="event.stopPropagation(); deleteReminder(${r.id})" title="Удалить">🗑️</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}

function reminderTypeLabel(type) {
    const map = { custom: 'Своё', follow_up: 'Повторный визит', vaccination: 'Вакцинация' };
    return map[type] || type;
}

async function saveReminder() {
    const editId = document.getElementById('reminderEditId').value;
    const data = {
        title: document.getElementById('reminderTitle').value,
        description: document.getElementById('reminderDesc').value,
        remind_date: document.getElementById('reminderDate').value,
        reminder_type: document.getElementById('reminderType').value
    };

    if (!data.title || !data.remind_date) {
        showToast('Заголовок и дата обязательны', 'error');
        return;
    }

    try {
        const url = editId ? `/api/reminders/${editId}` : '/api/reminders';
        const method = editId ? 'PUT' : 'POST';
        const resp = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (resp.ok) {
            showToast(editId ? 'Напоминание обновлено' : 'Напоминание создано');
            closeModal('reminderModal');
            clearReminderForm();
            loadReminders();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Ошибка', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

function editReminder(id, title, desc, date, type) {
    document.getElementById('reminderEditId').value = id;
    document.getElementById('reminderTitle').value = title;
    document.getElementById('reminderDesc').value = desc;
    document.getElementById('reminderType').value = type;
    if (date) {
        const dt = new Date(date);
        const local = new Date(dt.getTime() - dt.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
        document.getElementById('reminderDate').value = local;
    }
    document.getElementById('reminderModalTitle').textContent = 'Редактировать напоминание';
    showModal('reminderModal');
}

async function markReminderDone(id) {
    try {
        const resp = await fetch(`/api/reminders/${id}/done`, { method: 'PUT' });
        if (resp.ok) {
            showToast('Отмечено как выполнено');
            loadReminders();
        }
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}

async function deleteReminder(id) {
    if (!confirm('Удалить напоминание?')) return;
    try {
        const resp = await fetch(`/api/reminders/${id}`, { method: 'DELETE' });
        if (resp.ok) {
            showToast('Напоминание удалено');
            loadReminders();
        }
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}

function clearReminderForm() {
    document.getElementById('reminderEditId').value = '';
    document.getElementById('reminderTitle').value = '';
    document.getElementById('reminderDesc').value = '';
    document.getElementById('reminderDate').value = '';
    document.getElementById('reminderType').value = 'custom';
    document.getElementById('reminderModalTitle').textContent = 'Новое напоминание';
}

// ============ SETTINGS ============
async function loadSettings() {
    try {
        const resp = await fetch('/api/settings');
        if (!resp.ok) return;
        const s = await resp.json();

        document.getElementById('setClinicName').value = s.clinic_name || '';
        document.getElementById('setClinicAddress').value = s.clinic_address || '';
        document.getElementById('setClinicPhone').value = s.clinic_phone || '';
        document.getElementById('setWorkStart').value = s.work_start_hour || 9;
        document.getElementById('setWorkEnd').value = s.work_end_hour || 21;
        document.getElementById('setDocHeader').value = s.doc_header || '';
        document.getElementById('setDocDoctorName').value = s.doc_doctor_name || '';
        document.getElementById('setDocDoctorContacts').value = s.doc_doctor_contacts || '';
        document.getElementById('setDocFooter').value = s.doc_footer || '';

        // Load doctors list if admin
        if (currentDoctor && currentDoctor.is_admin) {
            loadDoctorsList();
        }
    } catch (e) {
        console.error(e);
    }
}

async function saveSettings() {
    const data = {
        clinic_name: document.getElementById('setClinicName').value,
        clinic_address: document.getElementById('setClinicAddress').value,
        clinic_phone: document.getElementById('setClinicPhone').value,
        work_start_hour: parseInt(document.getElementById('setWorkStart').value),
        work_end_hour: parseInt(document.getElementById('setWorkEnd').value),
        doc_header: document.getElementById('setDocHeader').value,
        doc_doctor_name: document.getElementById('setDocDoctorName').value,
        doc_doctor_contacts: document.getElementById('setDocDoctorContacts').value,
        doc_footer: document.getElementById('setDocFooter').value
    };

    try {
        const resp = await fetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (resp.ok) {
            showToast('Настройки сохранены');
        } else {
            showToast('Ошибка сохранения', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

// ============ DOCTORS (admin) ============
async function loadDoctorsList() {
    try {
        const resp = await fetch('/api/doctors');
        if (!resp.ok) return;
        const doctors = await resp.json();
        const el = document.getElementById('doctorsList');

        el.innerHTML = doctors.map(d => `
            <div class="data-card">
                <div class="data-card-info">
                    <div class="title">👨‍⚕️ ${d.full_name} ${d.is_admin ? '(Админ)' : ''}</div>
                    <div class="subtitle">${d.email} • ${d.username}</div>
                    <div class="details">${d.specialization || ''} ${d.phone ? '• ' + d.phone : ''}</div>
                </div>
                <div class="data-card-actions">
                    ${!d.is_admin ? `<button onclick="toggleDoctorActive(${d.id}, ${!d.is_active})" title="${d.is_active ? 'Деактивировать' : 'Активировать'}">${d.is_active ? '⏸️' : '▶️'}</button>` : ''}
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}

async function saveDoctor() {
    const data = {
        full_name: document.getElementById('newDoctorName').value,
        email: document.getElementById('newDoctorEmail').value,
        username: document.getElementById('newDoctorUsername').value,
        password: document.getElementById('newDoctorPassword').value,
        phone: document.getElementById('newDoctorPhone').value,
        specialization: document.getElementById('newDoctorSpec').value
    };

    if (!data.full_name || !data.email || !data.username || !data.password) {
        showToast('Заполните обязательные поля', 'error');
        return;
    }

    try {
        const resp = await fetch('/api/doctors', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (resp.ok) {
            showToast('Врач создан');
            closeModal('doctorModal');
            document.getElementById('newDoctorName').value = '';
            document.getElementById('newDoctorEmail').value = '';
            document.getElementById('newDoctorUsername').value = '';
            document.getElementById('newDoctorPassword').value = '';
            document.getElementById('newDoctorPhone').value = '';
            document.getElementById('newDoctorSpec').value = '';
            loadDoctorsList();
        } else {
            const err = await resp.json();
            showToast(err.detail || 'Ошибка', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}

async function toggleDoctorActive(id, active) {
    try {
        const resp = await fetch(`/api/doctors/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: active })
        });
        if (resp.ok) {
            showToast(active ? 'Врач активирован' : 'Врач деактивирован');
            loadDoctorsList();
        }
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}

// ============ VISIT FORM EDITOR ============
function showVisitFormEditor() {
    loadVisitFormConfig();
    showModal('visitFormEditorModal');
}

async function loadVisitFormConfig() {
    try {
        const resp = await fetch('/api/visit-forms');
        const configs = await resp.json();
        const config = configs[0];

        if (config && config.fields) {
            const container = document.getElementById('visitFormFields');
            container.innerHTML = config.fields.map((f, i) => createVisitFormFieldRow(f, i)).join('');
        }
    } catch (e) {
        console.error(e);
    }
}

function createVisitFormFieldRow(field, index) {
    return `
        <div class="vf-field-row" data-index="${index}">
            <input type="text" class="vf-name" value="${field.field_name || ''}" placeholder="Имя поля">
            <input type="text" class="vf-label" value="${field.field_label || ''}" placeholder="Подпись">
            <select class="vf-type">
                <option value="textarea" ${field.field_type === 'textarea' ? 'selected' : ''}>Текст</option>
                <option value="number" ${field.field_type === 'number' ? 'selected' : ''}>Число</option>
                <option value="text" ${field.field_type === 'text' ? 'selected' : ''}>Строка</option>
            </select>
            <label><input type="checkbox" class="vf-visible" ${field.is_visible ? 'checked' : ''}> Видимое</label>
            <label><input type="checkbox" class="vf-required" ${field.is_required ? 'checked' : ''}> Обяз.</label>
            <button class="vf-field-remove" onclick="this.parentElement.remove()">✕</button>
        </div>
    `;
}

function addVisitFormField() {
    const container = document.getElementById('visitFormFields');
    const index = container.children.length;
    const html = createVisitFormFieldRow({
        field_name: '',
        field_label: '',
        field_type: 'textarea',
        is_visible: true,
        is_required: false
    }, index);
    container.insertAdjacentHTML('beforeend', html);
}

async function saveVisitForm() {
    const fields = [];
    document.querySelectorAll('#visitFormFields .vf-field-row').forEach((row, i) => {
        fields.push({
            field_name: row.querySelector('.vf-name').value,
            field_label: row.querySelector('.vf-label').value,
            field_type: row.querySelector('.vf-type').value,
            is_visible: row.querySelector('.vf-visible').checked,
            is_required: row.querySelector('.vf-required').checked,
            sort_order: i
        });
    });

    try {
        // Get existing config or create new
        const listResp = await fetch('/api/visit-forms');
        const configs = await listResp.json();

        let url, method;
        if (configs.length > 0) {
            url = `/api/visit-forms/${configs[0].id}`;
            method = 'PUT';
        } else {
            url = '/api/visit-forms';
            method = 'POST';
        }

        const resp = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: 'Стандартная форма', fields })
        });

        if (resp.ok) {
            showToast('Форма приёма сохранена');
            closeModal('visitFormEditorModal');
        } else {
            showToast('Ошибка сохранения', 'error');
        }
    } catch (e) {
        showToast('Ошибка сети', 'error');
    }
}
