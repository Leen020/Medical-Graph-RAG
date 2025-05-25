import os
import tiktoken

def count_tokens(text, model='gpt-3.5-turbo'):
    # Create an encoding instance for the model.
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

# Directory where your text files are stored
directory = 'dataset/mimic_ex'

max_tokens = 0
max_file = None
max_text = ''

# Loop over all files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.txt'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            text = file.read()
            print(filename)
            tokens = count_tokens(text)
            if tokens > max_tokens:
                max_tokens = tokens
                max_file = filename
                max_text = text

print("File with the highest token count:", max_file)
print("Token count:", max_tokens)
