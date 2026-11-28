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

CART ACTION CLASSIFICATION:

If intent is cart, identify the requested operation:

- add: Add a product to the cart.
- remove: Remove a product from the cart.
- update: Change the quantity of an existing cart item.
- view: Display the current cart.

Examples:
"Add two cakes" -> cart_action = add
"Remove the chocolate cake" -> cart_action = remove
"Change its quantity to 3" -> cart_action = update
"Show my cart" -> cart_action = view

If intent is not cart, cart_action must be null.

Use the selected product context and conversation history
to understand references such as "this product" and "it".

Return ONLY one label for intent:
"search", "details", "cart", "checkout", "track", "chat"

and Return ONLY one label for cart_action:
"add", "remove", "update", "view", null

Do not provide explanations or additional text rather than "intent" and "cart_action".

"


"""



