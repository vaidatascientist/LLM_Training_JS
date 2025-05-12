MAX_NEW_DATA=1000000
python ./selfcodealign/src/star_align/self_ossinstruct.py \
 --seed_data_files "./data/c_to_i.jsonl" \
 --use_vllm_server True \
 --instruct_mode "I->R" \
 --max_new_data $MAX_NEW_DATA \
 --tag concept_gen \
 --temperature 0.7 \
 --seed_code_start_index 0 \
 --model "/project/phan/codellama/StarCoder" \
 --num_fewshots 8 \
 --num_batched_requests 200 \
 --num_sample_per_request 1 \
 --async_micro_batch_size 10 \
 --delay 0