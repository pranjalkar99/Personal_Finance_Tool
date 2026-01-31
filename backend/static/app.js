/**
 * Expense Tracker - Production-Ready Frontend Application
 */

const API_BASE_URL = '';

// Auth State
let accessToken = localStorage.getItem('accessToken');
let refreshToken = localStorage.getItem('refreshToken');
let currentUser = null;
let currentPage = 1;
let totalPages = 1;
let expenseToDelete = null;

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

// Filter elements
const filterCategory = document.getElementById('filter-category');
const filterStartDate = document.getElementById('filter-start-date');
const filterEndDate = document.getElementById('filter-end-date');
const sortOrder = document.getElementById('sort-order');

// Pagination
const prevPageBtn = document.getElementById('prev-page');
const nextPageBtn = document.getElementById('next-page');
const pageInfo = document.getElementById('page-info');
const pagination = document.getElementById('pagination');

// Modal
const deleteModal = document.getElementById('delete-modal');
const cancelDeleteBtn = document.getElementById('cancel-delete');
const confirmDeleteBtn = document.getElementById('confirm-delete');

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    document.getElementById('date').valueAsDate = new Date();
    
    // Auth form switches
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
    
    // Form submissions
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    expenseForm.addEventListener('submit', handleExpenseSubmit);
    logoutBtn.addEventListener('click', handleLogout);
    exportBtn.addEventListener('click', handleExport);
    
    // Filters
    filterCategory.addEventListener('change', () => { currentPage = 1; loadExpenses(); });
    filterStartDate.addEventListener('change', () => { currentPage = 1; loadExpenses(); });
    filterEndDate.addEventListener('change', () => { currentPage = 1; loadExpenses(); });
    sortOrder.addEventListener('change', () => { currentPage = 1; loadExpenses(); });
    
    // Pagination
    prevPageBtn.addEventListener('click', () => { currentPage--; loadExpenses(); });
    nextPageBtn.addEventListener('click', () => { currentPage++; loadExpenses(); });
    
    // Modal
    cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    confirmDeleteBtn.addEventListener('click', confirmDelete);
    
    // Check if logged in
    if (accessToken) {
        await checkAuth();
    } else {
        showAuthSection();
    }
}

// === Auth Functions ===

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
    } catch (error) {
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
    } catch (error) {
        showMessage('login-message', 'Network error. Please try again.', true);
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
            const detail = error.errors ? error.errors.map(e => e.message).join(', ') : error.detail;
            showMessage('register-message', detail || 'Registration failed', true);
        }
    } catch (error) {
        showMessage('register-message', 'Network error. Please try again.', true);
    } finally {
        setButtonLoading(btn, false);
    }
}

function handleLogout() {
    clearAuth();
    currentUser = null;
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
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${accessToken}`
    };
    
    let response = await fetch(`${API_BASE_URL}${url}`, { ...options, headers });
    
    // Try refresh if unauthorized
    if (response.status === 401 && refreshToken) {
        const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh?refresh_token=${refreshToken}`, {
            method: 'POST'
        });
        
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

// === UI Functions ===

function showAuthSection() {
    authSection.hidden = false;
    appSection.hidden = true;
}

function showAppSection() {
    authSection.hidden = true;
    appSection.hidden = false;
    userDisplay.textContent = currentUser.full_name || currentUser.username;
    loadExpenses();
    loadSummary();
}

function setButtonLoading(btn, loading) {
    btn.disabled = loading;
    btn.querySelector('.btn-text').hidden = loading;
    btn.querySelector('.btn-loading').hidden = !loading;
}

function showMessage(elementId, message, isError) {
    const el = document.getElementById(elementId);
    el.textContent = message;
    el.className = `form-message ${isError ? 'error' : 'success'}`;
    el.hidden = false;
    setTimeout(() => { el.hidden = true; }, 5000);
}

// === Expense Functions ===

async function handleExpenseSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    setButtonLoading(btn, true);
    
    const formData = new FormData(expenseForm);
    const expenseData = {
        amount: parseFloat(formData.get('amount')),
        category: formData.get('category'),
        description: formData.get('description'),
        date: new Date(formData.get('date')).toISOString(),
        idempotency_key: generateUUID()
    };
    
    try {
        const response = await fetchWithAuth('/expenses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(expenseData)
        });
        
        if (response.ok) {
            showMessage('form-message', 'Expense added!', false);
            expenseForm.reset();
            document.getElementById('date').valueAsDate = new Date();
            loadExpenses();
            loadSummary();
        } else {
            const error = await response.json();
            showMessage('form-message', error.detail || 'Failed to add expense', true);
        }
    } catch (error) {
        showMessage('form-message', 'Network error', true);
    } finally {
        setButtonLoading(btn, false);
    }
}

async function loadExpenses() {
    setListState('loading');
    
    const params = new URLSearchParams();
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
    } catch (error) {
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
    tbody.innerHTML = data.expenses.map(expense => `
        <tr>
            <td class="expense-date">${formatDate(expense.date)}</td>
            <td><span class="expense-category">${escapeHtml(expense.category)}</span></td>
            <td class="expense-description" title="${escapeHtml(expense.description)}">${escapeHtml(expense.description)}</td>
            <td class="expense-amount">${formatCurrency(expense.amount)}</td>
            <td class="expense-actions">
                <button class="btn btn-secondary btn-icon btn-sm" onclick="openDeleteModal(${expense.id})" title="Delete">✕</button>
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
            
            // Calculate this month
            const now = new Date();
            const monthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
            const monthTotal = data.monthly_totals[monthKey] || 0;
            document.getElementById('summary-month').textContent = formatCurrency(monthTotal);
        }
    } catch (error) {
        console.error('Failed to load summary', error);
    }
}

function openDeleteModal(expenseId) {
    expenseToDelete = expenseId;
    deleteModal.hidden = false;
}

function closeDeleteModal() {
    expenseToDelete = null;
    deleteModal.hidden = true;
}

async function confirmDelete() {
    if (!expenseToDelete) return;
    
    try {
        const response = await fetchWithAuth(`/expenses/${expenseToDelete}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            closeDeleteModal();
            loadExpenses();
            loadSummary();
        }
    } catch (error) {
        console.error('Delete failed', error);
    }
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
    } catch (error) {
        console.error('Export failed', error);
    }
}

function setListState(state) {
    document.getElementById('loading-indicator').hidden = state !== 'loading';
    document.getElementById('empty-state').hidden = state !== 'empty';
    document.getElementById('expenses-table').hidden = state !== 'data';
}

// === Utility Functions ===

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
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
