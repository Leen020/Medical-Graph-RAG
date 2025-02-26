import os

def search_words_in_files(directory, words):
    """
    Search for any of the specified words in all .txt files in a directory.
    :param directory: Path to the directory containing the .txt files
    :param words: List of words to search for. A file is considered a match if it contains any one of these words.
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
                        if any(word in content for word in words):
                            print(f"At least one of the words {words} found in file: {file_path}")
                            count += 1
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}")

    print(f"\nAt least one of the words {words} was found in {count} file(s).")

# Replace 'your_directory_path' with the directory containing your .txt files
# Replace 'your_word' with the word you want to search for
search_words_in_files('dataset', ['heart', 'cardiac', 'Echocardiography', 'Valvular', 'Coronary', 'Artery', 'Myocardial', 'Atrial', 'Arrhythmia', 'heart attack'])
