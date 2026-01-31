/**
 * Expense Tracker - Full Featured Frontend Application
 */

const API_BASE_URL = '';

// State
let accessToken = localStorage.getItem('accessToken');
let refreshToken = localStorage.getItem('refreshToken');
let currentUser = null;
let currentPage = 1;
let totalPages = 1;
let expenseToDelete = null;
let editingExpenseId = null;

// Charts
let categoryChart = null;
let monthlyChart = null;
let dailyChart = null;

const CHART_COLORS = [
    '#58a6ff', '#7ee787', '#d29922', '#f85149', '#a371f7',
    '#79c0ff', '#56d364', '#e3b341', '#ff7b72', '#bc8cff'
];

// DOM Elements
const authSection = document.getElementById('auth-section');
const appSection = document.getElementById('app-section');
const loginFormContainer = document.getElementById('login-form-container');
const registerFormContainer = document.getElementById('register-form-container');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const expenseForm = document.getElementById('expense-form');
const userDisplay = document.getElementById('user-display');
const logoutBtn = document.getElementById('logout-btn');
const exportBtn = document.getElementById('export-btn');
const themeToggle = document.getElementById('theme-toggle');

// Filters
const filterSearch = document.getElementById('filter-search');
const filterCategory = document.getElementById('filter-category');
const filterStartDate = document.getElementById('filter-start-date');
const filterEndDate = document.getElementById('filter-end-date');
const sortOrder = document.getElementById('sort-order');

// Pagination
const prevPageBtn = document.getElementById('prev-page');
const nextPageBtn = document.getElementById('next-page');
const pageInfo = document.getElementById('page-info');
const pagination = document.getElementById('pagination');

// Modals
const deleteModal = document.getElementById('delete-modal');
const importModal = document.getElementById('import-modal');

// Tabs
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    document.getElementById('date').valueAsDate = new Date();
    document.getElementById('recurring-start').valueAsDate = new Date();
    initTheme();
    
    // Auth switches
    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        loginFormContainer.hidden = true;
        registerFormContainer.hidden = false;
    });
    
    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        registerFormContainer.hidden = true;
        loginFormContainer.hidden = false;
    });
    
    // Forms
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    expenseForm.addEventListener('submit', handleExpenseSubmit);
    logoutBtn.addEventListener('click', handleLogout);
    exportBtn.addEventListener('click', handleExport);
    
    // Filters with debounce for search
    let searchTimeout;
    filterSearch.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => { currentPage = 1; loadExpenses(); }, 300);
    });
    filterCategory.addEventListener('change', () => { currentPage = 1; loadExpenses(); });
    filterStartDate.addEventListener('change', () => { currentPage = 1; loadExpenses(); });
    filterEndDate.addEventListener('change', () => { currentPage = 1; loadExpenses(); });
    sortOrder.addEventListener('change', () => { currentPage = 1; loadExpenses(); });
    
    // Pagination
    prevPageBtn.addEventListener('click', () => { currentPage--; loadExpenses(); });
    nextPageBtn.addEventListener('click', () => { currentPage++; loadExpenses(); });
    
    // Delete Modal
    document.getElementById('cancel-delete').addEventListener('click', closeDeleteModal);
    document.getElementById('confirm-delete').addEventListener('click', confirmDelete);
    
    // Tab navigation
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Theme toggle
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Cancel edit
    document.getElementById('cancel-edit-btn').addEventListener('click', cancelEdit);
    
    // Import
    document.getElementById('import-file').addEventListener('change', handleImportFile);
    document.getElementById('cancel-import').addEventListener('click', () => importModal.hidden = true);
    document.getElementById('confirm-import').addEventListener('click', confirmImport);
    
    // Budget form
    document.getElementById('budget-form').addEventListener('submit', handleBudgetSubmit);
    
    // Recurring form
    document.getElementById('recurring-form').addEventListener('submit', handleRecurringSubmit);
    document.getElementById('recurring-frequency').addEventListener('change', updateRecurringOptions);
    document.getElementById('process-recurring-btn').addEventListener('click', processRecurring);
    
    // Check auth
    if (accessToken) {
        await checkAuth();
    } else {
        showAuthSection();
    }
}

