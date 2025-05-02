"""Fixtures for browser automation tests."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import Browser, BrowserContext, ElementHandle, Page, Response


class PlaywrightMockFactory:
    """Factory to create comprehensive Playwright mocks."""

    @staticmethod
    def create_mock_browser():
        """Create a mocked browser."""
        browser_mock = AsyncMock(spec=Browser)
        return browser_mock

    @staticmethod
    def create_mock_context(browser_mock=None):
        """Create a mocked browser context."""
        if browser_mock is None:
            browser_mock = PlaywrightMockFactory.create_mock_browser()

        context_mock = AsyncMock(spec=BrowserContext)
        browser_mock.new_context.return_value = context_mock
        return context_mock

    @staticmethod
    def create_mock_page(context_mock=None):
        """Create a mocked page."""
        if context_mock is None:
            context_mock = PlaywrightMockFactory.create_mock_context()

        page_mock = AsyncMock(spec=Page)
        context_mock.new_page.return_value = page_mock
        return page_mock

    @staticmethod
    def create_mock_response(status=200, headers=None):
        """Create a mocked response."""
        if headers is None:
            headers = {"content-type": "text/html"}

        response_mock = AsyncMock(spec=Response)
        response_mock.status = status
        response_mock.headers = headers
        return response_mock

    @staticmethod
    def create_mock_element():
        """Create a mocked element."""
        element_mock = AsyncMock(spec=ElementHandle)
        return element_mock

    @staticmethod
    def setup_full_mock(html_content="<html><body><p>Test content</p></body></html>", status=200):
        """Set up a complete mock environment for testing."""
        browser_mock = PlaywrightMockFactory.create_mock_browser()
        context_mock = PlaywrightMockFactory.create_mock_context(browser_mock)
        page_mock = PlaywrightMockFactory.create_mock_page(context_mock)
        response_mock = PlaywrightMockFactory.create_mock_response(status)
        element_mock = PlaywrightMockFactory.create_mock_element()

        # Set up page mock methods
        page_mock.goto.return_value = response_mock
        page_mock.content.return_value = html_content
        page_mock.query_selector.return_value = element_mock
        element_mock.inner_html.return_value = "<p>Test content</p>"

        # Create playwright mock
        playwright_mock = MagicMock()
        playwright_mock.chromium = MagicMock()
        playwright_mock.chromium.launch = AsyncMock(return_value=browser_mock)

        class MockAsyncPlaywright:
            async def __aenter__(self):
                return playwright_mock

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        return {
            "playwright": playwright_mock,
            "browser": browser_mock,
            "context": context_mock,
            "page": page_mock,
            "response": response_mock,
            "element": element_mock,
            "mock_object": MockAsyncPlaywright(),
        }


@pytest.fixture
def mock_playwright_factory():
    """Fixture to provide the PlaywrightMockFactory."""
    return PlaywrightMockFactory


@pytest.fixture
def setup_mock_browser(monkeypatch):
    """Fixture to set up a mocked browser environment."""
    mock_setup = PlaywrightMockFactory.setup_full_mock()

    # Patch the async_playwright function
    monkeypatch.setattr("playwright.async_api.async_playwright", lambda: mock_setup["mock_object"])

    return mock_setup
