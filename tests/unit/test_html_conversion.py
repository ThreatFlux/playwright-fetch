"""Unit tests for HTML to Markdown conversion functionality."""

import pytest

from mcp_server_fetch.server import html_to_markdown


class TestHtmlToMarkdown:
    """Tests for HTML to Markdown conversion."""

    def test_basic_conversion(self):
        """Test basic HTML to Markdown conversion."""
        html = "<h1>Title</h1><p>This is a <strong>test</strong> paragraph.</p>"
        markdown = html_to_markdown(html)

        assert "# Title" in markdown
        assert "This is a **test** paragraph." in markdown

    def test_convert_links(self):
        """Test conversion of HTML links to Markdown."""
        html = '<p>Check out <a href="https://example.com">this link</a>.</p>'
        markdown = html_to_markdown(html)

        assert "Check out [this link](https://example.com)." in markdown

    def test_convert_lists(self):
        """Test conversion of HTML lists to Markdown."""
        html = """
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>
        """
        markdown = html_to_markdown(html)

        assert "* Item 1" in markdown
        assert "* Item 2" in markdown
        assert "* Item 3" in markdown

    def test_convert_headings(self, mock_html_content, mock_markdown_content):
        """Test conversion of HTML headings to Markdown."""
        markdown = html_to_markdown(mock_html_content)

        assert "# Test Website" in markdown
        assert "## Main Content" in markdown

    def test_convert_complex_document(self, mock_html_content, mock_markdown_content):
        """Test conversion of a complex HTML document."""
        markdown = html_to_markdown(mock_html_content)

        # Remove whitespace and newlines for comparison
        simplified_actual = "".join(markdown.split())
        simplified_expected = "".join(mock_markdown_content.split())

        assert "Test Website" in markdown
        assert "Main Content" in markdown
        assert "important" in markdown
        assert simplified_actual.find("MainContent") < simplified_actual.find("important")
        assert simplified_expected.find("MainContent") < simplified_expected.find("important")
