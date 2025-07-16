import os
import json
import re
import argparse
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from camel.storages import Neo4jGraph
from summerize import process_chunks
from retrieve import seq_ret
from utils import get_response, str_uuid

# Function to extract answer letter from model response
def extract_answer_letter(response):
    """Extract the answer letter (A, B, C, D, or E) from the model's response."""
    # Look for patterns like "The answer is A" or "Answer: B" or just "A."
    patterns = [
       r"(?:Cevap|Doğru seçenek|Seçenek|doğrudur|Answer|Correct option|Option|is correct)?[\s:]([A-Ea-e])[.\s]"
]
    
    for pattern in patterns:
        matches = re.findall(pattern, response, re.IGNORECASE)
        if matches:
            return matches[0].upper()
    
    # If no clear pattern, check if any option letter appears more frequently
    letter_counts = {}
    for letter in "ABCDE":
        # Count occurrences of the letter surrounded by spaces or punctuation
        pattern = r'(?:^|\s|[.,;:])' + letter + r'(?:\s|[.,;:]|$)'
        letter_counts[letter] = len(re.findall(pattern, response, re.IGNORECASE))
    
    # If one letter is mentioned significantly more, return it
    max_letter = max(letter_counts, key=letter_counts.get)
    if letter_counts[max_letter] > 1 and letter_counts[max_letter] > sum(count for letter, count in letter_counts.items() if letter != max_letter):
        return max_letter
    
    # Default to returning the first letter that appears in the response
    for letter in "ABCDE":
        if letter in response.upper():
            return letter
    
    return None  # No answer letter found

