set -e

export PYTHONPATH=$(pwd)/code:$PYTHONPATH
mkdir -p model_outputs/instruction
mkdir -p model_outputs/instruction_session
mkdir -p model_outputs/instruction_session_history

model_name=command-r-plus
# Evaluation is split into 3 steps. The final output is stored in model_outputs/instruction_session_history.

# Instructions
python -m fire code/generate_model_output.py generate_model_output_instruction --model_name "$model_name" \
    --topics_file topics.json \
    --output_dir model_outputs/instruction

# Sessions
for dialogue_id in {1..360}; do
    python -m fire code/generate_model_output.py generate_model_output_session \
        --dialogue_file "dataset/dialogue_${dialogue_id}.json" \
        --model_name "$model_name" \
        --instruction_output_path "model_outputs/instruction/${model_name}.json" \
        --output_dir model_outputs/instruction_session
done

# History
for dialogue_id in {1..360}; do
    python -m fire code/generate_model_output.py generate_model_output_history \
        --dialogue_file "dataset/dialogue_${dialogue_id}.json" \
        --model_name "$model_name" \
        --instruction_session_path "model_outputs/instruction_session/${model_name}/output_${dialogue_id}.json" \
        --output_dir model_outputs/instruction_session_history
done
