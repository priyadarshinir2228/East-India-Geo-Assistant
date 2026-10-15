"""Request screening and untrusted-text handling (Task 8.4).

Retrieved chunks and GeoServer responses are DATA. They only ever reach the model inside
<passage>/<fact> tags in the user message, after escaping, and the system prompt says text
inside those tags must never be followed as instructions. Requests to change data, reveal
secrets or prompts, or about unrelated topics are refused before any retrieval happens.
"""
import re

WRITE_INTENT = re.compile(r"\b(delete|drop|remove|erase|truncate|update|modify|change|edit|insert|overwrite|wipe)\b.*"
                          r"\b(data|index|indices|record|records|circular|circulars|school|schools|entry|entries|database|layer)\b", re.I)
SECRET_INTENT = re.compile(r"\b(password|passwd|api[ _-]?key|secret|token|credential|system prompt|your (instructions|prompt)|"
                           r"ignore (all|previous|the above))\b", re.I)
IN_SCOPE = re.compile(r"\b(school|schools|admission|admissions|circular|board|wbbse|wbchse|cbse|cisce|icse|seat|seats|cut-?off|"
                      r"class|age|exam|marks|lottery|ews|reservation|sibling|transfer certificate|document|documents|road|street|"
                      r"locality|near|where|located|kolkata|darjeeling|dum dum|behala|garia|shibpur|ballygunge|baranagar|rajarhat|"
                      r"chowrasta|north point|east india|session|stream|merit|deadline|form|forms|test|vidyalaya|vidyapith|academy|"
                      r"convent|collegiate|deo/)", re.I)
INJECTION_HINT = re.compile(r"ignore (all )?(previous|prior|above) instructions|system notice|print the .*password|"
                            r"reveal .*prompt", re.I)

REFUSALS = {
    "write": "I can only read the admission sources; I cannot change or delete any data.",
    "secret": "I cannot share passwords, keys, system prompts or other internal configuration.",
    "scope": "I can only answer questions about East India schools, admissions and the town geography in the corpus.",
}
ABSTAIN = "I cannot answer this from the available sources."


def screen(question):
    """Return a refusal reason key, or None if the question may proceed."""
    if WRITE_INTENT.search(question):
        return "write"
    if SECRET_INTENT.search(question):
        return "secret"
    if not IN_SCOPE.search(question):
        return "scope"
    return None


def escape(text):
    """Neutralise tag-like text so a passage cannot close its own <passage> wrapper."""
    return text.replace("<", "&lt;").replace(">", "&gt;")


def suspicious(text):
    return bool(INJECTION_HINT.search(text))
