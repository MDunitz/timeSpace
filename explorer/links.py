"""Turn the identifiers inside a Reference citation into links.

The reference-objects CSV stores citations as plain text with no URLs.
Only identifiers that map to a URL by a fixed rule are linked, so no link
target is guessed: BioNumbers IDs, DOIs, arXiv IDs and PubMed Central IDs.
"""

import html
import re

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
