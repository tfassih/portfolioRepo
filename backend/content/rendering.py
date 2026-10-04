import markdown
import nh3

TAGS = {
    "p",
    "br",
    "strong",
    "em",
    "blockquote",
    "ul",
    "ol",
    "li",
    "h2",
    "h3",
    "h4",
    "pre",
    "code",
    "a",
    "hr",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
}


def rich_text(value):
    html = markdown.markdown(value or "", extensions=["fenced_code", "tables"])
    return nh3.clean(
        html,
        tags=TAGS,
        attributes={"a": {"href", "title"}},
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer",
    )
