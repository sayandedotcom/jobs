from pipeline.sources.hackernews.parser import (
    extract_header_line,
    hn_html_to_plain,
)


def test_hackernews_header_extraction():
    html = """
    <p>Acme | Senior Backend Engineer | Remote</p>
    <p>Build APIs and data pipelines.</p>
    <p><a href="https://jobs.acme.com/backend">Apply here</a></p>
    """

    plain_text = hn_html_to_plain(html)

    assert extract_header_line(plain_text) == (
        "Acme | Senior Backend Engineer | Remote"
    )


def test_hackernews_header_extraction_handles_bullet_prefixes():
    comment = "- Example Corp | Staff Product Designer | Hybrid"

    assert extract_header_line(comment) == (
        "Example Corp | Staff Product Designer | Hybrid"
    )
