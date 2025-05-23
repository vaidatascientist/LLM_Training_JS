import datasets
import os
from multiprocessing import Pool
import boto3
from smart_open import open
from botocore import UNSIGNED
from botocore.config import Config
from itertools import islice
import jsbeautifier

from tree_sitter import Language, Parser

if not os.path.exists('my-languages.so'):
    Language.build_library('my-languages.so', ['tree-sitter-javascript'])

LANGUAGE = Language('my-languages.so', 'javascript')

s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))

def download_contents(blob_id, src_encoding):
    s3_url = f"s3://softwareheritage/content/{blob_id}"
    with open(s3_url, "rb", compression=".gz", transport_params={"client": s3}) as fin:
        content = fin.read().decode(src_encoding)
    return {"content": content}

def beautify_js_function(js_code):
    opts = jsbeautifier.default_options()
    opts.indent_size = 4
    return jsbeautifier.beautify(js_code, opts)

TOPLEVEL_QUERY = LANGUAGE.query("""
;; Function declarations
(
  (function_declaration
    name: (identifier) @function.name
    parameters: (formal_parameters) @function.params
    body: (statement_block) @function.body
  ) @function.def
)

;; Named arrow functions and function expressions via const/let
(
  (lexical_declaration
    (variable_declarator
      name: (identifier) @function.name
      value: [
        (function_expression
          parameters: (formal_parameters) @function.params
          body: (statement_block) @function.body
        )
        (arrow_function
          parameters: (formal_parameters) @function.params
          body: (_) @function.body
        )
      ]
    )
  ) @function.def
)

;; Assignment-based named function expressions
(
  (expression_statement
    (assignment_expression
      left: (identifier) @function.name
      right: [
        (function_expression
          parameters: (formal_parameters) @function.params
          body: (statement_block) @function.body
        )
        (arrow_function
          parameters: (formal_parameters) @function.params
          body: (_) @function.body
        )
      ]
    )
  ) @function.def
)

;; Anonymous inline function expressions in call arguments
(
  (call_expression
    arguments: (arguments
      [
        (function_expression
          parameters: (formal_parameters) @function.params
          body: (statement_block) @function.body
        )
        (arrow_function
          parameters: (formal_parameters) @function.params
          body: (_) @function.body
        )
      ] @function.body
    )
  ) @function.anonymous
)

;; Standalone anonymous functions not assigned or named
[
  (function_expression
    parameters: (formal_parameters) @function.params
    body: (statement_block) @function.body
  )
  (arrow_function
    parameters: (formal_parameters) @function.params
    body: (_) @function.body
  )
] @function.anonymous
""")

def node_to_string(buf, node):
    return buf[node.start_byte:node.end_byte].decode("utf8", errors="ignore")

def get_top_level_functions(src, tree):
    captures = TOPLEVEL_QUERY.captures(tree.root_node)
    res = []
    for node, ty in captures:
        if ty not in ["function.def", "function.anon"]:
            continue
        raw_fn = node_to_string(src, node)
        pretty_fn = beautify_js_function(raw_fn)  # <-- Beautify here
        res.append(pretty_fn)

    return res

def parse_ex(parser, ex):
    try:
        blob_id = ex.get("blob_id")
        src_encoding = ex.get("src_encoding")
        if not blob_id or not src_encoding:
            return []

        result = download_contents(blob_id, src_encoding)
        if not result or "content" not in result:
            return []

        code_str = result["content"]
        buf = bytes(code_str, "utf8")
        tree = parser.parse(buf)

        return get_top_level_functions(buf, tree) or []

    except Exception:
        return []

def process_chunk(chunk):
    parser = make_parser()  
    chunk_new_funs = set()
    for ex in chunk:
        try:
            fns = parse_ex(parser, ex)
            chunk_new_funs.update(fns)
        except Exception as e:
            print(f"❌ Error in process_chunk: {e}")
    return chunk_new_funs

def make_parser():
    parser = Parser()
    parser.set_language(LANGUAGE)
    return parser

def get_js_functions():
    ds = datasets.load_dataset(
        "bigcode/the-stack-v2-dedup",
        data_dir="data/JavaScript",
        split="train",
        streaming=True,
        cache_dir="./stack_cache"
    )
    
    first_1000 = list(islice(ds, 1000))

    funs = set()
    NUM_WORKERS = os.cpu_count()
    CHUNK_SIZE = 1000 * NUM_WORKERS

    chunk = []
    p = Pool(NUM_WORKERS)

    for i, ex in enumerate(first_1000):
        chunk.append(ex)

        if len(chunk) == CHUNK_SIZE or i == len(first_1000) - 1:
            subchunk_size = len(chunk) // NUM_WORKERS
            subchunks = [chunk[j:j + subchunk_size] for j in range(0, len(chunk), subchunk_size)]
            new_funs_iter = p.imap(process_chunk, subchunks)

            collected_funs = set()
            try:
                for result in new_funs_iter:
                    if result:
                        collected_funs.update(result)
            except Exception:
                pass

            funs.update(collected_funs)
            PARSERS = [make_parser() for _ in range(NUM_WORKERS)]
            chunk = []

    p.close()
    p.join()

    return funs

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    all_functions = get_js_functions()