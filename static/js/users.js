/**
 * User Management JavaScript
 * Handles CRUD operations for user accounts (admin only)
 */

const API_BASE_URL = window.location.origin;
let currentDeleteUserId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    loadUsers();
    setupEventListeners();
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Add user button
    document.getElementById('addUserBtn').addEventListener('click', openAddUserModal);

    // Modal close buttons
    document.getElementById('closeModal').addEventListener('click', closeUserModal);
    document.getElementById('cancelBtn').addEventListener('click', closeUserModal);
    document.getElementById('closeDeleteModal').addEventListener('click', closeDeleteModal);
    document.getElementById('cancelDeleteBtn').addEventListener('click', closeDeleteModal);

    // Form submit
    document.getElementById('userForm').addEventListener('submit', handleCreateUser);

    // Delete confirm
    document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDelete);

    // Search
    document.getElementById('searchInput').addEventListener('input', filterUsers);

    // Close modals on outside click
    window.addEventListener('click', function (e) {
        const userModal = document.getElementById('userModal');
        const deleteModal = document.getElementById('deleteModal');
        if (e.target === userModal) closeUserModal();
        if (e.target === deleteModal) closeDeleteModal();
    });
}

/**
 * Load all users
 */
async function loadUsers() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/users`);
        const data = await response.json();

        if (data.success) {
            displayUsers(data.users);
        } else {
            showError('Failed to load users');
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showError('Cannot connect to server');
    }
}

/**
 * Display users in table
 */
function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');

    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="no-data">No users found</td></tr>';
        return;
    }

    tbody.innerHTML = users.map(user => `
        <tr data-user-id="${user.id}">
            <td>${escapeHtml(user.username)}</td>
            <td>${escapeHtml(user.email || '-')}</td>
            <td><span class="role-badge role-${user.role}">${user.role}</span></td>
            <td><span class="status-badge status-${user.is_active ? 'active' : 'inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>${formatDate(user.created_at)}</td>
            <td class="actions">
                <button class="btn-icon" onclick="toggleUserStatus(${user.id}, ${!user.is_active})" title="${user.is_active ? 'Disable' : 'Enable'}">
                    ${user.is_active ? '🔒' : '🔓'}
                </button>
                <button class="btn-icon" onclick="deleteUser(${user.id})" title="Delete">
                    🗑️
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Filter users by search
 */
function filterUsers() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('#usersTableBody tr');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

/**
 * Open add user modal
 */
function openAddUserModal() {
    document.getElementById('modalTitle').textContent = 'Add New User';
    document.getElementById('userForm').reset();
    document.getElementById('userModal').classList.add('show');
}

/**
 * Close user modal
 */
function closeUserModal() {
    document.getElementById('userModal').classList.remove('show');
}

/**
 * Handle create user form submit
 */
async function handleCreateUser(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const userData = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: formData.get('password'),
        role: formData.get('role')
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });

        const data = await response.json();

        if (data.success) {
            showSuccess('User created successfully');
            closeUserModal();
            loadUsers();
        } else {
            showError(data.message || 'Failed to create user');
        }
    } catch (error) {
        console.error('Error creating user:', error);
        showError('Cannot connect to server');
    }
}

/**
 * Toggle user status (enable/disable)
 */
async function toggleUserStatus(userId, isActive) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/users/${userId}/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive })
        });

        const data = await response.json();

        if (data.success) {
            showSuccess(data.message);
            loadUsers();
        } else {
            showError(data.message || 'Failed to update user status');
        }
    } catch (error) {
        console.error('Error toggling user status:', error);
        showError('Cannot connect to server');
    }
}

/**
 * Delete user (show confirmation)
 */
function deleteUser(userId) {
    currentDeleteUserId = userId;
    document.getElementById('deleteModal').classList.add('show');
}

/**
 * Confirm delete user
 */
async function confirmDelete() {
    if (!currentDeleteUserId) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/users/${currentDeleteUserId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showSuccess('User deleted successfully');
            closeDeleteModal();
            loadUsers();
        } else {
            showError(data.message || 'Failed to delete user');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showError('Cannot connect to server');
    }
}

/**
 * Close delete modal
 */
function closeDeleteModal() {
    document.getElementById('deleteModal').classList.remove('show');
    currentDeleteUserId = null;
}

/**
 * Show success message
 */
function showSuccess(message) {
    alert('✅ ' + message);
}

/**
 * Show error message
 */
function showError(message) {
    alert('❌ ' + message);
}

/**
 * Format date
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
