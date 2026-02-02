/**
 * Blood Bridge - DOM updates and form handling.
 * Consumes API via BloodBridgeAPI; no inline API URLs.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Auto-hide flash messages
    document.querySelectorAll('.flash').forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            setTimeout(() => flash.remove(), 500);
        }, 4000);
    });

    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email')?.value?.trim() || '';
            const password = document.getElementById('password')?.value || '';
            const res = await window.BloodBridgeAPI.auth.login({ email, password });
            if (res.ok && res.data.success) {
                const data = res.data.data;
                if (data?.user?.session?.role && ['admin', 'bloodbank'].includes(data.user.session.role)) {
                    window.location.href = '/dashboard';
                } else {
                    window.location.href = '/choose_role';
                }
            } else {
                showFlash(res.data?.message || 'Login failed.', 'error');
            }
        });
    }

    // Register form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                name: document.querySelector('#register-form input[name="name"]')?.value?.trim() || '',
                email: document.querySelector('#register-form input[name="email"]')?.value?.trim()?.toLowerCase() || '',
                password: document.querySelector('#register-form input[name="password"]')?.value || '',
                blood_group: document.querySelector('#register-form select[name="blood_group"]')?.value?.trim() || null,
                admin_code: document.querySelector('#register-form input[name="admin_code"]')?.value?.trim() || '',
            };
            const res = await window.BloodBridgeAPI.auth.register(payload);
            if (res.ok && res.data.success) {
                window.location.href = '/login';
            } else {
                showFlash(res.data?.message || 'Registration failed.', 'error');
            }
        });
    }

    // Choose role form
    const chooseRoleForm = document.getElementById('choose-role-form');
    if (chooseRoleForm) {
        chooseRoleForm.addEventListener('submit', async (e) => {
            const btn = e.target.querySelector('button[type="submit"]:focus, button[name="role_choice"]');
            const role = (btn && btn.getAttribute('value')) || document.querySelector('input[name="role_choice"]:checked')?.value;
            if (!role) return;
            e.preventDefault();
            const res = await window.BloodBridgeAPI.auth.chooseRole({ role_choice: role });
            if (res.ok && res.data.success) {
                window.location.href = '/dashboard';
            } else {
                showFlash(res.data?.message || 'Failed to set role.', 'error');
            }
        });
        chooseRoleForm.querySelectorAll('button[name="role_choice"]').forEach(btn => {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                window.BloodBridgeAPI.auth.chooseRole({ role_choice: this.value }).then(res => {
                    if (res.ok && res.data.success) {
                        window.location.href = '/dashboard';
                    } else {
                        showFlash(res.data?.message || 'Failed to set role.', 'error');
                    }
                });
            });
        });
    }

    // Contact form
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nameEl = contactForm.querySelector('input[name="name"]');
            const emailEl = contactForm.querySelector('input[name="email"]') || contactForm.querySelector('input[type="email"]');
            const payload = {
                name: (nameEl?.value || '').trim(),
                email: (emailEl?.value || '').trim().toLowerCase(),
                subject: (contactForm.querySelector('select[name="subject"]')?.value || '').trim(),
                message: (contactForm.querySelector('textarea[name="message"]')?.value || '').trim(),
            };
            const res = await window.BloodBridgeAPI.health.contact(payload);
            if (res.ok && res.data.success) {
                showFlash(res.data.message, 'success');
                contactForm.reset();
            } else {
                showFlash(res.data?.message || 'Failed to send message.', 'error');
            }
        });
    }

    // Blood request form (recipient / request_blood page)
    const bloodRequestForm = document.getElementById('blood-request-form');
    if (bloodRequestForm) {
        bloodRequestForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                patient_name: bloodRequestForm.querySelector('[name="patient_name"]')?.value?.trim() || '',
                blood_group: bloodRequestForm.querySelector('[name="blood_group"]')?.value?.trim() || '',
                units: bloodRequestForm.querySelector('[name="units"]')?.value || '',
                hospital: bloodRequestForm.querySelector('[name="hospital"]')?.value?.trim() || '',
            };
            const res = await window.BloodBridgeAPI.requests.create(payload);
            if (res.ok && res.data.success) {
                showFlash(res.data.message, 'success');
                window.location.href = '/dashboard';
            } else {
                showFlash(res.data?.message || 'Failed to submit request.', 'error');
            }
        });
    }

    // Schedule donation form
    const scheduleForm = document.getElementById('schedule-donation-form');
    if (scheduleForm) {
        scheduleForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                donation_date: scheduleForm.querySelector('[name="donation_date"]')?.value?.trim() || '',
                blood_group: scheduleForm.querySelector('[name="blood_group"]')?.value?.trim() || '',
                location: scheduleForm.querySelector('[name="location"]')?.value?.trim() || '',
                time_slot: scheduleForm.querySelector('[name="time_slot"]')?.value?.trim() || '',
            };
            const res = await window.BloodBridgeAPI.donors.schedule(payload);
            if (res.ok && res.data.success) {
                showFlash(res.data.message, 'success');
                window.location.href = '/dashboard';
            } else {
                showFlash(res.data?.message || 'Failed to schedule donation.', 'error');
            }
        });
    }
});

function showFlash(message, type = 'success') {
    const existing = document.querySelector('.container .flash');
    if (existing) existing.remove();
    const div = document.createElement('div');
    div.className = 'flash' + (type === 'error' ? ' error' : '');
    div.textContent = message;
    const container = document.querySelector('.container');
    if (container) container.insertBefore(div, container.firstChild);
    setTimeout(() => {
        div.style.opacity = '0';
        setTimeout(() => div.remove(), 500);
    }, 4000);
}

window.BloodBridgeShowFlash = showFlash;
