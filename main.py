from tqdm import tqdm
import datasets

from seedgather import get_js_functions
from seedgather_filter1 import does_have_return, typecheck_batch
from seedgather_filter2 import pre_filtering
from seedgather_filter3 import chunkify, generate_prompts, get_responses
from seedgather_fewshot import prompt_fmt

def main():
    all_functions = get_js_functions()
    print(f"✅ Total JavaScript functions extracted: {len(all_functions)}")
    
    ds = datasets.Dataset.from_dict({
        "content": list(all_functions),
        "id": list(range(len(all_functions)))
    })
    
    ds = ds.filter(lambda x: does_have_return(x["content"]))
    print(f"✅ Total JavaScript functions with return statements: {len(ds)}")
    
    batch = []
    max_i = len(ds) - 1

    new_ds = {
        "content": [],
        "sha1": [],
        "id": [],
    }

    e_id = 0

    for i, ex in enumerate(tqdm(ds, total=len(ds))):
        try:
            code = ex["content"]

            batch.append(code)

            if len(batch) == 250 or i == max_i:
                filemap = typecheck_batch(batch)
                for sha1, contents in filemap.items():
                    new_ds["content"].append(contents)
                    new_ds["sha1"].append(sha1)
                    new_ds["id"].append(e_id)
                    e_id += 1
                batch = []
                
        except Exception as e:
            print(f"There was an error: {e}")
            continue

    new_ds_hf = datasets.Dataset.from_dict(new_ds)
    print(f"✅ Total high quality JavaScript functions with return statements: {len(new_ds_hf)}")
    
    dataset = new_ds_hf
    dataset = dataset.filter(pre_filtering)
    print(f"✅ Total JavaScript functions after pre-filtering: {len(dataset)}")
    
    # save the dataset to disk
    dataset.save_to_disk("data")
    
if __name__ == "__main__":
    main()