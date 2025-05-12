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
        """
        /**
         * Do a simple network scan assuming 192.168.1.x subnet
         */
        function simpleScanNetwork() {
            const baseIP = "192.168.1.";
            const addresses = ["127.0.0.1"];

            for (let i = 1; i < 255; i++) {
                addresses.push(baseIP + i);
            }

            return addresses;
        }
        """,
        "No",
        "The comment says it's a 'network scan', but the function only generates IP addresses. It doesn't perform any scanning logic like pinging or probing."
    ),
    (
        """
        /**
         * Convert inches to meters
         */
        function inchesToMeters(inches) {
            return inches * 0.0254;
        }
        """,
        "Yes",
        "The comment correctly describes the function — it converts inches to meters using the correct conversion factor."
    ),
    (
        """
        /**
         * Converts a DataFrame to a dictionary
         */
        function transDfIntoDict(data) {
            data.en_name = data.en_name.map(n => n.toUpperCase());
            const [enFirst, enLast] = data.en_name.map(n => n.split(" "));
            const [jpFirst, jpLast] = data.jp_name.map(n => n.split("・"));
            return {
                full: Object.fromEntries(data.en_name.map((n, i) => [n, data.jp_name[i]])),
                first: Object.fromEntries(enFirst.map((n, i) => [n, jpFirst[i]])),
                last: Object.fromEntries(enLast.map((n, i) => [n, jpLast[i]]))
            };
        }
        """,
        "No",
        "The comment oversimplifies the function. It not only converts to a dictionary but also manipulates Japanese and English names in ways not described."
    ),
    (
        """
        /**
         * Crop image to square using smallest dimension
         */
        function squareCrop(image, targetSize = null) {
            const [w, h] = [image.width, image.height];
            const size = targetSize || Math.min(w, h);
            const dx = (w - size) / 2;
            const dy = (h - size) / 2;
            return image.crop(dx, dy, dx + size, dy + size);
        }
        """,
        "Yes",
        "The comment clearly matches the behavior of the function — cropping an image to a square of the smallest dimension or a specified size."
    ),
    (
        """
        /**
         * Set up motif files for scan workflow
         */
        function setupMotifFiles(args) {
            const cluster = args.cluster;
            const motifs = {};
            motifs.early = `${args.inputs.inference[cluster].scanmotifs_dir}/${args.inputs.inference[cluster].scanmotifs_early_dir}/ggr.scanmotifs.h5`;
            motifs.mid = `${args.inputs.inference[cluster].scanmotifs_dir}/${args.inputs.inference[cluster].scanmotifs_mid_dir}/ggr.scanmotifs.h5`;
            motifs.late = `${args.inputs.inference[cluster].scanmotifs_dir}/${args.inputs.inference[cluster].scanmotifs_late_dir}/ggr.scanmotifs.h5`;
            return motifs;
        }
        """,
        "No",
        "The comment says it sets up motif files but doesn't mention the multiple timepoints (early, mid, late) or how paths are constructed using cluster values."
    ),
    (
        """
        /**
         * Return scalar triple product of u and v with z-axis
         */
        function trip(u, v) {
            return u[0] * v[1] - u[1] * v[0];
        }
        """,
        "Yes",
        "The comment accurately reflects the math performed — the z-component of the cross product, also known as the scalar triple product in 2D."
    ),
    (
        """
        /**
         * Fetches all posts
         */
        async function getPosts(userId) {
            return fetch(`/api/posts/${userId}`).then(res => res.json());
        }
        """,
        "No",
        "The comment does not mention the input parameter `userId`, which is critical to how the function behaves. It's not fetching 'all posts' — it's fetching posts for a specific user."
    ),
    (
        """
        /**
         * Highlight the active tab
         */
        function highlightTab(id) {
            document.querySelectorAll(".tab").forEach(el => el.classList.remove("active"));
            document.getElementById(id).classList.add("active");
        }
        """,
        "Yes",
        "The comment clearly matches the function behavior — it highlights the selected tab while removing highlights from others."
    ),
    (
        """
        /**
         * Calculates the sum of two numbers
         */
        function multiply(a, b) {
            return a * b;
        }
        """,
        "No",
        "The comment says it calculates the sum, but the function multiplies the two inputs. This is a classic case of mismatched description."
    ),
    (
        """
        /**
         * TODO
         */
        function filterUsers(users) {
            return users.filter(u => u.active);
        }
        """,
        "No",
        "The comment provides no useful information — it just says 'TODO', which makes it impossible to reimplement the function from the description."
    )
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