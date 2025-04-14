import tree_sitter_javascript as tsjs
from tree_sitter import Language, Parser

LANGUAGE = Language(tsjs.language())

import datasets
import os
import signal
from multiprocessing import Pool
import boto3
import smart_open
from botocore import UNSIGNED
from botocore.config import Config

# JavaScript-specific Tree-sitter query for top-level functions with docstrings
TOPLEVEL_DOCSTRING_QUERY = LANGUAGE.query("""
(
  (function_declaration
    name: (identifier)
    body: (statement_block . 
      (comment) @docstring)) @function.def
)
""")

def node_to_string(buf, node):
    return buf[node.start_byte:node.end_byte].decode("utf8", errors="ignore")

def get_fns_with_docstrings(src, tree):
    captures = TOPLEVEL_DOCSTRING_QUERY.captures(tree.root_node)
    res = []
    for node, ty in captures:
        if ty != "function.def":
            continue
        _, col = node.start_point
        if col != 0:
            continue
        res.append(node_to_string(src, node))
    return res


def parse_ex(parser, ex):
    try:
        ex = download_contents(ex["blob_id"], ex["src_encoding"])
        buf = bytes(ex, "utf8")
        tree = parser.parse(buf)
        return get_fns_with_docstrings(buf, tree)
    except Exception as e:
        print(f"Error parsing blob {ex.get('blob_id')}: {e}")
        return []

PARSERS = None

def process_chunk(idx_and_chunk):
    global PARSERS
    idx, chunk = idx_and_chunk
    parser = PARSERS[idx]
    chunk_new_funs = set()
    for ex in chunk:
        chunk_new_funs.update(parse_ex(parser, ex))
    return chunk_new_funs

def make_parser():
    parser = Parser(LANGUAGE)
    return parser

def main_js():
    global PARSERS
    ds = datasets.load_dataset(
        "bigcode/the-stack-v2-dedup",
        "JavaScript",
        streaming=True,
        split="train",
        cache_dir="./stack_cache"
    )

    funs = set()
    NUM_WORKERS = os.cpu_count()
    PARSERS = [make_parser() for _ in range(NUM_WORKERS)]
    CHUNK_SIZE = 1000 * NUM_WORKERS

    chunk = []
    p = Pool(NUM_WORKERS)

    i = 0
    for ex in ds:
        try:
            chunk.append(ex)
            if len(chunk) == CHUNK_SIZE:
                print(f"Processing chunk {i // CHUNK_SIZE}")
                subchunk_size = len(chunk) // NUM_WORKERS
                subchunks = [chunk[j:j + subchunk_size] for j in range(0, len(chunk), subchunk_size)]
                new_funs_iter = p.imap(process_chunk, [(j, subchunk) for j, subchunk in enumerate(subchunks)])

                print("Getting new functions")
                len_before = len(funs)

                while True:
                    try:
                        def timeout_handler(_, __):
                            raise KeyboardInterrupt
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(60)
                        funs.update(next(new_funs_iter))
                        signal.alarm(0)
                    except KeyboardInterrupt:
                        signal.alarm(0)
                        print("Timeout or keyboard interrupt. Restarting pool.")
                        p.terminate()
                        p.join()
                        p = Pool(NUM_WORKERS)
                        break
                    except StopIteration:
                        break
                    except Exception as e:
                        print(f"Error during pool iteration: {e}")

                PARSERS = [make_parser() for _ in range(NUM_WORKERS)]
                print(f"✅ Done processing chunk {i // CHUNK_SIZE}. Got {len(funs) - len_before} new functions.")
                chunk = []

            i += 1
            if i % 1000 == 0:
                print(f"Progress: {i} examples processed.")

        except Exception as e:
            print(f"Error on example {i}: {e}")
            chunk = []

        # Optional: early stop if needed
        # if i > 10000:
        #     break

    p.close()
    p.join()

    print(f"✅ Total JavaScript functions extracted: {len(funs)}")
    return funs