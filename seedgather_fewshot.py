# import random
# from seedgather_filter2 import js_extract_docstring

# def template_few_shot(code, answer, rationale):
#     doc, code = js_extract_docstring(code)
#     prompt = f"""
# <issue_start>username_0: I have a function in JavaScript and I'd like someone to check my description of this function.
# I'm doing this so that I can write a good comment for this function.

# Here is the code for the function:
# ```js
# {code}
# ```

# Here is my description of this program:
# ```
# {doc}
# ```

# Do not attempt to execute the function or to judge its correctness.
# Answer with "Yes" or "No" depending on if my description has enough information alone to re-implement the function.
# Also, answer with "No" if the description does not match the function.<issue_comment>username_1: Sure, no problem. I will be able to help.
# My answer is: {answer}

# {rationale}

# Upvotes: 200"""
#     return prompt

# FEW_SHOTS = [
#     (
#         '''/**
#  * Adds two numbers together.
#  * @param {number} a
#  * @param {number} b
#  * @returns {number}
#  */
# function add(a, b) {
#     return a + b;
# }''',
#         "Yes",
#         "The JSDoc comment accurately describes the function's purpose and parameters."
#     ),
#     (
#         '''// Returns the square of a number
# function square(x) {
#     return x * x;
# }''',
#         "Yes",
#         "The single-line comment matches the function's behavior."
#     ),
#     (
#         '''function mystery(a, b) {
#     // TODO: implement this function
#     return;
# }''',
#         "No",
#         "The comment is a TODO and does not describe the function."
#     ),
# ]

# def prompt_fmt(code):
#     doc, code = js_extract_docstring(code)
#     random.shuffle(FEW_SHOTS)
#     buf = ""
#     for few in FEW_SHOTS:
#         buf += template_few_shot(*few)
#     buf += f"""<issue_start>username_0: I have a function in JavaScript and I'd like someone to check my description of this function.
# I'm doing this so that I can write a good comment for this function.

# Here is the code for the function:
# ```js
# {code}
# ```

# Here is my description of this program:
# ```
# {doc}
# ```

# Do not attempt to execute the function or to judge its correctness.
# Answer with "Yes" or "No" depending on if my description has enough information alone to re-implement the function.
# Also, answer with "No" if the description does not match the function.
# Upvotes: 100<issue_comment>username_1: Sure, no problem. I will be able to help.
# My answer is:"""
#     return buf

import random
from seedgather_filter2 import js_extract_docstring

def template_few_shot(code, answer, rationale):
    doc, code = js_extract_docstring(code)
    prompt = f"""
Here is the code for the function:
```js
{code}
```

Here is my description of this program:
```
{doc}
```

Does the description have enough information alone to re-implement the function? Answer "Yes" or "No". If the description does not match the function, answer "No".

My answer is: {answer}

{rationale}
"""
    return prompt

FEW_SHOTS = [
    (
        '''/**
 * Adds two numbers together.
 * @param {number} a
 * @param {number} b
 * @returns {number}
 */
function add(a, b) {
    return a + b;
}''',
        "Yes",
        "The JSDoc comment accurately describes the function's purpose and parameters."
    ),
    (
        '''// Returns the square of a number
function square(x) {
    return x * x;
}''',
        "Yes",
        "The single-line comment matches the function's behavior."
    ),
    (
        '''function mystery(a, b) {
    // TODO: implement this function
    return;
}''',
        "No",
        "The comment is a TODO and does not describe the function."
    ),
]

def prompt_fmt(code):
    doc, code = js_extract_docstring(code)
    random.shuffle(FEW_SHOTS)
    buf = ""
    for few in FEW_SHOTS:
        buf += template_few_shot(*few)
    buf += f"""
Here is the code for the function:
```js
{code}
```

Here is my description of this program:
```
{doc}
```

Does the description have enough information alone to re-implement the function? Answer "Yes" or "No". If the description does not match the function, answer "No".

My answer is:"""
    return buf