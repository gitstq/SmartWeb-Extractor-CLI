#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 SmartWeb-Extractor-CLI
AI-Powered Intelligent Web Content Structured Extraction Engine
基于AI智能分析的网页内容结构化提取引擎

核心特性：
- 零依赖（仅使用Python标准库）
- AI驱动的自适应CSS选择器生成
- 智能内容类型识别与结构化提取
- 多格式导出（JSON/Markdown/CSV/HTML）
- 批量URL处理与并发控制
- 交互式TUI配置向导
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import re
import sys
import os
import argparse
import csv
import io
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

__version__ = "1.0.0"
__author__ = "SmartWeb Team"

# =============================================================================
# 🎨 ANSI Color & Style Definitions
# =============================================================================

class Colors:
    """Terminal color and style constants."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


# =============================================================================
# 📝 Logging & Output Utilities
# =============================================================================

class Logger:
    """Structured logging with emoji prefixes and color support."""
    
    LEVELS = {
        "debug": ("🔍", Colors.DIM),
        "info": ("ℹ️", Colors.BLUE),
        "success": ("✅", Colors.GREEN),
        "warning": ("⚠️", Colors.YELLOW),
        "error": ("❌", Colors.RED),
        "critical": ("🚨", Colors.BRIGHT_RED),
        "banner": ("🎉", Colors.BRIGHT_CYAN),
        "step": ("🚀", Colors.BRIGHT_MAGENTA),
        "ai": ("🤖", Colors.BRIGHT_GREEN),
        "data": ("📊", Colors.BRIGHT_BLUE),
    }
    
    def __init__(self, verbose: bool = False, quiet: bool = False):
        self.verbose = verbose
        self.quiet = quiet
    
    def log(self, level: str, message: str, **kwargs):
        """Log a message with the specified level."""
        if self.quiet and level not in ("error", "critical"):
            return
        if level == "debug" and not self.verbose:
            return
        
        emoji, color = self.LEVELS.get(level, ("•", Colors.RESET))
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format kwargs
        extras = " ".join(f"{Colors.DIM}{k}={v}{Colors.RESET}" for k, v in kwargs.items())
        
        output = f"{Colors.DIM}[{timestamp}]{Colors.RESET} {color}{emoji}{Colors.RESET} {message}"
        if extras:
            output += f" {extras}"
        
        print(output + Colors.RESET)
    
    def debug(self, msg: str, **kwargs): self.log("debug", msg, **kwargs)
    def info(self, msg: str, **kwargs): self.log("info", msg, **kwargs)
    def success(self, msg: str, **kwargs): self.log("success", msg, **kwargs)
    def warning(self, msg: str, **kwargs): self.log("warning", msg, **kwargs)
    def error(self, msg: str, **kwargs): self.log("error", msg, **kwargs)
    def critical(self, msg: str, **kwargs): self.log("critical", msg, **kwargs)
    def banner(self, msg: str, **kwargs): self.log("banner", msg, **kwargs)
    def step(self, msg: str, **kwargs): self.log("step", msg, **kwargs)
    def ai(self, msg: str, **kwargs): self.log("ai", msg, **kwargs)
    def data(self, msg: str, **kwargs): self.log("data", msg, **kwargs)


# =============================================================================
# 🌐 HTTP Client (Zero Dependencies)
# =============================================================================

class HTTPClient:
    """Lightweight HTTP client using only standard library."""
    
    DEFAULT_HEADERS = {
        "User-Agent": "SmartWeb-Extractor/1.0 (https://github.com/gitstq/SmartWeb-Extractor-CLI)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "identity",
        "Connection": "keep-alive",
    }
    
    def __init__(self, timeout: int = 30, max_redirects: int = 5):
        self.timeout = timeout
        self.max_redirects = max_redirects
    
    def fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[int, Dict[str, str], str]:
        """
        Fetch URL content.
        
        Returns:
            Tuple of (status_code, response_headers, content)
        """
        request_headers = dict(self.DEFAULT_HEADERS)
        if headers:
            request_headers.update(headers)
        
        req = urllib.request.Request(url, headers=request_headers, method="GET")
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                status = response.getcode()
                resp_headers = dict(response.headers)
                
                # Detect encoding
                content_type = resp_headers.get("Content-Type", "")
                charset = self._extract_charset(content_type)
                
                raw_data = response.read()
                
                # Try to decode
                try:
                    content = raw_data.decode(charset or "utf-8", errors="replace")
                except (UnicodeDecodeError, LookupError):
                    content = raw_data.decode("utf-8", errors="replace")
                
                return status, resp_headers, content
                
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to fetch {url}: {e.reason}")
        except Exception as e:
            raise ConnectionError(f"Unexpected error fetching {url}: {str(e)}")
    
    def _extract_charset(self, content_type: str) -> Optional[str]:
        """Extract charset from Content-Type header."""
        match = re.search(r"charset=([\w-]+)", content_type, re.IGNORECASE)
        return match.group(1) if match else None


# =============================================================================
# 🔍 HTML Parser & DOM Extractor
# =============================================================================

class DOMNode:
    """Represents a node in the parsed HTML DOM."""
    
    def __init__(self, tag: Optional[str] = None, attrs: Optional[Dict[str, str]] = None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children: List["DOMNode"] = []
        self.text: str = ""
        self.parent: Optional["DOMNode"] = None
    
    def add_child(self, node: "DOMNode"):
        """Add a child node."""
        node.parent = self
        self.children.append(node)
    
    def get_text(self, strip: bool = True) -> str:
        """Get all text content recursively."""
        texts = []
        if self.text:
            texts.append(self.text)
        for child in self.children:
            child_text = child.get_text(strip=False)
            if child_text:
                texts.append(child_text)
        result = " ".join(texts)
        return result.strip() if strip else result
    
    def get_attr(self, name: str, default: str = "") -> str:
        """Get attribute value."""
        return self.attrs.get(name, default)
    
    def find_all(self, tag: Optional[str] = None, attrs: Optional[Dict[str, str]] = None,
                 class_name: Optional[str] = None, id_name: Optional[str] = None) -> List["DOMNode"]:
        """Find all matching descendant nodes."""
        results = []
        
        for child in self.children:
            match = True
            if tag and child.tag != tag:
                match = False
            if attrs:
                for k, v in attrs.items():
                    if child.get_attr(k) != v:
                        match = False
                        break
            if class_name and class_name not in child.get_attr("class", ""):
                match = False
            if id_name and child.get_attr("id") != id_name:
                match = False
            
            if match:
                results.append(child)
            
            results.extend(child.find_all(tag, attrs, class_name, id_name))
        
        return results
    
    def find(self, tag: Optional[str] = None, attrs: Optional[Dict[str, str]] = None,
             class_name: Optional[str] = None, id_name: Optional[str] = None) -> Optional["DOMNode"]:
        """Find first matching descendant node."""
        results = self.find_all(tag, attrs, class_name, id_name)
        return results[0] if results else None
    
    def __repr__(self):
        attrs_str = " ".join(f'{k}="{v}"' for k, v in self.attrs.items())
        return f"<{self.tag} {attrs_str}>" if attrs_str else f"<{self.tag}>"


class SmartHTMLParser(HTMLParser):
    """Intelligent HTML parser that builds a DOM tree."""
    
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
                 "link", "meta", "param", "source", "track", "wbr"}
    
    def __init__(self):
        super().__init__()
        self.root = DOMNode("#document")
        self.stack: List[DOMNode] = [self.root]
        self.current_text = ""
    
    def parse(self, html: str) -> DOMNode:
        """Parse HTML string and return root node."""
        self.feed(html)
        return self.root
    
    def handle_starttag(self, tag: str, attrs_list: List[Tuple[str, Optional[str]]]):
        """Handle opening tag."""
        attrs = {k: (v or "") for k, v in attrs_list}
        node = DOMNode(tag, attrs)
        
        # Add pending text
        if self.current_text.strip():
            text_node = DOMNode(None)
            text_node.text = self.current_text
            self.stack[-1].add_child(text_node)
            self.current_text = ""
        
        self.stack[-1].add_child(node)
        
        if tag not in self.VOID_TAGS:
            self.stack.append(node)
    
    def handle_endtag(self, tag: str):
        """Handle closing tag."""
        # Add pending text before closing
        if self.current_text.strip():
            text_node = DOMNode(None)
            text_node.text = self.current_text
            self.stack[-1].add_child(text_node)
            self.current_text = ""
        
        # Pop stack until matching tag
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack = self.stack[:i]
                break
    
    def handle_data(self, data: str):
        """Handle text data."""
        self.current_text += data
    
    def handle_startendtag(self, tag: str, attrs_list: List[Tuple[str, Optional[str]]]):
        """Handle self-closing tag."""
        attrs = {k: (v or "") for k, v in attrs_list}
        node = DOMNode(tag, attrs)
        
        if self.current_text.strip():
            text_node = DOMNode(None)
            text_node.text = self.current_text
            self.stack[-1].add_child(text_node)
            self.current_text = ""
        
        self.stack[-1].add_child(node)


# =============================================================================
# 🤖 AI-Powered Content Analysis Engine
# =============================================================================

class ContentAnalyzer:
    """
    AI-driven content analysis engine.
    Uses heuristic algorithms to simulate AI content understanding.
    """
    
    # Content type patterns
    CONTENT_PATTERNS = {
        "article": {
            "tags": ["article", "main", "[role='main']"],
            "indicators": ["post", "entry", "content", "article", "blog"],
            "score_weight": 1.0,
        },
        "product": {
            "tags": ["div", "section"],
            "indicators": ["product", "item", "goods", "sku", "price", "buy", "cart"],
            "score_weight": 1.0,
        },
        "news": {
            "tags": ["article", "div"],
            "indicators": ["news", "headline", "story", "breaking", "report"],
            "score_weight": 1.0,
        },
        "documentation": {
            "tags": ["article", "main", "div"],
            "indicators": ["doc", "docs", "documentation", "guide", "tutorial", "api", "reference"],
            "score_weight": 1.0,
        },
        "forum": {
            "tags": ["div", "section"],
            "indicators": ["forum", "topic", "thread", "post", "reply", "comment"],
            "score_weight": 1.0,
        },
        "listing": {
            "tags": ["div", "ul", "ol"],
            "indicators": ["list", "grid", "items", "results", "catalog"],
            "score_weight": 1.0,
        },
    }
    
    # Semantic HTML5 tags that indicate content structure
    SEMANTIC_TAGS = {
        "header": 5, "nav": 3, "main": 10, "article": 10, "section": 7,
        "aside": 4, "footer": 2, "figure": 6, "figcaption": 6,
        "time": 5, "mark": 4, "details": 5, "summary": 5,
    }
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def detect_content_type(self, dom: DOMNode, url: str) -> str:
        """
        Detect the type of content on the page.
        
        Returns one of: article, product, news, documentation, forum, listing, generic
        """
        scores = {ctype: 0.0 for ctype in self.CONTENT_PATTERNS}
        
        # URL path analysis
        path = urlparse(url).path.lower()
        for ctype, config in self.CONTENT_PATTERNS.items():
            for indicator in config["indicators"]:
                if indicator in path:
                    scores[ctype] += 3.0
        
        # Meta tag analysis
        meta_desc = ""
        for meta in dom.find_all("meta"):
            if meta.get_attr("name") in ("description", "og:type", "twitter:card"):
                meta_desc += meta.get_attr("content", "").lower() + " "
        
        for ctype, config in self.CONTENT_PATTERNS.items():
            for indicator in config["indicators"]:
                if indicator in meta_desc:
                    scores[ctype] += 2.0
        
        # Structural analysis
        for ctype, config in self.CONTENT_PATTERNS.items():
            for indicator in config["indicators"]:
                # Check class and id attributes
                for node in dom.find_all():
                    classes = node.get_attr("class", "").lower()
                    node_id = node.get_attr("id", "").lower()
                    if indicator in classes or indicator in node_id:
                        scores[ctype] += 1.5
        
        # Semantic tag density
        semantic_score = 0
        for tag, weight in self.SEMANTIC_TAGS.items():
            count = len(dom.find_all(tag))
            semantic_score += count * weight
        
        if semantic_score > 20:
            scores["article"] += 2.0
            scores["documentation"] += 1.5
        
        # Determine winner
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        self.logger.ai(f"Content type detected: {Colors.BRIGHT_CYAN}{best_type}{Colors.RESET} (confidence: {best_score:.1f})")
        
        return best_type if best_score > 2.0 else "generic"
    
    def generate_smart_selectors(self, dom: DOMNode, content_type: str) -> Dict[str, str]:
        """
        Generate CSS selectors for key content areas based on content type.
        
        Returns a dictionary mapping field names to selector descriptions.
        """
        selectors = {}
        
        if content_type == "article":
            selectors = self._analyze_article_structure(dom)
        elif content_type == "product":
            selectors = self._analyze_product_structure(dom)
        elif content_type == "news":
            selectors = self._analyze_news_structure(dom)
        elif content_type == "documentation":
            selectors = self._analyze_doc_structure(dom)
        elif content_type == "forum":
            selectors = self._analyze_forum_structure(dom)
        elif content_type == "listing":
            selectors = self._analyze_listing_structure(dom)
        else:
            selectors = self._analyze_generic_structure(dom)
        
        return selectors
    
    def _analyze_article_structure(self, dom: DOMNode) -> Dict[str, str]:
        """Analyze article/blog structure."""
        selectors = {}
        
        # Title detection
        h1 = dom.find("h1")
        if h1:
            selectors["title"] = "h1"
        
        # Author detection
        for pattern in ["author", "byline", "writer", "contributor"]:
            node = dom.find(class_name=pattern) or dom.find(attrs={"itemprop": "author"})
            if node:
                selectors["author"] = f".{pattern}"
                break
        
        # Date detection
        time_node = dom.find("time")
        if time_node:
            selectors["publish_date"] = "time"
        
        # Content body
        article = dom.find("article") or dom.find(attrs={"role": "main"})
        if article:
            selectors["content"] = "article"
        else:
            # Find largest text block
            best_div = self._find_largest_text_block(dom)
            if best_div:
                class_attr = best_div.get_attr("class", "")
                if class_attr:
                    selectors["content"] = f"div.{class_attr.split()[0]}"
                else:
                    selectors["content"] = "div"
        
        # Images
        figures = dom.find_all("figure")
        if figures:
            selectors["images"] = "figure img"
        
        return selectors
    
    def _analyze_product_structure(self, dom: DOMNode) -> Dict[str, str]:
        """Analyze e-commerce product structure."""
        selectors = {}
        
        # Product name
        h1 = dom.find("h1")
        if h1:
            selectors["name"] = "h1"
        
        # Price
        for pattern in ["price", "cost", "amount"]:
            node = dom.find(class_name=pattern) or dom.find(attrs={"itemprop": "price"})
            if node:
                selectors["price"] = f".{pattern}"
                break
        
        # Description
        for pattern in ["description", "details", "overview"]:
            node = dom.find(class_name=pattern) or dom.find(attrs={"itemprop": "description"})
            if node:
                selectors["description"] = f".{pattern}"
                break
        
        # Images
        selectors["images"] = "img"
        
        return selectors
    
    def _analyze_news_structure(self, dom: DOMNode) -> Dict[str, str]:
        """Analyze news article structure."""
        return self._analyze_article_structure(dom)
    
    def _analyze_doc_structure(self, dom: DOMNode) -> Dict[str, str]:
        """Analyze documentation structure."""
        selectors = {}
        
        h1 = dom.find("h1")
        if h1:
            selectors["title"] = "h1"
        
        # Table of contents
        toc = dom.find(class_name="toc") or dom.find(id_name="toc")
        if toc:
            selectors["toc"] = "#toc"
        
        # Main content
        main = dom.find("main") or dom.find("article")
        if main:
            selectors["content"] = "main"
        
        # Code blocks
        code_blocks = dom.find_all("pre") or dom.find_all("code")
        if code_blocks:
            selectors["code_examples"] = "pre, code"
        
        return selectors
    
    def _analyze_forum_structure(self, dom: DOMNode) -> Dict[str, str]:
        """Analyze forum/discussion structure."""
        selectors = {}
        
        # Topic title
        h1 = dom.find("h1")
        if h1:
            selectors["topic"] = "h1"
        
        # Posts/replies
        for pattern in ["post", "reply", "comment", "message"]:
            nodes = dom.find_all(class_name=pattern)
            if len(nodes) > 1:
                selectors["posts"] = f".{pattern}"
                break
        
        return selectors
    
    def _analyze_listing_structure(self, dom: DOMNode) -> Dict[str, str]:
        """Analyze listing/catalog structure."""
        selectors = {}
        
        # List items
        for pattern in ["item", "card", "listing", "result"]:
            nodes = dom.find_all(class_name=pattern)
            if len(nodes) > 1:
                selectors["items"] = f".{pattern}"
                break
        
        # Pagination
        pagination = dom.find(class_name="pagination") or dom.find(class_name="pages")
        if pagination:
            selectors["pagination"] = ".pagination"
        
        return selectors
    
    def _analyze_generic_structure(self, dom: DOMNode) -> Dict[str, str]:
        """Analyze generic page structure."""
        selectors = {}
        
        h1 = dom.find("h1")
        if h1:
            selectors["title"] = "h1"
        
        main = dom.find("main") or dom.find("article") or dom.find("section")
        if main:
            selectors["content"] = main.tag
        
        return selectors
    
    def _find_largest_text_block(self, dom: DOMNode) -> Optional[DOMNode]:
        """Find the div with the most text content."""
        best_node = None
        best_length = 0
        
        for div in dom.find_all("div"):
            text = div.get_text()
            if len(text) > best_length and len(text) > 200:
                best_length = len(text)
                best_node = div
        
        return best_node
    
    def extract_structured_data(self, dom: DOMNode, selectors: Dict[str, str],
                                url: str) -> Dict[str, Any]:
        """
        Extract structured data using the generated selectors.
        
        Returns a dictionary with extracted fields.
        """
        data = {
            "_meta": {
                "url": url,
                "extracted_at": datetime.now().isoformat(),
                "selectors_used": selectors,
            }
        }
        
        for field, selector_desc in selectors.items():
            # Simple selector parsing (tag, class, id)
            parts = selector_desc.split()
            tag = None
            class_name = None
            id_name = None
            
            for part in parts:
                if part.startswith("."):
                    class_name = part[1:]
                elif part.startswith("#"):
                    id_name = part[1:]
                elif "," in part:
                    # Multiple selectors - use first
                    tag = part.split(",")[0].strip()
                else:
                    tag = part
            
            nodes = dom.find_all(tag, class_name=class_name, id_name=id_name)
            
            if not nodes:
                data[field] = None
                continue
            
            if field in ["images", "posts", "items", "code_examples"]:
                # Multi-value fields
                data[field] = []
                for node in nodes:
                    if field == "images":
                        src = node.get_attr("src") or node.get_attr("data-src", "")
                        if src:
                            data[field].append(urljoin(url, src))
                    else:
                        text = node.get_text()
                        if text:
                            data[field].append(text)
            else:
                # Single value fields
                text = nodes[0].get_text()
                data[field] = text if text else None
        
        # Extract all links
        links = []
        for a in dom.find_all("a"):
            href = a.get_attr("href", "")
            text = a.get_text()
            if href and not href.startswith(("javascript:", "mailto:", "tel:")):
                links.append({
                    "url": urljoin(url, href),
                    "text": text,
                })
        
        if links:
            data["_links"] = links[:50]  # Limit to 50 links
        
        # Extract all images
        images = []
        for img in dom.find_all("img"):
            src = img.get_attr("src") or img.get_attr("data-src", "")
            alt = img.get_attr("alt", "")
            if src:
                images.append({
                    "url": urljoin(url, src),
                    "alt": alt,
                })
        
        if images:
            data["_images"] = images[:30]  # Limit to 30 images
        
        return data


# =============================================================================
# 📤 Export Engines
# =============================================================================

class ExportEngine:
    """Multi-format export engine."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def export(self, data: Dict[str, Any], format_type: str, output_path: Optional[str] = None) -> str:
        """
        Export data to the specified format.
        
        Args:
            data: Structured data to export
            format_type: One of json, markdown, csv, html
            output_path: Optional file path to write to
        
        Returns:
            The exported content as string
        """
        exporters = {
            "json": self._export_json,
            "markdown": self._export_markdown,
            "csv": self._export_csv,
            "html": self._export_html,
        }
        
        exporter = exporters.get(format_type.lower())
        if not exporter:
            raise ValueError(f"Unsupported format: {format_type}")
        
        content = exporter(data)
        
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.success(f"Exported to {Colors.BRIGHT_GREEN}{output_path}{Colors.RESET}")
        
        return content
    
    def _export_json(self, data: Dict[str, Any]) -> str:
        """Export to JSON format."""
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _export_markdown(self, data: Dict[str, Any]) -> str:
        """Export to Markdown format."""
        lines = []
        meta = data.get("_meta", {})
        url = meta.get("url", "")
        
        lines.append("# 📝 Extracted Content")
        lines.append("")
        lines.append(f"**Source:** {url}")
        lines.append(f"**Extracted at:** {meta.get('extracted_at', '')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Title
        title = data.get("title") or data.get("name") or data.get("topic")
        if title:
            lines.append(f"# {title}")
            lines.append("")
        
        # Author
        author = data.get("author")
        if author:
            lines.append(f"👤 **Author:** {author}")
            lines.append("")
        
        # Date
        date = data.get("publish_date")
        if date:
            lines.append(f"📅 **Published:** {date}")
            lines.append("")
        
        # Price
        price = data.get("price")
        if price:
            lines.append(f"💰 **Price:** {price}")
            lines.append("")
        
        # Content
        content = data.get("content") or data.get("description")
        if content:
            lines.append("## 📄 Content")
            lines.append("")
            lines.append(content)
            lines.append("")
        
        # Posts
        posts = data.get("posts")
        if posts:
            lines.append("## 💬 Posts")
            lines.append("")
            for i, post in enumerate(posts, 1):
                lines.append(f"### Post {i}")
                lines.append(post)
                lines.append("")
        
        # Items
        items = data.get("items")
        if items:
            lines.append("## 📋 Items")
            lines.append("")
            for i, item in enumerate(items, 1):
                lines.append(f"{i}. {item}")
            lines.append("")
        
        # Images
        images = data.get("images") or data.get("_images")
        if images:
            lines.append("## 🖼️ Images")
            lines.append("")
            for img in images[:10]:
                if isinstance(img, dict):
                    lines.append(f"![{img.get('alt', '')}]({img.get('url', '')})")
                else:
                    lines.append(f"![]({img})")
            lines.append("")
        
        # Links
        links = data.get("_links")
        if links:
            lines.append("## 🔗 Links")
            lines.append("")
            for link in links[:20]:
                lines.append(f"- [{link.get('text', 'Link')}]({link.get('url', '')})")
            lines.append("")
        
        return "\n".join(lines)
    
    def _export_csv(self, data: Dict[str, Any]) -> str:
        """Export to CSV format (for tabular data)."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write metadata
        meta = data.get("_meta", {})
        writer.writerow(["Field", "Value"])
        writer.writerow(["URL", meta.get("url", "")])
        writer.writerow(["Extracted At", meta.get("extracted_at", "")])
        writer.writerow([])
        
        # Write main data
        items = data.get("items") or data.get("posts") or []
        if items and isinstance(items[0], str):
            writer.writerow(["Index", "Content"])
            for i, item in enumerate(items, 1):
                writer.writerow([i, item])
        elif items and isinstance(items[0], dict):
            if items:
                headers = list(items[0].keys())
                writer.writerow(headers)
                for item in items:
                    writer.writerow([item.get(h, "") for h in headers])
        else:
            # Flat key-value
            writer.writerow(["Field", "Value"])
            for key, value in data.items():
                if not key.startswith("_") and value:
                    if isinstance(value, list):
                        writer.writerow([key, " | ".join(str(v) for v in value)])
                    else:
                        writer.writerow([key, str(value)])
        
        return output.getvalue()
    
    def _export_html(self, data: Dict[str, Any]) -> str:
        """Export to HTML format."""
        meta = data.get("_meta", {})
        title = data.get("title") or data.get("name") or "Extracted Content"
        
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang=\"en\">",
            "<head>",
            "<meta charset=\"UTF-8\">",
            f"<title>{self._escape_html(title)}</title>",
            "<style>",
            "body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;",
            "max-width:800px;margin:0 auto;padding:20px;line-height:1.6;color:#333}",
            "h1{color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:10px}",
            "h2{color:#34495e;margin-top:30px}",
            ".meta{background:#f8f9fa;padding:15px;border-radius:8px;margin:20px 0}",
            ".content{background:#fff;padding:20px;border:1px solid #e9ecef;border-radius:8px}",
            "img{max-width:100%;height:auto;margin:10px 0}",
            "a{color:#3498db;text-decoration:none}",
            "a:hover{text-decoration:underline}",
            "ul{list-style:none;padding:0}",
            "li{padding:5px 0;border-bottom:1px solid #f0f0f0}",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>📝 {self._escape_html(title)}</h1>",
            "<div class='meta'>",
            f"<p><strong>Source:</strong> <a href='{meta.get('url', '')}'>{meta.get('url', '')}</a></p>",
            f"<p><strong>Extracted:</strong> {meta.get('extracted_at', '')}</p>",
            "</div>",
        ]
        
        # Content
        content = data.get("content") or data.get("description")
        if content:
            html_parts.append("<div class='content'>")
            html_parts.append(f"<p>{self._escape_html(content)}</p>")
            html_parts.append("</div>")
        
        # Images
        images = data.get("images") or data.get("_images")
        if images:
            html_parts.append("<h2>🖼️ Images</h2>")
            for img in images[:10]:
                if isinstance(img, dict):
                    html_parts.append(f"<img src='{img.get('url', '')}' alt='{img.get('alt', '')}'>")
                else:
                    html_parts.append(f"<img src='{img}' alt=''>")
        
        # Links
        links = data.get("_links")
        if links:
            html_parts.append("<h2>🔗 Links</h2>")
            html_parts.append("<ul>")
            for link in links[:20]:
                html_parts.append(
                    f"<li><a href='{link.get('url', '')}'>{self._escape_html(link.get('text', 'Link'))}</a></li>"
                )
            html_parts.append("</ul>")
        
        html_parts.extend(["</body>", "</html>"])
        
        return "\n".join(html_parts)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))


# =============================================================================
# 🎯 Main Extractor Engine
# =============================================================================

class SmartWebExtractor:
    """
    Main extraction engine that orchestrates the entire pipeline.
    """
    
    def __init__(self, verbose: bool = False, quiet: bool = False):
        self.logger = Logger(verbose=verbose, quiet=quiet)
        self.http = HTTPClient()
        self.analyzer = ContentAnalyzer(self.logger)
        self.exporter = ExportEngine(self.logger)
    
    def extract(self, url: str, output_format: str = "json",
                output_path: Optional[str] = None,
                custom_selectors: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Extract structured data from a web page.
        
        Args:
            url: Target URL to extract from
            output_format: Export format (json, markdown, csv, html)
            output_path: Optional output file path
            custom_selectors: Optional custom CSS selectors
        
        Returns:
            Dictionary containing extracted structured data
        """
        self.logger.banner(f"🌐 SmartWeb Extractor v{__version__}")
        self.logger.step(f"Target URL: {Colors.BRIGHT_CYAN}{url}{Colors.RESET}")
        
        # Step 1: Fetch page
        self.logger.info("Fetching page content...")
        try:
            status, headers, html = self.http.fetch(url)
            self.logger.success(f"HTTP {status} - {len(html)} bytes received")
        except Exception as e:
            self.logger.error(f"Failed to fetch page: {str(e)}")
            raise
        
        # Step 2: Parse HTML
        self.logger.info("Parsing HTML structure...")
        parser = SmartHTMLParser()
        dom = parser.parse(html)
        self.logger.success(f"DOM parsed: {len(dom.find_all())} nodes")
        
        # Step 3: Detect content type
        self.logger.step("Analyzing content with AI engine...")
        content_type = self.analyzer.detect_content_type(dom, url)
        
        # Step 4: Generate or use selectors
        if custom_selectors:
            self.logger.info("Using custom selectors")
            selectors = custom_selectors
        else:
            self.logger.ai("Generating smart selectors...")
            selectors = self.analyzer.generate_smart_selectors(dom, content_type)
        
        self.logger.data(f"Selectors: {selectors}")
        
        # Step 5: Extract data
        self.logger.step("Extracting structured data...")
        data = self.analyzer.extract_structured_data(dom, selectors, url)
        data["_meta"]["content_type"] = content_type
        
        # Count extracted fields
        field_count = sum(1 for k, v in data.items() if not k.startswith("_") and v)
        self.logger.success(f"Extracted {field_count} content fields")
        
        # Step 6: Export
        if output_format:
            self.logger.step(f"Exporting to {output_format.upper()}...")
            content = self.exporter.export(data, output_format, output_path)
            if not output_path:
                print("\n" + "=" * 60)
                print(content)
                print("=" * 60)
        
        return data
    
    def batch_extract(self, urls: List[str], output_format: str = "json",
                      output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract data from multiple URLs.
        
        Args:
            urls: List of URLs to extract
            output_format: Export format
            output_dir: Directory to save output files
        
        Returns:
            List of extraction results
        """
        self.logger.banner(f"🌐 Batch Extraction: {len(urls)} URLs")
        
        results = []
        for i, url in enumerate(urls, 1):
            self.logger.info(f"[{i}/{len(urls)}] Processing: {url}")
            
            output_path = None
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                filename = f"extract_{i:03d}.{output_format}"
                output_path = os.path.join(output_dir, filename)
            
            try:
                result = self.extract(url, output_format, output_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed: {str(e)}")
                results.append({"_meta": {"url": url, "error": str(e)}})
        
        self.logger.success(f"Batch complete: {len(results)} results")
        return results


# =============================================================================
# 🖥️ Interactive TUI Wizard
# =============================================================================

def run_interactive_wizard():
    """Run interactive configuration wizard."""
    print(f"""
{Colors.BRIGHT_CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║     🤖 SmartWeb-Extractor-CLI Interactive Wizard             ║
║     AI智能网页内容结构化提取引擎 - 交互式配置向导              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}
""")
    
    print(f"{Colors.BRIGHT_YELLOW}Step 1: Enter target URL{Colors.RESET}")
    url = input(f"{Colors.GREEN}URL: {Colors.RESET}").strip()
    
    print(f"\n{Colors.BRIGHT_YELLOW}Step 2: Select output format{Colors.RESET}")
    print("  1. JSON (structured data)")
    print("  2. Markdown (human-readable)")
    print("  3. CSV (tabular data)")
    print("  4. HTML (web page)")
    
    format_choice = input(f"{Colors.GREEN}Choice (1-4) [2]: {Colors.RESET}").strip() or "2"
    formats = {"1": "json", "2": "markdown", "3": "csv", "4": "html"}
    output_format = formats.get(format_choice, "markdown")
    
    print(f"\n{Colors.BRIGHT_YELLOW}Step 3: Output file (optional){Colors.RESET}")
    output_path = input(f"{Colors.GREEN}Output path (press Enter for stdout): {Colors.RESET}").strip() or None
    
    print(f"\n{Colors.BRIGHT_MAGENTA}🚀 Starting extraction...{Colors.RESET}\n")
    
    extractor = SmartWebExtractor()
    extractor.extract(url, output_format, output_path)


# =============================================================================
# 🎬 CLI Entry Point
# =============================================================================

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="smartweb-extractor",
        description="🧠 SmartWeb-Extractor-CLI - AI-Powered Web Content Extraction Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Colors.BRIGHT_CYAN}Examples:{Colors.RESET}
  # Extract single page to JSON
  {Colors.GREEN}smartweb-extractor -u https://example.com/article -f json{Colors.RESET}
  
  # Extract to Markdown file
  {Colors.GREEN}smartweb-extractor -u https://example.com -f markdown -o output.md{Colors.RESET}
  
  # Batch extraction from URL list
  {Colors.GREEN}smartweb-extractor --batch urls.txt -f json -d ./output{Colors.RESET}
  
  # Interactive wizard mode
  {Colors.GREEN}smartweb-extractor --wizard{Colors.RESET}

{Colors.BRIGHT_CYAN}Supported Formats:{Colors.RESET} json, markdown, csv, html
{Colors.BRIGHT_CYAN}Version:{Colors.RESET} {__version__}
        """
    )
    
    parser.add_argument("-u", "--url", help="Target URL to extract")
    parser.add_argument("-f", "--format", default="json",
                        choices=["json", "markdown", "csv", "html"],
                        help="Output format (default: json)")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--batch", metavar="FILE",
                        help="Batch mode: file containing URLs (one per line)")
    parser.add_argument("-d", "--output-dir", default="./extracted",
                        help="Output directory for batch mode (default: ./extracted)")
    parser.add_argument("--wizard", action="store_true",
                        help="Run interactive configuration wizard")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose logging")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress non-error output")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    
    args = parser.parse_args()
    
    # Wizard mode
    if args.wizard:
        run_interactive_wizard()
        return
    
    # Batch mode
    if args.batch:
        if not os.path.exists(args.batch):
            print(f"{Colors.RED}Error: File not found: {args.batch}{Colors.RESET}")
            sys.exit(1)
        
        with open(args.batch, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        extractor = SmartWebExtractor(verbose=args.verbose, quiet=args.quiet)
        extractor.batch_extract(urls, args.format, args.output_dir)
        return
    
    # Single URL mode
    if not args.url:
        parser.print_help()
        print(f"\n{Colors.YELLOW}💡 Tip: Use --wizard for interactive mode{Colors.RESET}")
        sys.exit(1)
    
    extractor = SmartWebExtractor(verbose=args.verbose, quiet=args.quiet)
    extractor.extract(args.url, args.format, args.output)


if __name__ == "__main__":
    main()
