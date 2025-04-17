import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM
from seedgather_fewshot import prompt_fmt

# def unindent(s):
#     lines = s.splitlines()
#     non_blank_lines = [line for line in lines if line.strip()]
#     min_indent = min(len(line) - len(line.lstrip())
#                      for line in non_blank_lines) if non_blank_lines else 0
#     unindented_lines = [line[min_indent:] if len(
#         line) >= min_indent else line for line in lines]
#     return '\n'.join(unindented_lines)

def chunkify(lst, n):
    chunks = []
    for i in range(0, len(lst), n):
        chunk = []
        for j in range(n):
            if i + j < len(lst):
                chunk.append(lst[i + j])
        chunks.append(chunk)
    return chunks

def generate_prompts(dataset, tokenizer, few_shot_toks, dummy_prompt, prompt_fmt, max_tokens=16380):
    prompts = []
    for ex in tqdm(dataset, total=len(dataset), desc="Generating prompts"):
        code = ex["content"]
        toks = len(tokenizer.encode(code)) + few_shot_toks
        if toks > max_tokens:
            print(f"Skipping example with {toks} tokens")
            prompts.append(dummy_prompt)
            continue
        p = prompt_fmt(code)
        prompts.append(p)
    return prompts

def get_responses(prompts, tokenizer, model, chunkify, chunk_size=512):
    responses = []
    device = model.device if hasattr(model, "device") else torch.device("cuda" if torch.cuda.is_available() else "cpu")
    for chunk in tqdm(chunkify(prompts, chunk_size), desc="Generating responses"):
        # Tokenize and generate for each prompt in the chunk
        for prompt in chunk:
            inputs = tokenizer(prompt, return_tensors="pt").to(device)
            outputs = model.generate(
                **inputs,
                max_new_tokens=5,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.eos_token_id,
            )
            output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            c = output_text.lower()
            yes_count = c.count("yes")
            no_count = c.count("no")
            if yes_count > no_count:
                responses.append(True)
            elif yes_count < no_count:
                responses.append(False)
            else:
                responses.append(False)
    return responses
