"""
AutoTestAI - HTML Analyzer
Parses HTML source code to extract web elements, locators, and page structure.
Generates a priority-based locator strategy map for test automation.
"""
import re
import logging
from typing import List, Optional, Dict, Set
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from app.models.schemas import ElementLocator, LocatorMap

logger = logging.getLogger(__name__)

# Elements that are typically interacted with in test automation
INTERACTIVE_TAGS = {
    "input", "button", "select", "textarea", "a",
    "option", "label", "form", "img", "video",
}

# Input types that represent interactive elements
INTERACTIVE_INPUT_TYPES = {
    "text", "password", "email", "number", "tel", "url", "search",
    "checkbox", "radio", "submit", "button", "file", "date",
    "datetime-local", "time", "month", "week", "range", "color",
}

# Attributes commonly used for locators
LOCATOR_ATTRIBUTES = [
    "data-testid", "data-test", "data-test-id", "data-cy",
    "id", "name", "aria-label", "aria-labelledby",
    "placeholder", "title", "alt", "value", "href", "type",
    "class", "role",
]


def _generate_css_selector(element: Tag) -> str:
    """Generate a CSS attribute selector for an element (Priority 3)."""
    tag = element.name

    # Check data-testid attributes
    for attr in ["data-testid", "data-test", "data-test-id", "data-cy"]:
        if element.get(attr):
            return f"[{attr}='{element[attr]}']"

    # Check name attribute
    if element.get("name"):
        return f"{tag}[name='{element['name']}']"

    # Check type for inputs
    if tag == "input" and element.get("type"):
        return f"input[type='{element['type']}']"

    # Check placeholder
    if element.get("placeholder"):
        return f"{tag}[placeholder='{element['placeholder']}']"

    # Check aria-label
    if element.get("aria-label"):
        return f"{tag}[aria-label='{element['aria-label']}']"

    # Check href for links
    if tag == "a" and element.get("href"):
        href = element["href"].split("?")[0]
        return f"a[href*='{href}']"

    # Check role
    if element.get("role"):
        return f"{tag}[role='{element['role']}']"

    return f"{tag}"


def _generate_xpath(element: Tag) -> str:
    """Generate an XPath locator for an element."""
    tag = element.name

    # Prefer id-based xpath
    if element.get("id"):
        return f"//{tag}[@id='{element['id']}']"

    # data-testid xpath
    if element.get("data-testid"):
        return f"//{tag}[@data-testid='{element['data-testid']}']"

    # name xpath
    if element.get("name"):
        return f"//{tag}[@name='{element['name']}']"

    # text-based xpath for buttons and links
    text = element.get_text(strip=True)
    if text and tag in ("button", "a", "label", "span", "h1", "h2", "h3"):
        if len(text) < 50:
            return f"//{tag}[contains(text(),'{text[:30]}')]"

    # Placeholder
    if element.get("placeholder"):
        return f"//{tag}[@placeholder='{element['placeholder']}']"

    # Fallback: class-based
    classes = element.get("class", [])
    if classes:
        return f"//{tag}[contains(@class,'{classes[0]}')]"

    return f"//{tag}"


def _build_locators(element: Tag) -> Dict[str, str]:
    """
    Build priority-ordered locator strategies for an element strictly following:
    1. ID (Highest priority)
    2. Class name
    3. CSS Selector
    4. XPath
    """
    locators = {}

    # Priority 1: ID
    elem_id = element.get("id")
    if elem_id and str(elem_id).strip():
        clean_id = str(elem_id).strip()
        locators["id"] = f"#{clean_id}"
        locators["raw_id"] = clean_id

    # Priority 2: Class name
    classes = element.get("class", [])
    if classes:
        if isinstance(classes, list):
            # Filter out generic layout classes (row, col, d-flex, etc.)
            filtered = [c.strip() for c in classes if c.strip() and not re.match(r"^(col|row|d-|m-|p-|w-|h-)\b", c.strip())]
            target_class = filtered[0] if filtered else classes[0].strip()
        else:
            target_class = str(classes).strip()
        
        if target_class:
            locators["class"] = f".{target_class}"
            locators["raw_class"] = target_class

    # Priority 3: CSS Selector
    css = _generate_css_selector(element)
    if css:
        locators["css"] = css

    # Priority 4: XPath
    xpath = _generate_xpath(element)
    if xpath:
        locators["xpath"] = xpath

    # Determine chosen primary locator strictly following user priority:
    # Priority 1: ID
    # Priority 2: Class name
    # Priority 3: CSS Selector
    # Priority 4: XPath
    if "id" in locators:
        locators["primary"] = locators["id"]
        locators["strategy"] = "ID"
    elif "class" in locators:
        locators["primary"] = locators["class"]
        locators["strategy"] = "Class name"
    elif "css" in locators:
        locators["primary"] = locators["css"]
        locators["strategy"] = "CSS Selector"
    elif "xpath" in locators:
        locators["primary"] = locators["xpath"]
        locators["strategy"] = "XPath"
    else:
        locators["primary"] = element.name
        locators["strategy"] = "Tag"

    return locators


def _extract_attributes(element: Tag) -> Dict[str, str]:
    """Extract relevant attributes from an element."""
    attrs = {}
    for attr in LOCATOR_ATTRIBUTES:
        val = element.get(attr)
        if val:
            if isinstance(val, list):
                attrs[attr] = " ".join(val)
            else:
                attrs[attr] = str(val)
    return attrs