// === Theme ===
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    if (accessToken) saveThemeToServer(newTheme);
}

async function saveThemeToServer(theme) {
    try {
        await fetchWithAuth('/users/me/theme', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme })
        });
    } catch (e) { console.error('Theme save failed', e); }
}

// === Tabs ===
function switchTab(tabName) {
    tabBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabName));
    tabContents.forEach(content => content.classList.toggle('active', content.id === `${tabName}-tab`));
    
    if (tabName === 'analytics') loadAnalytics();
    if (tabName === 'budgets') loadBudgets();
    if (tabName === 'recurring') loadRecurring();
}

// === Auth ===
async function checkAuth() {
    try {
        const response = await fetchWithAuth('/users/me');
        if (response.ok) {
            currentUser = await response.json();
            showAppSection();
        } else {
            clearAuth();
            showAuthSection();
        }
    } catch (e) {
        clearAuth();
        showAuthSection();
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const btn = loginForm.querySelector('button');
    setButtonLoading(btn, true);
    
    const formData = new FormData(loginForm);
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: formData.get('username'),
                password: formData.get('password')
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            saveAuth(data.access_token, data.refresh_token);
            await checkAuth();
        } else {
            const error = await response.json();
            showMessage('login-message', error.detail || 'Login failed', true);
        }
    } catch (e) {
        showMessage('login-message', 'Network error', true);
    } finally {
        setButtonLoading(btn, false);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const btn = registerForm.querySelector('button');
    setButtonLoading(btn, true);
    
    const formData = new FormData(registerForm);
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: formData.get('email'),
                username: formData.get('username'),
                password: formData.get('password'),
                full_name: formData.get('full_name') || null
            })
        });
        
        if (response.ok) {
            showMessage('register-message', 'Account created! Please login.', false);
            registerForm.reset();
            setTimeout(() => {
                registerFormContainer.hidden = true;
                loginFormContainer.hidden = false;
            }, 1500);
        } else {
            const error = await response.json();
            showMessage('register-message', error.detail || 'Registration failed', true);
        }
    } catch (e) {
        showMessage('register-message', 'Network error', true);
    } finally {
        setButtonLoading(btn, false);
    }
}

function handleLogout() {
    clearAuth();
    currentUser = null;
    destroyCharts();
    showAuthSection();
}

function saveAuth(access, refresh) {
    accessToken = access;
    refreshToken = refresh;
    localStorage.setItem('accessToken', access);
    localStorage.setItem('refreshToken', refresh);
}

function clearAuth() {
    accessToken = null;
    refreshToken = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
}

