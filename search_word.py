import os

def search_word_in_files(directory, word):
    """
    Search for a specific word in all .txt files in a directory.
    :param directory: Path to the directory containing the .txt files
    :param word: Word to search for
    """
    count = 0
    if not os.path.exists(directory):
        print(f"The directory '{directory}' does not exist.")
        return

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if word in content:
                            print(f"Word '{word}' found in file: {file_path}")
                            count+=1
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}")
    
    print(f"\nThe word '{word}' was found in {count} file(s).")

# Replace 'your_directory_path' with the directory containing your .txt files
# Replace 'your_word' with the word you want to search for
search_word_in_files('dataset', 'abuse transferred from for pancytopenia')