"""Unit tests for the get_robots_txt_url function."""

import pytest

from mcp_server_fetch.server import get_robots_txt_url


class TestGetRobotsTxtUrl:
    """Tests for the get_robots_txt_url function."""

    def test_simple_url(self):
        """Test with a simple URL."""
        url = "https://example.com"
        robots_url = get_robots_txt_url(url)
        assert robots_url == "https://example.com/robots.txt"

    def test_url_with_path(self):
        """Test with a URL that has a path."""
        url = "https://example.com/some/path"
        robots_url = get_robots_txt_url(url)
        assert robots_url == "https://example.com/robots.txt"

    def test_url_with_query_params(self):
        """Test with a URL that has query parameters."""
        url = "https://example.com/search?q=test&page=1"
        robots_url = get_robots_txt_url(url)
        assert robots_url == "https://example.com/robots.txt"

    def test_url_with_fragment(self):
        """Test with a URL that has a fragment."""
        url = "https://example.com/page#section1"
        robots_url = get_robots_txt_url(url)
        assert robots_url == "https://example.com/robots.txt"

    def test_url_with_credentials(self):
        """Test with a URL that has username and password."""
        url = "https://user:password@example.com/secure"
        robots_url = get_robots_txt_url(url)
        assert robots_url == "https://user:password@example.com/robots.txt"

    def test_url_with_port(self):
        """Test with a URL that has a custom port."""
        url = "https://example.com:8080/api"
        robots_url = get_robots_txt_url(url)
        assert robots_url == "https://example.com:8080/robots.txt"

    def test_different_schemes(self):
        """Test with different URL schemes."""
        # HTTP
        url = "http://example.com"
        robots_url = get_robots_txt_url(url)
        assert robots_url == "http://example.com/robots.txt"

        # FTP (unlikely but should work)
        url = "ftp://example.com"
        robots_url = get_robots_txt_url(url)
        assert robots_url == "ftp://example.com/robots.txt"

    def test_complex_url(self):
        """Test with a complex URL that has multiple components."""
        url = "https://user:pass@example.com:8443/path/to/page?query=value&filter=test#section2"
        robots_url = get_robots_txt_url(url)
        assert robots_url == "https://user:pass@example.com:8443/robots.txt"

    def test_subdomain_url(self):
        """Test with a URL that has a subdomain."""
        url = "https://blog.example.com/posts"
        robots_url = get_robots_txt_url(url)
        assert robots_url == "https://blog.example.com/robots.txt"