async function fetchWithAuth(url, options = {}) {
    const headers = { ...options.headers, 'Authorization': `Bearer ${accessToken}` };
    let response = await fetch(`${API_BASE_URL}${url}`, { ...options, headers });
    
    if (response.status === 401 && refreshToken) {
        const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh?refresh_token=${refreshToken}`, { method: 'POST' });
        if (refreshResponse.ok) {
            const data = await refreshResponse.json();
            saveAuth(data.access_token, data.refresh_token);
            headers['Authorization'] = `Bearer ${accessToken}`;
            response = await fetch(`${API_BASE_URL}${url}`, { ...options, headers });
        } else {
            clearAuth();
            showAuthSection();
        }
    }
    return response;
}

// === UI ===
function showAuthSection() {
    authSection.hidden = false;
    appSection.hidden = true;
}

function showAppSection() {
    authSection.hidden = true;
    appSection.hidden = false;
    userDisplay.textContent = currentUser.full_name || currentUser.username;
    if (currentUser.theme) setTheme(currentUser.theme);
    loadExpenses();
    loadSummary();
}

function setButtonLoading(btn, loading) {
    btn.disabled = loading;
    const text = btn.querySelector('.btn-text');
    const load = btn.querySelector('.btn-loading');
    if (text) text.hidden = loading;
    if (load) load.hidden = !loading;
}

function showMessage(elementId, message, isError) {
    const el = document.getElementById(elementId);
    el.textContent = message;
    el.className = `form-message ${isError ? 'error' : 'success'}`;
    el.hidden = false;
    setTimeout(() => { el.hidden = true; }, 5000);
}

// === Expenses ===
async function handleExpenseSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    setButtonLoading(btn, true);
    
    const formData = new FormData(expenseForm);
    const tags = formData.get('tags') ? formData.get('tags').split(',').map(t => t.trim()).filter(t => t) : [];
    
    const expenseData = {
        amount: parseFloat(formData.get('amount')),
        currency: formData.get('currency') || 'INR',
        category: formData.get('category'),
        description: formData.get('description'),
        date: new Date(formData.get('date')).toISOString(),
        tags: tags,
        notes: formData.get('notes') || null,
        idempotency_key: editingExpenseId ? null : generateUUID()
    };
    
    try {
        const url = editingExpenseId ? `/expenses/${editingExpenseId}` : '/expenses';
        const method = editingExpenseId ? 'PATCH' : 'POST';
        
        const response = await fetchWithAuth(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(expenseData)
        });
        
        if (response.ok) {
            showMessage('form-message', editingExpenseId ? 'Expense updated!' : 'Expense added!', false);
            resetExpenseForm();
            loadExpenses();
            loadSummary();
        } else {
            const error = await response.json();
            showMessage('form-message', error.detail || 'Failed', true);
        }
    } catch (e) {
        showMessage('form-message', 'Network error', true);
    } finally {
        setButtonLoading(btn, false);
    }
}

function resetExpenseForm() {
    expenseForm.reset();
    document.getElementById('date').valueAsDate = new Date();
    document.getElementById('edit-expense-id').value = '';
    document.getElementById('form-title').textContent = 'New Expense';
    document.getElementById('submit-btn').querySelector('.btn-text').textContent = 'Add Expense';
    document.getElementById('cancel-edit-btn').hidden = true;
    editingExpenseId = null;
}

function cancelEdit() {
    resetExpenseForm();
}

async function editExpense(id) {
    try {
        const response = await fetchWithAuth(`/expenses/${id}`);
        if (response.ok) {
            const expense = await response.json();
            editingExpenseId = id;
            
            document.getElementById('edit-expense-id').value = id;
            document.getElementById('amount').value = expense.amount;
            document.getElementById('currency').value = expense.currency || 'INR';
            document.getElementById('category').value = expense.category;
            document.getElementById('description').value = expense.description;
            document.getElementById('date').value = expense.date.split('T')[0];
            document.getElementById('tags').value = (expense.tags || []).join(', ');
            document.getElementById('notes').value = expense.notes || '';
            
            document.getElementById('form-title').textContent = 'Edit Expense';
            document.getElementById('submit-btn').querySelector('.btn-text').textContent = 'Update Expense';
            document.getElementById('cancel-edit-btn').hidden = false;
            
            document.getElementById('expense-form').scrollIntoView({ behavior: 'smooth' });
        }
    } catch (e) {
        console.error('Failed to load expense for edit', e);
    }
}

async function loadExpenses() {
    setListState('loading');
    
    const params = new URLSearchParams();
    if (filterSearch.value) params.append('search', filterSearch.value);
    if (filterCategory.value) params.append('category', filterCategory.value);
    if (filterStartDate.value) params.append('start_date', filterStartDate.value);
    if (filterEndDate.value) params.append('end_date', filterEndDate.value);
    if (sortOrder.value) params.append('sort', sortOrder.value);
    params.append('page', currentPage);
    params.append('page_size', 15);
    
    try {
        const response = await fetchWithAuth(`/expenses?${params}`);
        if (response.ok) {
            const data = await response.json();
            renderExpenses(data);
        } else {
            setListState('empty');
        }
    } catch (e) {
        setListState('empty');
    }
}

function renderExpenses(data) {
    document.getElementById('total-amount').textContent = formatCurrency(data.total);
    document.getElementById('total-count').textContent = `${data.count} expense${data.count !== 1 ? 's' : ''}`;
    
    totalPages = data.total_pages;
    pageInfo.textContent = `Page ${data.page} of ${totalPages}`;
    prevPageBtn.disabled = data.page <= 1;
    nextPageBtn.disabled = data.page >= totalPages;
    pagination.hidden = totalPages <= 1;
    
    if (data.expenses.length === 0) {
        setListState('empty');
        return;
    }
    
    const tbody = document.getElementById('expenses-body');
    tbody.innerHTML = data.expenses.map(exp => `
        <tr>
            <td class="expense-date">${formatDate(exp.date)}</td>
            <td><span class="expense-category">${escapeHtml(exp.category)}</span></td>
            <td class="expense-description" title="${escapeHtml(exp.description)}">${escapeHtml(exp.description)}</td>
            <td class="expense-tags">${(exp.tags || []).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}</td>
            <td class="expense-amount">${formatCurrencyWithCode(exp.amount, exp.currency)}</td>
            <td class="expense-actions">
                <button class="btn btn-secondary btn-icon btn-sm" onclick="editExpense(${exp.id})" title="Edit">✎</button>
                <button class="btn btn-secondary btn-icon btn-sm" onclick="openDeleteModal(${exp.id})" title="Delete">✕</button>
            </td>
        </tr>
    `).join('');
    
    setListState('data');
}

async function loadSummary() {
    try {
        const response = await fetchWithAuth('/expenses/summary');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('summary-total').textContent = formatCurrency(data.total_expenses);
            document.getElementById('summary-count').textContent = data.expense_count;
            document.getElementById('summary-avg').textContent = formatCurrency(data.average_expense);
            
            const now = new Date();
            const monthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
            document.getElementById('summary-month').textContent = formatCurrency(data.monthly_totals[monthKey] || 0);
        }
    } catch (e) { console.error('Summary load failed', e); }
}

function openDeleteModal(id) {
    expenseToDelete = id;
    deleteModal.hidden = false;
}

function closeDeleteModal() {
    expenseToDelete = null;
    deleteModal.hidden = true;
}

async function confirmDelete() {
    if (!expenseToDelete) return;
    try {
        const response = await fetchWithAuth(`/expenses/${expenseToDelete}`, { method: 'DELETE' });
        if (response.ok) {
            closeDeleteModal();
            loadExpenses();
            loadSummary();
        }
    } catch (e) { console.error('Delete failed', e); }
}

async function handleExport() {
    const params = new URLSearchParams();
    if (filterCategory.value) params.append('category', filterCategory.value);
    if (filterStartDate.value) params.append('start_date', filterStartDate.value);
    if (filterEndDate.value) params.append('end_date', filterEndDate.value);
    
    try {
        const response = await fetchWithAuth(`/expenses/export?${params}`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'expenses.csv';
            a.click();
            window.URL.revokeObjectURL(url);
        }
    } catch (e) { console.error('Export failed', e); }
}

function setListState(state) {
    document.getElementById('loading-indicator').hidden = state !== 'loading';
    document.getElementById('empty-state').hidden = state !== 'empty';
    document.getElementById('expenses-table').hidden = state !== 'data';
}

// === Import ===
let importFileContent = null;

async function handleImportFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = async (event) => {
        importFileContent = event.target.result;
        
        // Preview
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetchWithAuth('/expenses/import/preview', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const preview = await response.json();
                renderImportPreview(preview);
                importModal.hidden = false;
            }
        } catch (e) { console.error('Import preview failed', e); }
    };
    reader.readAsText(file);
    e.target.value = '';
}

function renderImportPreview(preview) {
    const container = document.getElementById('import-preview');
    container.innerHTML = `
        <p><strong>Total rows:</strong> ${preview.total_rows} | <strong>Valid:</strong> ${preview.valid_rows} | <strong>Invalid:</strong> ${preview.invalid_rows}</p>
        <p><strong>Estimated total:</strong> ${formatCurrency(preview.estimated_total)}</p>
        ${preview.errors.length > 0 ? `<p style="color: var(--accent-danger);">Errors: ${preview.errors.map(e => `Row ${e.row_number}: ${e.error}`).join(', ')}</p>` : ''}
        <table>
            <thead><tr><th>Date</th><th>Category</th><th>Description</th><th>Amount</th></tr></thead>
            <tbody>
                ${preview.preview_data.slice(0, 10).map(row => `
                    <tr><td>${row.date}</td><td>${row.category}</td><td>${row.description}</td><td>${row.amount}</td></tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

async function confirmImport() {
    const fileInput = document.getElementById('import-file');
    const file = new File([importFileContent], 'import.csv', { type: 'text/csv' });
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetchWithAuth('/expenses/import', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            alert(`Imported ${result.success_count} expenses. ${result.error_count} errors.`);
            importModal.hidden = true;
            loadExpenses();
            loadSummary();
        }
    } catch (e) { console.error('Import failed', e); }
}

// === Budgets ===
async function loadBudgets() {
    try {
        const response = await fetchWithAuth('/budgets/overview');
        if (response.ok) {
            const data = await response.json();
            renderBudgetAlerts(data.alerts);
            renderBudgetsList(data.budgets);
        }
    } catch (e) { console.error('Budgets load failed', e); }
}

function renderBudgetAlerts(alerts) {
    const container = document.getElementById('budget-alerts');
    if (alerts.length === 0) {
        container.innerHTML = '<p class="empty-text">No budget alerts</p>';
        return;
    }
    container.innerHTML = alerts.map(a => `
        <div class="budget-alert ${a.severity}">
            <div class="budget-alert-icon">${a.severity === 'danger' ? '⚠' : '⚡'}</div>
            <div class="budget-alert-content">
                <div class="budget-alert-title">${escapeHtml(a.category)}</div>
                <div class="budget-alert-message">${a.message}</div>
            </div>
        </div>
    `).join('');
}

function renderBudgetsList(budgets) {
    const container = document.getElementById('budgets-list');
    if (budgets.length === 0) {
        container.innerHTML = '<p class="empty-text">No budgets set yet.</p>';
        return;
    }
    container.innerHTML = budgets.map(b => {
        const pct = Math.min(b.percentage_used, 100);
        const barClass = b.is_over_budget ? 'danger' : b.is_alert ? 'warning' : 'safe';
        return `
            <div class="budget-item">
                <div class="budget-item-header">
                    <span class="budget-item-category">${escapeHtml(b.budget.category)}</span>
                    <span class="budget-item-limit">${formatCurrency(b.budget.monthly_limit)}/mo</span>
                </div>
                <div class="budget-progress">
                    <div class="budget-progress-bar ${barClass}" style="width: ${pct}%"></div>
                </div>
                <div class="budget-item-stats">
                    <span>Spent: ${formatCurrency(b.current_spending)}</span>
                    <span>Remaining: ${formatCurrency(b.remaining)}</span>
                    <span>${b.percentage_used}%</span>
                </div>
            </div>
        `;
    }).join('');
}

async function handleBudgetSubmit(e) {
    e.preventDefault();
    const category = document.getElementById('budget-category').value;
    const limit = parseFloat(document.getElementById('budget-limit').value);
    const alert = parseInt(document.getElementById('budget-alert').value);
    
    try {
        const response = await fetchWithAuth('/budgets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, monthly_limit: limit, alert_threshold: alert })
        });
        
        if (response.ok) {
            showMessage('budget-message', 'Budget set!', false);
            document.getElementById('budget-form').reset();
            loadBudgets();
        } else {
            showMessage('budget-message', 'Failed to set budget', true);
        }
    } catch (e) { showMessage('budget-message', 'Network error', true); }
}

// === Recurring ===
function updateRecurringOptions() {
    const freq = document.getElementById('recurring-frequency').value;
    document.getElementById('day-of-week-group').hidden = freq !== 'weekly';
    document.getElementById('day-of-month-group').hidden = freq === 'daily' || freq === 'weekly';
}

async function loadRecurring() {
    try {
        const response = await fetchWithAuth('/recurring');
        if (response.ok) {
            const data = await response.json();
            renderRecurringList(data.items);
        }
    } catch (e) { console.error('Recurring load failed', e); }
}

function renderRecurringList(items) {
    const container = document.getElementById('recurring-list');
    if (items.length === 0) {
        container.innerHTML = '<p class="empty-text">No recurring expenses set up.</p>';
        return;
    }
    container.innerHTML = items.map(r => `
        <div class="recurring-item ${r.is_active ? '' : 'inactive'}">
            <div class="recurring-item-info">
                <div class="recurring-item-desc">${escapeHtml(r.description)}</div>
                <div class="recurring-item-details">${r.category} • ${r.frequency} • Next: ${r.next_run_date}</div>
            </div>
            <span class="recurring-item-amount">${formatCurrency(r.amount)}</span>
            <div class="recurring-item-actions">
                <button class="btn btn-secondary btn-sm" onclick="toggleRecurring(${r.id})">${r.is_active ? 'Pause' : 'Resume'}</button>
                <button class="btn btn-danger btn-sm" onclick="deleteRecurring(${r.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

async function handleRecurringSubmit(e) {
    e.preventDefault();
    const freq = document.getElementById('recurring-frequency').value;
    
    const data = {
        amount: parseFloat(document.getElementById('recurring-amount').value),
        category: document.getElementById('recurring-category').value,
        description: document.getElementById('recurring-description').value,
        frequency: freq,
        start_date: document.getElementById('recurring-start').value,
        day_of_week: freq === 'weekly' ? parseInt(document.getElementById('recurring-dow').value) : null,
        day_of_month: ['monthly', 'yearly'].includes(freq) ? parseInt(document.getElementById('recurring-dom').value) : null,
        month_of_year: freq === 'yearly' ? new Date().getMonth() + 1 : null
    };
    
    try {
        const response = await fetchWithAuth('/recurring', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showMessage('recurring-message', 'Recurring expense added!', false);
            document.getElementById('recurring-form').reset();
            document.getElementById('recurring-start').valueAsDate = new Date();
            loadRecurring();
        } else {
            const error = await response.json();
            showMessage('recurring-message', error.detail || 'Failed', true);
        }
    } catch (e) { showMessage('recurring-message', 'Network error', true); }
}

async function toggleRecurring(id) {
    try {
        await fetchWithAuth(`/recurring/${id}/toggle`, { method: 'POST' });
        loadRecurring();
    } catch (e) { console.error('Toggle failed', e); }
}

async function deleteRecurring(id) {
    if (!confirm('Delete this recurring expense?')) return;
    try {
        await fetchWithAuth(`/recurring/${id}`, { method: 'DELETE' });
        loadRecurring();
    } catch (e) { console.error('Delete failed', e); }
}

async function processRecurring() {
    try {
        const response = await fetchWithAuth('/recurring/process', { method: 'POST' });
        if (response.ok) {
            const result = await response.json();
            alert(`Processed ${result.processed_count} recurring expenses.`);
            loadExpenses();
            loadSummary();
            loadRecurring();
        }
    } catch (e) { console.error('Process failed', e); }
}

// === Analytics ===
async function loadAnalytics() {
    try {
        const response = await fetchWithAuth('/expenses/analytics?months=12');
        if (response.ok) {
            const data = await response.json();
            renderAnalytics(data);
        }
    } catch (e) { console.error('Analytics load failed', e); }
}

function renderAnalytics(data) {
    document.getElementById('analytics-total').textContent = formatCurrency(data.total_expenses);
    document.getElementById('analytics-lowest').textContent = formatCurrency(data.lowest_expense);
    document.getElementById('analytics-highest').textContent = formatCurrency(data.highest_expense);
    document.getElementById('analytics-avg').textContent = formatCurrency(data.average_expense);
    
    document.getElementById('mom-current').textContent = formatCurrency(data.current_month_total);
    document.getElementById('mom-previous').textContent = formatCurrency(data.previous_month_total);
    
    const changeEl = document.getElementById('mom-change');
    const change = parseFloat(data.month_over_month_change);
    changeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(1)}%`;
    changeEl.className = `mom-value ${change > 0 ? 'negative' : change < 0 ? 'positive' : 'neutral'}`;
    
    renderCategoryChart(data.categories);
    renderMonthlyChart(data.monthly_data);
    renderDailyChart(data.daily_data);
    renderCategoryTable(data.categories);
}

function renderCategoryChart(categories) {
    const ctx = document.getElementById('category-chart').getContext('2d');
    if (categoryChart) categoryChart.destroy();
    if (categories.length === 0) return;
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories.map(c => c.category),
            datasets: [{ data: categories.map(c => parseFloat(c.total)), backgroundColor: CHART_COLORS.slice(0, categories.length), borderWidth: 0 }]
        },
        options: { responsive: true, maintainAspectRatio: false, cutout: '65%', plugins: { legend: { display: false } } }
    });
    
    document.getElementById('category-legend').innerHTML = categories.map((c, i) => `
        <div class="legend-item"><span class="legend-color" style="background: ${CHART_COLORS[i]}"></span><span>${escapeHtml(c.category)}</span></div>
    `).join('');
}

function renderMonthlyChart(monthlyData) {
    const ctx = document.getElementById('monthly-chart').getContext('2d');
    if (monthlyChart) monthlyChart.destroy();
    if (monthlyData.length === 0) return;
    
    monthlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: monthlyData.map(m => m.month),
            datasets: [{ data: monthlyData.map(m => parseFloat(m.total)), backgroundColor: 'rgba(88, 166, 255, 0.6)', borderRadius: 4 }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
}

function renderDailyChart(dailyData) {
    const ctx = document.getElementById('daily-chart').getContext('2d');
    if (dailyChart) dailyChart.destroy();
    if (dailyData.length === 0) return;
    
    dailyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dailyData.map(d => d.date.slice(5)),
            datasets: [{ data: dailyData.map(d => parseFloat(d.total)), borderColor: '#7ee787', backgroundColor: 'rgba(126, 231, 135, 0.1)', fill: true, tension: 0.3 }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
}

function renderCategoryTable(categories) {
    const tbody = document.getElementById('category-table-body');
    if (categories.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">No data</td></tr>';
        return;
    }
    tbody.innerHTML = categories.map((c, i) => `
        <tr>
            <td><span class="rank-badge ${i < 3 ? ['gold','silver','bronze'][i] : ''}">${i + 1}</span></td>
            <td>${escapeHtml(c.category)}</td>
            <td class="text-right" style="font-family:var(--font-mono)">${formatCurrency(c.total)}</td>
            <td class="text-right">${c.count}</td>
            <td class="text-right">${c.percentage}%</td>
            <td><div class="progress-bar"><div class="progress-fill" style="width:${c.percentage}%"></div></div></td>
        </tr>
    `).join('');
}

function destroyCharts() {
    if (categoryChart) { categoryChart.destroy(); categoryChart = null; }
    if (monthlyChart) { monthlyChart.destroy(); monthlyChart = null; }
    if (dailyChart) { dailyChart.destroy(); dailyChart = null; }
}

// === Utilities ===
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 2 }).format(amount);
}

function formatCurrencyWithCode(amount, currency = 'INR') {
    const symbols = { INR: '₹', USD: '$', EUR: '€', GBP: '£', JPY: '¥' };
    return `${symbols[currency] || currency} ${parseFloat(amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = Math.random() * 16 | 0;
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}
