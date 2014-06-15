
import re as re

# Wrap strings that look like a URL starting with 'www.' in a href prefixed with 'http://'.
# TODO/FIXME: This will also turn http://www. into an href but with two http:// prefixes.
# TODO/FIXME: Doing a replace of the match will catch addresses with the same base but different sub-pages.
def find_and_convert_url_to_href(html_text):
    if not html_text: return None

    www_finder = re.compile(r'www\.[a-zA-Z0-9\./_-]*') # TODO unhandled chars: ~:?#\[\]@!$&()\*+,;=
    www_matches = www_finder.findall(html_text)
    for match in www_matches:
        href_url = '<a href="http://' + match + '" target="_blank">' + match + '</a>'
        html_text = html_text.replace(match, href_url)

    return html_text

