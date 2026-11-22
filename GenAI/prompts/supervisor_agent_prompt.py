ROUTER_PROMPT = """Classify the customer's latest message into exactly ONE intent.

search   - wants to find, browse or compare products, or asks what's available / the price of a KIND of product
details  - Ask a question about a product already discovered or selected.
            Examples: Is this eggless? What are its dimensions?
            Does this product have a warranty?
cart     - add / remove / change quantity of items already shown (e.g. "add 2", "I'll take the first one",
           "remove 3", "make it two"), or asks to see the cart
checkout - wants to buy / check out / pay, or is giving recipient, address, city, delivery date,
           their own name for the card, or a gift message
track    - asks about the status of an order that was already placed
chat     - greeting, thanks, or a general question that is none of the above

"search" vs "details": if they're asking for a NEW kind of product, it's search, even if they
also mention a number in passing. If they're asking a QUESTION about a specific item already on
screen, it's details.

Use the selected product context and conversation history
to understand references such as "this product" and "it".

Return ONLY one label:
"search", "details", "cart", "checkout", "track", "chat"

Do not provide explanations or additional text.

"


"""



