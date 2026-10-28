PICK_PROMPT = "Which numbered product is the customer asking about?\n{refs}"
ANSWER_PROMPT = """Answer the customer's question using ONLY this product data — never
add anything not present here. If the data doesn't cover it, say you're not sure and
suggest they check the product page.

{product_json}"""