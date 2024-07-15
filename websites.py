import re
from urllib.parse import urlparse, parse_qs

# TODO: welcome open-source community to expand this list
letter_case_formatter = [
    "ORCID", "GitHub", "LinkedIn", "TikTok", "YouTube", "ResearchGate", "SoundCloud",
]


def format_domain(domain):
    """Capitalize the domain name properly."""
    domain_parts = domain.split('.')
    # Handle cases like 'www' and known domains
    if domain_parts[0] == 'www':
        domain_parts.pop(0)
    domain_ = domain_parts[0].capitalize()
    for domain_1 in letter_case_formatter:
        domain_1_capitalize = domain_1.capitalize()
        if domain_ == domain_1_capitalize:
            domain_ = domain_1
    return domain_


def score_candidate(part, index, is_query=False):
    """Score a potential username candidate based on its characteristics."""
    # Basic score based on the length of the part
    score = len(part)
    # Add to score based on its position (earlier is better)
    position_score = 10 / (index + 1)
    # If it's from query parameters, it might be less likely to be a username
    if is_query:
        score += position_score / 2  # Lower the position effect if in query
    else:
        score += position_score
    return score


def extract_username(path, query):
    """
    Extract the best potential username from the path and query string using scoring.
    """
    candidates = []
    # First, attempt to find a username in the path
    path_parts = path.strip('/').split('/')
    for index, part in enumerate(path_parts):
        if re.match(r'^[\w-]+$', part):
            candidates.append((part, score_candidate(part, index)))
    # Check the query parameters
    for key, values in query.items():
        for index, val in enumerate(values):
            if re.match(r'^[\w-]+$', val):
                # Consider keys like 'user', 'username', 'userid' as more likely
                # candidates
                bonus = 10 if re.search(r'user(name|id)?', key, re.I) else 0
                candidates.append(
                    (val, score_candidate(val, index, is_query=True) + bonus))
    # Sort candidates by score, highest first
    if candidates:
        candidates.sort(key=lambda x: -x[1])
        return candidates[0][0]
    else:
        return ""


def convert_url(url):
    """Convert URL to a formatted string based on heuristic rules."""
    # Parse the URL to extract domain and path
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    formatted_domain = format_domain(domain)
    path = parsed_url.path
    query = parse_qs(parsed_url.query)
    username = extract_username(path, query)
    if username:
        return f"{formatted_domain}: {username}"
    else:
        return domain + path
