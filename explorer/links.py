"""Turn the identifiers inside a Reference citation into links.

Two kinds of link, neither guessed:
- identifiers inside the citation text that map to a URL by a fixed rule
  (BioNumbers IDs, DOIs, arXiv IDs and PubMed Central IDs), linked in place;
- the row's `Reference_URL` entries (space-separated pages that were fetched
  and checked against the citation), listed after the text by host name.
"""

import html
import re
from urllib.parse import urlsplit

# (pattern, URL template). Group "id" is substituted into the template; the
# whole match becomes the link text.
IDENTIFIER_LINKS = [
    (r"BioNumbers (?P<id>\d+)", "https://bionumbers.hms.harvard.edu/bionumber.aspx?id={id}"),
    (r"doi:(?P<id>10\.\d{4,9}/[^\s;,)]+[^\s;,).])", "https://doi.org/{id}"),
    (r"arXiv:(?P<id>\d{4}\.\d{4,5})", "https://arxiv.org/abs/{id}"),
    (r"(?P<id>PMC\d+)", "https://pmc.ncbi.nlm.nih.gov/articles/{id}"),
]

LINK_HTML = '<a href="{url}" target="_blank" rel="noopener">{text}</a>'


def identifier_urls(text):
    """URLs for every linkable identifier in `text`, in order of appearance."""
    found = []
    for pattern, template in IDENTIFIER_LINKS:
        found += [(m.start(), template.format(id=m.group("id"))) for m in re.finditer(pattern, text)]
    return [url for _, url in sorted(found)]


def linkify_reference(text):
    """HTML-escape a citation and wrap its linkable identifiers in anchors."""
    out = html.escape(text)
    for pattern, template in IDENTIFIER_LINKS:
        out = re.sub(
            pattern,
            lambda m, t=template: LINK_HTML.format(url=t.format(id=m.group("id")), text=m.group(0)),
            out,
        )
    return out


def host_label(url):
    """Link text for a source URL: its host without a leading 'www.'."""
    return re.sub(r"^www\.", "", urlsplit(url).netloc)


def source_links_html(urls):
    """Anchors for a row's checked source pages, labelled by host."""
    return " · ".join(LINK_HTML.format(url=html.escape(u), text=host_label(u)) for u in urls)


def reference_html(text, urls):
    """Citation with identifier links in place, then the row's source pages."""
    out = linkify_reference(text)
    if urls:
        out += "<br>Source pages: " + source_links_html(urls)
    return out
