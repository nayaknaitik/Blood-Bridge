/**
 * Admin frontend logic: login, dashboard, lists.
 */

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('admin-login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('admin-email')?.value?.trim() || '';
      const password = document.getElementById('admin-password')?.value || '';
      const res = await window.BloodBridgeAdminAPI.auth.login({ email, password });
      if (res.ok && res.data.success) {
        window.location.href = '/admin/dashboard';
      } else {
        alert(res.data?.message || 'Admin login failed.');
      }
    });
  }

  const dashRoot = document.getElementById('admin-dashboard-root');
  if (dashRoot) {
    window.BloodBridgeAdminAPI.dashboard.stats().then((res) => {
      if (!res.ok || !res.data.success) {
        dashRoot.innerHTML = '<p class="flash error">Failed to load admin dashboard.</p>';
        return;
      }
      const d = res.data.data;
      const stats = d.stats || {};
      const inv = d.inventory || [];
      let html = '<div class="admin-container">';
      html += '<header class="admin-header"><h1>Administrator Control Panel</h1><p>System overview</p></header>';
      html += '<div class="stats-grid">';
      html += `<div class="stat-card"><h3>${stats.total_users || 0}</h3><p>Total Users</p></div>`;
      html += `<div class="stat-card"><h3>${stats.donors_count || 0}</h3><p>Donors</p></div>`;
      html += `<div class="stat-card"><h3>${stats.pending_requests || 0}</h3><p>Pending Requests</p></div>`;
      html += `<div class="stat-card"><h3>${stats.total_inventory || 0}</h3><p>Total Units</p></div>`;
      html += '</div>';
      html += '<section class="admin-table-section"><h2>Blood Inventory</h2><div class="inventory-grid">';
      inv.forEach(item => {
        html += `<div class="inventory-card${item.units < 5 ? ' low' : ''}"><h3>${item.group}</h3><p>${item.units} Units</p></div>`;
      });
      html += '</div></section></div>';
      dashRoot.innerHTML = html;
    });
  }

  const usersRoot = document.getElementById('admin-users-root');
  if (usersRoot) {
    window.BloodBridgeAdminAPI.users.list().then((res) => {
      if (!res.ok || !res.data.success) {
        usersRoot.innerHTML = '<p class="flash error">Failed to load users.</p>';
        return;
      }
      const users = res.data.data.users || [];
      let html = '<div class="admin-container"><h2>Users</h2><div class="table-wrapper"><table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Actions</th></tr></thead><tbody>';
      if (!users.length) {
        html += '<tr><td colspan="4" style="text-align:center;">No users.</td></tr>';
      } else {
        users.forEach(u => {
          const role = u.role || 'user';
          html += `<tr><td>${u.name || ''}</td><td>${u.email || ''}</td><td>${role}</td>`;
          html += `<td><button type="button" class="btn-sm delete" data-user-id="${u.id}">Delete</button></td></tr>`;
        });
      }
      html += '</tbody></table></div></div>';
      usersRoot.innerHTML = html;
      usersRoot.querySelectorAll('button.btn-sm.delete').forEach(btn => {
        btn.addEventListener('click', () => {
          const id = btn.getAttribute('data-user-id');
          if (!id || !confirm('Delete this user?')) return;
          window.BloodBridgeAdminAPI.users.delete(id).then(r => {
            if (r.ok && r.data.success) window.location.reload();
            else alert(r.data?.message || 'Failed to delete user.');
          });
        });
      });
    });
  }

  const reqRoot = document.getElementById('admin-requests-root');
  if (reqRoot) {
    window.BloodBridgeAdminAPI.requests.list().then((res) => {
      if (!res.ok || !res.data.success) {
        reqRoot.innerHTML = '<p class="flash error">Failed to load requests.</p>';
        return;
      }
      const reqs = res.data.data.requests || [];
      let html = '<div class="admin-container"><h2>Blood Requests</h2><div class="table-wrapper"><table><thead><tr><th>Patient</th><th>Group</th><th>Units</th><th>Hospital</th><th>Status</th><th>Date</th></tr></thead><tbody>';
      if (!reqs.length) {
        html += '<tr><td colspan="6" style="text-align:center;">No requests.</td></tr>';
      } else {
        reqs.forEach(r => {
          html += `<tr><td>${r.patient_name || ''}</td><td>${r.blood_group || ''}</td><td>${r.units || ''}</td><td>${r.hospital || ''}</td><td>${r.status || ''}</td><td>${r.timestamp || ''}</td></tr>`;
        });
      }
      html += '</tbody></table></div></div>';
      reqRoot.innerHTML = html;
    });
  }

  const invRoot = document.getElementById('admin-inventory-root');
  if (invRoot) {
    window.BloodBridgeAdminAPI.inventory.list().then((res) => {
      if (!res.ok || !res.data.success) {
        invRoot.innerHTML = '<p class="flash error">Failed to load inventory.</p>';
        return;
      }
      const inv = res.data.data.inventory || [];
      let html = '<div class="admin-container"><h2>Blood Inventory</h2><div class="inventory-grid">';
      inv.forEach(item => {
        html += `<div class="inventory-card${item.units < 5 ? ' low' : ''}"><h3>${item.group}</h3><p>${item.units} Units</p></div>`;
      });
      html += '</div></div>';
      invRoot.innerHTML = html;
    });
  }
});

