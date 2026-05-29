"""
Tests for core SEO views (sitemap.xml and robots.txt).
"""
import pytest
from django.urls import reverse

class TestSEOMetadata:
    """Test SEO-related views like sitemap.xml and robots.txt."""

    def test_sitemap_xml_renders_correctly(self, client, db):
        """GET /sitemap.xml should return valid XML sitemap."""
        url = reverse('core:sitemap')
        response = client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/xml'
        
        # Verify content contains XML declaration and home loc
        content = response.content.decode('utf-8')
        assert '<?xml version="1.0" encoding="UTF-8"?>' in content
        assert '<urlset' in content
        assert '/agendar/' in content

    def test_robots_txt_renders_correctly(self, client):
        """GET /robots.txt should return plain text robots config."""
        url = reverse('core:robots')
        response = client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/plain'
        
        content = response.content.decode('utf-8')
        assert 'User-agent: *' in content
        assert 'Disallow: /studio/' in content
        assert 'Sitemap: ' in content
        assert '/sitemap.xml' in content
