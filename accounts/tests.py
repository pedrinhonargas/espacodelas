"""
Tests for accounts app — authentication and profile views.
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User


class TestLoginView:
    """Tests for the login flow."""

    def test_login_page_renders(self, client, db):
        """GET /studio/login/ should return 200."""
        url = reverse('dashboard:login')
        response = client.get(url)
        assert response.status_code == 200

    def test_login_with_valid_credentials_redirects(self, client, create_user, create_professional):
        """POST with valid credentials should redirect to dashboard."""
        user = create_user(username='prof_login', password='senha123')
        create_professional(name='LoginTest', user=user)
        url = reverse('dashboard:login')
        response = client.post(url, {'username': 'prof_login', 'password': 'senha123'})
        assert response.status_code == 302

    def test_login_with_invalid_credentials_shows_error(self, client, db):
        """POST with wrong password should return 200 with error."""
        User.objects.create_user(username='badlogin', password='correct')
        url = reverse('dashboard:login')
        response = client.post(url, {'username': 'badlogin', 'password': 'wrong'})
        assert response.status_code == 200  # re-renders form with error

    def test_login_staff_redirects_to_owner(self, client, create_user):
        """Staff user should be redirected to owner dashboard."""
        create_user(username='admin_user', password='senha123', is_staff=True)
        url = reverse('dashboard:login')
        response = client.post(url, {'username': 'admin_user', 'password': 'senha123'})
        assert response.status_code == 302
        assert 'owner' in response.url or 'studio' in response.url

    def test_already_authenticated_user_redirected(self, client, create_user, create_professional):
        """An already logged-in user should be redirected away from login page."""
        user = create_user(username='already_in', password='senha123')
        create_professional(name='Already', user=user)
        client.login(username='already_in', password='senha123')
        url = reverse('dashboard:login')
        response = client.get(url)
        assert response.status_code == 302


class TestLogoutView:
    """Tests for logout."""

    def test_logout_redirects_to_home(self, client, create_user):
        """GET /studio/logout/ should redirect to home."""
        create_user(username='logout_user', password='senha123')
        client.login(username='logout_user', password='senha123')
        url = reverse('dashboard:logout')
        response = client.get(url)
        assert response.status_code == 302


class TestProtectedViews:
    """Tests that dashboard views require authentication."""

    @pytest.mark.parametrize("url_name", [
        'dashboard:agenda',
        'dashboard:block_slot',
    ])
    def test_unauthenticated_redirects_to_login(self, client, db, url_name):
        """Unauthenticated user should be redirected to login."""
        url = reverse(url_name)
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_owner_dashboard_requires_staff(self, client, create_user, create_professional):
        """Non-staff professional should not access owner dashboard."""
        user = create_user(username='non_staff', password='senha123', is_staff=False)
        create_professional(name='NonStaff', user=user)
        client.login(username='non_staff', password='senha123')
        url = reverse('dashboard:owner')
        response = client.get(url)
        assert response.status_code == 403  # PermissionDenied


class TestProfileView:
    """Tests for the profile edit view."""

    def test_profile_page_loads_for_professional(self, client, create_user, create_professional):
        """Professional should be able to access profile page."""
        user = create_user(username='prof_profile', password='senha123')
        create_professional(name='ProfileTest', user=user)
        client.login(username='prof_profile', password='senha123')
        url = reverse('accounts:profile')
        response = client.get(url)
        assert response.status_code == 200

    def test_profile_update_saves_data(self, client, create_user, create_professional):
        """POST to profile should update professional data."""
        user = create_user(username='prof_update', password='senha123')
        prof = create_professional(name='OldName', user=user)
        client.login(username='prof_update', password='senha123')
        url = reverse('accounts:profile')
        response = client.post(url, {'name': 'NewName', 'bio': 'Nova bio'})
        assert response.status_code == 302  # redirect on success
        prof.refresh_from_db()
        assert prof.name == 'NewName'
