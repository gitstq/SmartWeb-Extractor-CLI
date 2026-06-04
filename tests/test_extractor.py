#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 SmartWeb-Extractor-CLI Test Suite
Unit tests for the extraction engine
"""

import sys
import os
import unittest
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartweb_extractor import (
    Colors, Logger, HTTPClient, DOMNode, SmartHTMLParser,
    ContentAnalyzer, ExportEngine, SmartWebExtractor
)


class TestColors(unittest.TestCase):
    """Test color constants."""
    
    def test_color_codes(self):
        """Test that color codes are valid ANSI sequences."""
        self.assertTrue(Colors.RED.startswith("\033["))
        self.assertTrue(Colors.GREEN.startswith("\033["))
        self.assertTrue(Colors.RESET == "\033[0m")


class TestLogger(unittest.TestCase):
    """Test logging functionality."""
    
    def test_logger_creation(self):
        """Test logger initialization."""
        logger = Logger(verbose=True, quiet=False)
        self.assertTrue(logger.verbose)
        self.assertFalse(logger.quiet)
    
    def test_log_levels(self):
        """Test different log levels."""
        logger = Logger(verbose=True, quiet=False)
        # These should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.success("Success message")
        logger.warning("Warning message")
        logger.error("Error message")


class TestDOMNode(unittest.TestCase):
    """Test DOM node operations."""
    
    def test_node_creation(self):
        """Test DOM node creation."""
        node = DOMNode("div", {"class": "test"})
        self.assertEqual(node.tag, "div")
        self.assertEqual(node.get_attr("class"), "test")
    
    def test_add_child(self):
        """Test adding child nodes."""
        parent = DOMNode("div")
        child = DOMNode("p")
        parent.add_child(child)
        self.assertEqual(len(parent.children), 1)
        self.assertEqual(child.parent, parent)
    
    def test_get_text(self):
        """Test text extraction."""
        parent = DOMNode("div")
        text_node = DOMNode()
        text_node.text = "Hello World"
        parent.add_child(text_node)
        self.assertEqual(parent.get_text(), "Hello World")
    
    def test_find_all(self):
        """Test finding nodes by tag."""
        root = DOMNode("div")
        p1 = DOMNode("p")
        p2 = DOMNode("p")
        root.add_child(p1)
        root.add_child(p2)
        
        results = root.find_all("p")
        self.assertEqual(len(results), 2)


class TestSmartHTMLParser(unittest.TestCase):
    """Test HTML parser."""
    
    def test_parse_simple_html(self):
        """Test parsing simple HTML."""
        html = "<html><body><h1>Title</h1><p>Paragraph</p></body></html>"
        parser = SmartHTMLParser()
        dom = parser.parse(html)
        
        h1 = dom.find("h1")
        self.assertIsNotNone(h1)
        self.assertEqual(h1.get_text(), "Title")
    
    def test_parse_with_attributes(self):
        """Test parsing HTML with attributes."""
        html = '<div class="container" id="main"><p class="text">Content</p></div>'
        parser = SmartHTMLParser()
        dom = parser.parse(html)
        
        div = dom.find("div")
        self.assertEqual(div.get_attr("class"), "container")
        self.assertEqual(div.get_attr("id"), "main")
    
    def test_parse_self_closing(self):
        """Test parsing self-closing tags."""
        html = '<div><img src="test.jpg" alt="Test"><br></div>'
        parser = SmartHTMLParser()
        dom = parser.parse(html)
        
        img = dom.find("img")
        self.assertIsNotNone(img)
        self.assertEqual(img.get_attr("src"), "test.jpg")


class TestContentAnalyzer(unittest.TestCase):
    """Test content analysis engine."""
    
    def setUp(self):
        self.logger = Logger(quiet=True)
        self.analyzer = ContentAnalyzer(self.logger)
    
    def test_detect_article_content(self):
        """Test article content detection."""
        html = """
        <html>
            <body>
                <article>
                    <h1>Article Title</h1>
                    <div class="author">John Doe</div>
                    <div class="content">Article content here...</div>
                </article>
            </body>
        </html>
        """
        parser = SmartHTMLParser()
        dom = parser.parse(html)
        
        content_type = self.analyzer.detect_content_type(dom, "https://example.com/blog/post")
        self.assertEqual(content_type, "article")
    
    def test_generate_selectors(self):
        """Test selector generation."""
        html = """
        <html>
            <body>
                <article>
                    <h1>Title</h1>
                    <time>2026-01-01</time>
                    <div class="content">Content</div>
                </article>
            </body>
        </html>
        """
        parser = SmartHTMLParser()
        dom = parser.parse(html)
        
        selectors = self.analyzer.generate_smart_selectors(dom, "article")
        self.assertIn("title", selectors)
        self.assertIn("content", selectors)


class TestExportEngine(unittest.TestCase):
    """Test export functionality."""
    
    def setUp(self):
        self.logger = Logger(quiet=True)
        self.engine = ExportEngine(self.logger)
        self.sample_data = {
            "_meta": {"url": "https://example.com", "extracted_at": "2026-01-01"},
            "title": "Test Title",
            "content": "Test content",
        }
    
    def test_export_json(self):
        """Test JSON export."""
        result = self.engine.export(self.sample_data, "json")
        data = json.loads(result)
        self.assertEqual(data["title"], "Test Title")
    
    def test_export_markdown(self):
        """Test Markdown export."""
        result = self.engine.export(self.sample_data, "markdown")
        self.assertIn("# Test Title", result)
        self.assertIn("Test content", result)
    
    def test_export_csv(self):
        """Test CSV export."""
        result = self.engine.export(self.sample_data, "csv")
        self.assertIn("Field,Value", result)
    
    def test_export_html(self):
        """Test HTML export."""
        result = self.engine.export(self.sample_data, "html")
        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn("Test Title", result)


class TestSmartWebExtractor(unittest.TestCase):
    """Test main extractor engine."""
    
    def setUp(self):
        self.extractor = SmartWebExtractor(quiet=True)
    
    def test_extractor_creation(self):
        """Test extractor initialization."""
        self.assertIsNotNone(self.extractor.http)
        self.assertIsNotNone(self.extractor.analyzer)
        self.assertIsNotNone(self.extractor.exporter)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestColors))
    suite.addTests(loader.loadTestsFromTestCase(TestLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestDOMNode))
    suite.addTests(loader.loadTestsFromTestCase(TestSmartHTMLParser))
    suite.addTests(loader.loadTestsFromTestCase(TestContentAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestExportEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestSmartWebExtractor))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
