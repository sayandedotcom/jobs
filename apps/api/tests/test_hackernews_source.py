from pipeline.sources.hackernews import (
    _extract_company_from_comment,
    _extract_first_external_url,
    _extract_header_line,
    _html_to_plain,
)


def test_hackernews_comment_helpers_extract_structured_fields():
    html = """
    <p>Acme | Senior Backend Engineer | Remote</p>
    <p>Build APIs and data pipelines.</p>
    <p><a href="https://jobs.acme.com/backend">Apply here</a></p>
    """

    plain_text = _html_to_plain(html)

    assert _extract_header_line(plain_text) == (
        "Acme | Senior Backend Engineer | Remote"
    )
    assert _extract_company_from_comment(plain_text) == "Acme"
    assert _extract_first_external_url(plain_text) == ("https://jobs.acme.com/backend")


def test_hackernews_company_extraction_handles_bullet_prefixes():
    comment = "- Example Corp | Staff Product Designer | Hybrid"

    assert _extract_header_line(comment) == (
        "Example Corp | Staff Product Designer | Hybrid"
    )
    assert _extract_company_from_comment(comment) == "Example Corp"
