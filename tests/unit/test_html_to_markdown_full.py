"""Full test suite for the HTML to markdown conversion function."""

import pytest

from mcp_server_fetch.server import html_to_markdown


class TestHtmlToMarkdownFull:
    """Comprehensive tests for the html_to_markdown function."""

    def test_simple_conversion(self):
        """Test converting simple HTML to markdown."""
        html = "<h1>Hello World</h1><p>This is a test.</p>"
        markdown = html_to_markdown(html)
        assert "# Hello World" in markdown
        assert "This is a test." in markdown

    def test_multiline_conversion(self):
        """Test converting multiline HTML to markdown."""
        html = """
        <div>
            <h1>Title</h1>
            <p>Paragraph 1</p>
            <p>Paragraph 2</p>
        </div>
        """
        markdown = html_to_markdown(html)
        assert "# Title" in markdown
        assert "Paragraph 1" in markdown
        assert "Paragraph 2" in markdown

    def test_nested_elements(self):
        """Test converting nested HTML elements to markdown."""
        html = """
        <article>
            <h2>Article Title</h2>
            <section>
                <h3>Section Title</h3>
                <p>This is a <strong>important</strong> paragraph with <em>emphasized</em> text.</p>
            </section>
        </article>
        """
        markdown = html_to_markdown(html)
        assert "## Article Title" in markdown
        assert "### Section Title" in markdown
        assert "This is a **important** paragraph with *emphasized* text." in markdown

    def test_links_conversion(self):
        """Test converting HTML links to markdown."""
        html = """
        <p>Check out <a href="https://example.com">this link</a> for more information.</p>
        <p>Or visit <a href="https://example.org" title="Example Site">another site</a>.</p>
        """
        markdown = html_to_markdown(html)
        assert "[this link](https://example.com)" in markdown
        assert "another site" in markdown
        assert "https://example.org" in markdown

    def test_lists_conversion(self):
        """Test converting HTML lists to markdown."""
        html = """
        <h3>Ordered List</h3>
        <ol>
            <li>First item</li>
            <li>Second item</li>
            <li>Third item</li>
        </ol>

        <h3>Unordered List</h3>
        <ul>
            <li>Apple</li>
            <li>Banana</li>
            <li>Cherry</li>
        </ul>
        """
        markdown = html_to_markdown(html)
        assert "### Ordered List" in markdown
        assert "1. First item" in markdown
        assert "2. Second item" in markdown
        assert "3. Third item" in markdown
        assert "### Unordered List" in markdown
        assert "* Apple" in markdown
        assert "* Banana" in markdown
        assert "* Cherry" in markdown

    def test_nested_lists(self):
        """Test converting nested HTML lists to markdown."""
        html = """
        <ul>
            <li>Top level 1
                <ul>
                    <li>Nested 1.1</li>
                    <li>Nested 1.2</li>
                </ul>
            </li>
            <li>Top level 2
                <ul>
                    <li>Nested 2.1</li>
                    <li>Nested 2.2</li>
                </ul>
            </li>
        </ul>
        """
        markdown = html_to_markdown(html)
        assert "* Top level 1" in markdown
        assert "Nested 1.1" in markdown
        assert "Nested 1.2" in markdown
        assert "* Top level 2" in markdown
        assert "Nested 2.1" in markdown
        assert "Nested 2.2" in markdown

    def test_code_blocks(self):
        """Test converting HTML code blocks to markdown."""
        html = """
        <pre><code>function example() {
            console.log("Hello, world!");
        }</code></pre>

        <p>Inline <code>code</code> example.</p>
        """
        markdown = html_to_markdown(html)
        assert "```\nfunction example() {" in markdown
        assert 'console.log("Hello, world!");' in markdown
        assert "```" in markdown
        assert "Inline `code` example." in markdown

    def test_blockquote_conversion(self):
        """Test converting HTML blockquotes to markdown."""
        html = """
        <blockquote>
            <p>This is a blockquote.</p>
            <p>It can contain multiple paragraphs.</p>
        </blockquote>
        """
        markdown = html_to_markdown(html)
        assert "> This is a blockquote." in markdown
        assert "> It can contain multiple paragraphs." in markdown

    def test_image_conversion(self):
        """Test converting HTML images to markdown."""
        html = """
        <figure>
            <img src="https://example.com/image.jpg" alt="Example Image">
            <figcaption>Figure 1: An example image</figcaption>
        </figure>
        """
        markdown = html_to_markdown(html)
        assert "![Example Image](https://example.com/image.jpg)" in markdown
        assert "Figure 1: An example image" in markdown

    def test_tables_conversion(self):
        """Test converting HTML tables to markdown."""
        html = """
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Age</th>
                    <th>Role</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>John</td>
                    <td>30</td>
                    <td>Developer</td>
                </tr>
                <tr>
                    <td>Jane</td>
                    <td>28</td>
                    <td>Designer</td>
                </tr>
            </tbody>
        </table>
        """
        markdown = html_to_markdown(html)
        assert "Name" in markdown
        assert "Age" in markdown
        assert "Role" in markdown
        assert "John" in markdown
        assert "30" in markdown
        assert "Developer" in markdown
        assert "Jane" in markdown
        assert "28" in markdown
        assert "Designer" in markdown

    def test_special_characters(self):
        """Test handling of special characters in HTML."""
        html = """
        <p>Special characters: &amp; &lt; &gt; &quot; &apos;</p>
        <p>HTML entities: &copy; &reg; &trade;</p>
        """
        markdown = html_to_markdown(html)
        assert "Special characters: & < > \" '" in markdown
        assert "HTML entities: © ® ™" in markdown
