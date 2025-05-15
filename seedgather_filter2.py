import re

BAD_IMPORTS = ["require(", "import ", "from "]
BAD_WORDS = ["todo", "fixme", "bug"]
BAD_SUBSTRINGS = BAD_WORDS + BAD_IMPORTS

def js_extract_docstring(code):
    """
    Extracts JSDoc (/** ... */) or leading // comments before the function.
    Returns (docstring, code).
    """
    docstring = ""
    # JSDoc style
    match = re.search(r"/\*\*([\s\S]*?)\*/", code)
    if match:
        docstring = match.group(0)
    else:
        # Single line comments before function
        lines = code.splitlines()
        doc_lines = []
        for line in lines:
            if line.strip().startswith("//"):
                doc_lines.append(line.strip())
            elif line.strip().startswith("function") or "=>" in line:
                break
        docstring = "\n".join(doc_lines)
    return docstring.strip(), code

def pre_filtering(ex):
    code = ex["content"]

    if "function()" in code or "() =>" in code:
        return False

    lower = code.lower()
    for word in BAD_SUBSTRINGS:
        if word in lower:
            return False

    lines = code.split("\n")
    if len(lines) > 150:
        return False

    return True