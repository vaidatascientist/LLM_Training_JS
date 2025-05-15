import subprocess
import tempfile
import hashlib
import os
import argparse
from typing import Dict
from tree_sitter import Language, Parser

if not os.path.exists('my-languages.so'):
    Language.build_library('my-languages.so', ['tree-sitter-javascript'])

LANGUAGE = Language('my-languages.so', 'javascript')

RETURN_QUERY = LANGUAGE.query("""
(return_statement) @return
""")

def make_parser():
    parser = Parser()
    parser.set_language(LANGUAGE)
    return parser

def does_have_return(src):
    parser = make_parser()
    tree = parser.parse(bytes(src, "utf8"))
    root = tree.root_node
    captures = RETURN_QUERY.captures(root)
    for node, _ in captures:
        if len(node.children) <= 1:  
            continue
        else:
            return True
    return False

# runs eslint in the given directory, returns a map of file -> error count
def run_eslint(d):
    try:
        outs = subprocess.run(
            ["eslint", ".", "--no-eslintrc", "--env", "es6", "--parser-options=ecmaVersion:2018", "--format", "compact"],
            cwd=d,
            capture_output=True,
            timeout=120,
            text=True,
        ).stdout
    except Exception as e:
        print(e)
        return None

    filemap = {}
    lines = outs.split("\n")
    for line in lines:
        if ":" in line and "error" in line:
            parts = line.split(":")
            if len(parts) >= 2:
                file = parts[0].split("/")[-1]
                if file not in filemap:
                    filemap[file] = 0
                filemap[file] += 1
    return filemap

def typecheck_batch(files):
    # Create a temporary directory using the tempfile module
    filemap: Dict[str, str] = {}
    with tempfile.TemporaryDirectory() as tempdir:
        for contents in files:
            hash_object = hashlib.sha1(bytes(contents, "utf8"))
            hex_dig = hash_object.hexdigest()
            filemap[hex_dig] = contents
            name = os.path.join(tempdir, hex_dig + ".js")
            with open(name, "w") as f:
                f.write(contents)

        # Run eslint in the temporary directory
        typecheck_map = run_eslint(tempdir)
        print(typecheck_map)

        if typecheck_map is None:
            return {}

        for contents, errors in typecheck_map.items():
            no_js = contents.replace(".js", "")
            if errors == 0:
                continue
            if no_js in filemap:
                del filemap[no_js]

        return filemap

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some JavaScript files.")
    parser.add_argument("files", nargs="+", help="List of JavaScript files to process")
    args = parser.parse_args()

    for file in args.files:
        with open(file, "r") as f:
            code = f.read()
            print(f"Processing {file}...")
            if does_have_return(code):
                print("Has return statement")
            else:
                print("No return statement")