def _get_element_description(element: Tag) -> str:
    """Generate a human-readable description of the element."""
    tag = element.name
    text = element.get_text(strip=True)[:50] if element.get_text(strip=True) else ""

    if tag == "input":
        input_type = element.get("type", "text")
        placeholder = element.get("placeholder", "")
        label = element.get("aria-label", "")
        name = element.get("name", "")
        desc = f"{input_type} input"
        if placeholder:
            desc += f" ({placeholder})"
        elif label:
            desc += f" ({label})"
        elif name:
            desc += f" ({name})"
        return desc
    elif tag == "button":
        return f"button '{text}'" if text else "button"
    elif tag == "a":
        return f"link '{text}'" if text else "link"
    elif tag == "select":
        name = element.get("name", "")
        return f"dropdown ({name})" if name else "dropdown"
    elif tag == "textarea":
        name = element.get("name", element.get("placeholder", ""))
        return f"textarea ({name})" if name else "textarea"
    elif tag == "form":
        action = element.get("action", "")
        return f"form ({action})" if action else "form"
    else:
        return f"{tag} '{text}'" if text else tag


def _is_interactive(element: Tag) -> bool:
    """Determine if an element is interactive/actionable or a key assertion element."""
    tag = element.name.lower()

    if tag in INTERACTIVE_TAGS:
        return True

    # Check for click handlers
    if any(element.get(attr) for attr in ["onclick", "ng-click", "@click", "v-on:click"]):
        return True

    # Check role attribute (interactive or alert)
    role = element.get("role", "").lower()
    if role in ("button", "link", "checkbox", "radio", "tab", "menuitem", "option", "alert", "status"):
        return True

    # Check for alerts, error messages, or key assertion elements
    classes = element.get("class", [])
    classes_str = " ".join(classes) if isinstance(classes, list) else str(classes)
    if any(k in classes_str.lower() for k in ["alert", "error", "toast", "message", "title", "header"]):
        return True

    if tag in ("h1", "h2", "h3"):
        return True

    # Check tabindex (makes element focusable/interactive)
    if element.get("tabindex") is not None:
        return True

    return False


def _extract_forms(soup: BeautifulSoup) -> List[Dict]:
    """Extract form structures from HTML."""
    forms = []
    for form in soup.find_all("form"):
        form_data = {
            "action": form.get("action", ""),
            "method": form.get("method", "GET").upper(),
            "id": form.get("id"),
            "name": form.get("name"),
            "fields": [],
        }

        for field in form.find_all(["input", "select", "textarea"]):
            field_info = {
                "tag": field.name,
                "type": field.get("type", "text") if field.name == "input" else field.name,
                "name": field.get("name"),
                "id": field.get("id"),
                "required": field.has_attr("required"),
                "placeholder": field.get("placeholder"),
            }
            form_data["fields"].append(field_info)

        forms.append(form_data)

    return forms


def analyze_html(
    html_content: str,
    source_url: Optional[str] = None,
    include_non_interactive: bool = False,
) -> LocatorMap:
    """
    Analyze HTML source code and extract element locators.

    Args:
        html_content: Raw HTML string
        source_url: URL the HTML was fetched from
        include_non_interactive: If True, include all visible elements (not just interactive)

    Returns:
        LocatorMap with all detected elements and their locator strategies
    """
    logger.info("Analyzing HTML content...")

    soup = BeautifulSoup(html_content, "lxml")

    # Extract page title
    title_tag = soup.find("title")
    page_title = title_tag.get_text(strip=True) if title_tag else None

    elements: List[ElementLocator] = []
    seen_ids: Set[str] = set()

    # Find all interactive elements
    for tag in soup.find_all(True):
        if not isinstance(tag, Tag):
            continue

        is_interactive = _is_interactive(tag)

        if not is_interactive and not include_non_interactive:
            continue

        # Skip hidden elements
        style = tag.get("style", "")
        if "display:none" in style.replace(" ", "") or "visibility:hidden" in style.replace(" ", ""):
            continue

        # Avoid duplicates
        elem_id = tag.get("id", "")
        if elem_id and elem_id in seen_ids:
            continue
        if elem_id:
            seen_ids.add(elem_id)

        locators = _build_locators(tag)
        attributes = _extract_attributes(tag)
        description = _get_element_description(tag)

        element = ElementLocator(
            tag=tag.name,
            element_type=tag.get("type") if tag.name == "input" else tag.name,
            text=tag.get_text(strip=True)[:100] if tag.get_text(strip=True) else None,
            locators=locators,
            attributes=attributes,
            is_interactive=is_interactive,
            description=description,
        )
        elements.append(element)

    # Extract forms
    forms = _extract_forms(soup)

    logger.info(
        f"HTML analysis complete: {len(elements)} elements, "
        f"{len(forms)} forms found"
    )

    return LocatorMap(
        source_url=source_url,
        page_title=page_title,
        elements=elements,
        forms=forms,
    )


def analyze_html_file(file_path: str) -> LocatorMap:
    """
    Analyze an HTML file and extract element locators.

    Args:
        file_path: Path to the HTML file

    Returns:
        LocatorMap with detected elements
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"HTML file not found: {file_path}")

    html_content = path.read_text(encoding="utf-8", errors="ignore")
    return analyze_html(html_content, source_url=f"file://{path}")
