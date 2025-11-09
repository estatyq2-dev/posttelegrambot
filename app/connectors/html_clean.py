"""HTML cleaning and text extraction."""

from bs4 import BeautifulSoup
from typing import Optional


def extract_text_from_html(html: str) -> str:
    """Extract clean text from HTML."""
    if not html:
        return ""
    
    soup = BeautifulSoup(html, "lxml")
    
    # Remove script and style elements
    for script in soup(["script", "style", "meta", "link"]):
        script.decompose()
    
    # Get text
    text = soup.get_text(separator="\n")
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)
    
    return text


def clean_html_tags(text: str) -> str:
    """Remove all HTML tags from text."""
    if not text:
        return ""
    
    soup = BeautifulSoup(text, "lxml")
    return soup.get_text()


def extract_links(html: str) -> list[str]:
    """Extract all links from HTML."""
    if not html:
        return []
    
    soup = BeautifulSoup(html, "lxml")
    links = []
    
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and href.startswith(("http://", "https://")):
            links.append(href)
    
    return links


def extract_images(html: str) -> list[str]:
    """Extract all image URLs from HTML."""
    if not html:
        return []
    
    soup = BeautifulSoup(html, "lxml")
    images = []
    
    for img in soup.find_all("img"):
        src = img.get("src")
        if src and src.startswith(("http://", "https://")):
            images.append(src)
    
    return images

