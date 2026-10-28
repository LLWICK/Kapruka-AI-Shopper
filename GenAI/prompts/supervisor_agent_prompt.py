ROUTER_PROMPT = """
Classify the shopping request into exactly one category.

search: Find, search for, or browse products.
compare: Compare two or more specific products.
gift: Recommend gifts based on recipient, occasion, or preferences.
other: Anything else.

Return only one label: search, compare, gift, or other.
"""