# Function to load MCQ questions from JSON file
def load_mcq_questions(json_file="./prompt.json"):
    """Load MCQ questions from a JSON file."""
    with open(json_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    return questions

# Function to save inference results to JSON file
def save_inference_results(results, filename="inference_results.json"):
    """Save inference results to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Inference results saved to {filename}")

# Function to load inference results from JSON file
def load_inference_results(filename="inference_results.json"):
    """Load inference results from a JSON file."""
    with open(filename, 'r', encoding='utf-8') as f:
        results = json.load(f)
    return results

# Function to evaluate MCQ performance
def evaluate_mcq_performance(results):
    """Evaluate model performance on MCQs using various metrics."""
    true_answers = []
    predicted_answers = []
    
    for result in results:
        if "answer_letter" in result and "predicted_letter" in result:
            true_answers.append(result["answer_letter"])
            predicted_answers.append(result["predicted_letter"])
    
    if not true_answers or not predicted_answers:
        print("No valid answer pairs found for evaluation.")
        return {}
    
    # Convert letters to numeric labels for multi-class metrics
    letter_to_num = {letter: i for i, letter in enumerate("ABCDE")}
    true_nums = [letter_to_num[letter] for letter in true_answers]
    pred_nums = [letter_to_num.get(letter, 0) for letter in predicted_answers]  # Default to 0 if letter not found
    
    # Calculate metrics
    accuracy = accuracy_score(true_answers, predicted_answers)
    
    # For multi-class classification, we need to specify averaging method
    precision = precision_score(true_nums, pred_nums, average='macro', zero_division=0)
    recall = recall_score(true_nums, pred_nums, average='macro', zero_division=0)
    f1 = f1_score(true_nums, pred_nums, average='macro', zero_division=0)
    
    # Calculate per-class metrics
    class_metrics = {}
    unique_letters = sorted(set(true_answers))
    
    for letter in unique_letters:
        letter_idx = letter_to_num[letter]
        true_binary = [1 if ans == letter else 0 for ans in true_answers]
        pred_binary = [1 if pred == letter else 0 for pred in predicted_answers]
        
        class_metrics[letter] = {
            "precision": precision_score(true_binary, pred_binary, zero_division=0),
            "recall": recall_score(true_binary, pred_binary, zero_division=0),
            "f1": f1_score(true_binary, pred_binary, zero_division=0)
        }
    
    metrics = {
        "accuracy": accuracy,
        "macro_precision": precision,
        "macro_recall": recall,
        "macro_f1": f1,
        "per_class": class_metrics,
        "total_questions": len(true_answers),
        "correct_answers": sum(1 for t, p in zip(true_answers, predicted_answers) if t == p)
    }
    
    # Print evaluation results
    print("\nEvaluation Results:")
    print(f"Total Questions: {metrics['total_questions']}")
    print(f"Correct Answers: {metrics['correct_answers']}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Macro Precision: {metrics['macro_precision']:.4f}")
    print(f"Macro Recall: {metrics['macro_recall']:.4f}")
    print(f"Macro F1 Score: {metrics['macro_f1']:.4f}")
    
    print("\nPer-Class Metrics:")
    for letter, letter_metrics in metrics["per_class"].items():
        print(f"Class {letter}:")
        print(f"  Precision: {letter_metrics['precision']:.4f}")
        print(f"  Recall: {letter_metrics['recall']:.4f}")
        print(f"  F1 Score: {letter_metrics['f1']:.4f}")
    
    # Generate and print classification report
    target_names = [f"Option {letter}" for letter in sorted(set(true_answers))]
    print("\nClassification Report:")
    print(classification_report(true_nums, pred_nums, target_names=target_names, zero_division=0))
    
    return metrics

# Function to run inference on MCQ questions
def run_inference(n4j, questions, results_file="inference_results.json"):
    """Run inference on MCQ questions and save results."""
    inference_results = []

    for idx, question_data in enumerate(questions):
        question_text = question_data["question"]
        question_id = question_data["question_id"]
        correct_answer = question_data["answer_letter"]
        
        question_text += """\nSoruyu yanıtla. Cevabını yalnızca şu formatta ver:\nCevap: B\nAçıklama yapma. Yukarıdaki format dışında başka bir biçim kullanma."""
        
        print(f"\nProcessing Question {idx+1} (ID: {question_id}): {question_text}\n")

        # Generate summary for this single question
        summaries = process_chunks(question_text)  # returns a list (may contain 1 item)

        for summary in summaries:
            # Retrieve relevant subgraph
            gid = seq_ret(n4j, summary)

            # Query graph and get response
            response = get_response(n4j, gid, question_text)
            
            # Extract answer letter from response
            predicted_letter = extract_answer_letter(response)
            
            # Store results
            result = {
                "question_id": question_id,
                "question": question_text,
                "full_answer": response,
                "predicted_letter": predicted_letter,
                "answer_letter": correct_answer
            }
            inference_results.append(result)
            
            print(f"Question: {question_text}")
            print(f"Model Answer: {response}")
            print(f"Extracted Answer Letter: {predicted_letter}")
            print(f"Correct Answer Letter: {correct_answer}")
            print(f"Correct: {predicted_letter == correct_answer}\n")

    # Save inference results to JSON file
    save_inference_results(inference_results, results_file)
    return inference_results

# Main function
def main():
    parser = argparse.ArgumentParser(description="MCQ Evaluation Tool")
    parser.add_argument('-inference', action='store_true', help='Run inference on MCQ questions')
    parser.add_argument('-evaluate', action='store_true', help='Evaluate model performance on MCQs')
    parser.add_argument('-results_file', type=str, default='inference_results.json', help='File to save/load inference results')
    parser.add_argument('-questions_file', type=str, default='./prompt.json', help='JSON file containing MCQ questions')
    args = parser.parse_args()
    
    # Connect to Neo4j if needed for inference
    n4j = None
    if args.inference:
        url = os.getenv("NEO4J_URL")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        # Set Neo4j instance
        n4j = Neo4jGraph(
            url=url,
            username=username,             
            password=password     
        )
    
    # Run inference if requested
    if args.inference:
        # Load questions from JSON file
        mcq_questions = load_mcq_questions(args.questions_file)
        
        # Run inference
        inference_results = run_inference(n4j, mcq_questions, args.results_file)
        
        # If evaluate flag is also set, perform evaluation immediately
        if args.evaluate:
            evaluate_mcq_performance(inference_results)
    
    # Run evaluation if requested (and not already done)
    elif args.evaluate:
        # Load previously saved inference results and evaluate
        try:
            inference_results = load_inference_results(args.results_file)
            evaluate_mcq_performance(inference_results)
        except FileNotFoundError:
            print(f"Error: Results file '{args.results_file}' not found. Run inference first or specify correct file path.")

if __name__ == "__main__":
    main()