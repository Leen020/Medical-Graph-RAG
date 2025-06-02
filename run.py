import os
from getpass import getpass
from camel.storages import Neo4jGraph
from camel.agents import KnowledgeGraphAgent
from camel.loaders import UnstructuredIO
from dataloader import load_high
# Add this import at the top of the file with other imports
import argparse
from data_chunk import run_chunk
from creat_graph import creat_metagraph
from summerize import process_chunks
from retrieve import seq_ret
from utils import *
from nano_graphrag import GraphRAG, QueryParam
import re
from print_logger import Logger
import sys
import json
# Import the mcq_evaluation module for MCQ evaluation functionality
from mcq_evaluation import *

# %% set up parser
parser = argparse.ArgumentParser()
parser.add_argument('-simple', action='store_true')
parser.add_argument('-construct_graph', action='store_true')
parser.add_argument('-inference', action='store_true')
parser.add_argument('-diagnoses', action='store_true')
parser.add_argument('-evaluate', action='store_true', help='Evaluate model performance on MCQs')
parser.add_argument('-results_file', type=str, default='inference_results.json', help='File to save/load inference results')
parser.add_argument('-grained_chunk', action='store_true')
parser.add_argument('-trinity', action='store_true')
parser.add_argument('-trinity_gid1', type=str)
parser.add_argument('-trinity_gid2', type=str)
parser.add_argument('-ingraphmerge', action='store_true')
parser.add_argument('-crossgraphmerge', action='store_true')
parser.add_argument('-dataset', type=str, default='mimic_ex')
parser.add_argument('-data_path', type=str, default='./dataset_test')
parser.add_argument('-test_data_path', type=str, default='./dataset_ex/report_0.txt')
# Modify the argument parser section to include MCQ evaluation options
parser.add_argument('-mcq_eval', action='store_true', help='Run MCQ evaluation using mcq_evaluation.py')
parser.add_argument('-questions_file', type=str, default='./prompt.json', help='JSON file containing MCQ questions')

args = parser.parse_args()

# Initialize logging at the start of your script
sys.stdout = Logger("processing.log")
sys.stderr = sys.stdout  # Redirect stderr to the same logger

# Keep a reference to original stdout/stderr if needed
original_stdout = sys.__stdout__
original_stderr = sys.__stderr__

def natural_sort_key(s):
    # Split the string into text and number parts and convert numeric parts to integers
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

if args.simple:
    graph_func = GraphRAG(working_dir="./nanotest")

    with open("./dataset_ex/report_0.txt") as f:
        graph_func.insert(f.read())

    # Perform local graphrag search (I think is better and more scalable one)
    print(graph_func.query("What is the main symptom of the patient?", param=QueryParam(mode="local")))

else:

    url=os.getenv("NEO4J_URL")
    username=os.getenv("NEO4J_USERNAME")
    password=os.getenv("NEO4J_PASSWORD")

    # Set Neo4j instance
    n4j = Neo4jGraph(
        url=url,
        username=username,             
        password=password     
    )

    if args.construct_graph: 
        if args.dataset == 'mimic_ex' or 'books':
            files =sorted(
                [file for file in os.listdir(args.data_path) if os.path.isfile(os.path.join(args.data_path, file))],
                key=natural_sort_key
            )
            
            # Read and print the contents of each file
            for file_name in files:
                print(file_name)
                file_path = os.path.join(args.data_path, file_name)
                try:
                    content = load_high(file_path)
                    gid = str_uuid()
                    filename = os.path.splitext(file_name)[0]
                    n4j = creat_metagraph(args, content, gid, n4j, filename)
                
                except ValueError as e:
                    if "Azure has not provided the response due to a content filter" in str(e):
                        print(f"\nSkipped '{file_name}' due to content filter. File removed.\n")
                        os.remove(file_path)  # Delete the problematic document
                        continue  # Skip to next document
                except Exception as e:
                    print(f"Unexpected error processing {file_name}: {str(e)}")
                    raise

                if args.trinity:
                    link_context(n4j, args.trinity_gid1)
            if args.crossgraphmerge:
                merge_similar_nodes(n4j, None)

    # Handle MCQ evaluation using the imported functions from mcq_evaluation.py
    if args.inference:
        if args.mcq_eval:
            # Use the run_inference function from mcq_evaluation.py
            mcq_questions = load_mcq_questions(args.questions_file)
            inference_results = run_inference(n4j, mcq_questions, args.results_file)
            
            # If evaluate flag is also set, perform evaluation immediately
            if args.evaluate:
                evaluate_mcq_performance(inference_results)
        else:
            # Original inference code for non-MCQ evaluation
            questions = load_high("./prompt.txt").split("\n\n")  # assuming questions are separated by double newline
            questions = [q.strip() for q in questions if q.strip()]  # clean up
            if args.diagnoses:
                questions.insert(0,"Provide all the possible diagnoses for this patient's case.\n")
                print(questions)
            all_responses = []

            for idx, question in enumerate(questions):
                print(f"\nProcessing Question {idx+1}: {question}\n")

                # Generate summary for this single question
                summaries = process_chunks(question)  # returns a list (may contain 1 item)

                for summary in summaries:
                    # Retrieve relevant subgraph
                    gid = seq_ret(n4j, summary)

                    # Query graph and get response
                    response = get_response(n4j, gid, question)
                    all_responses.append((question, response))
        
    
    elif args.evaluate and args.mcq_eval:
        # Load previously saved inference results and evaluate using mcq_evaluation.py
        try:
            inference_results = load_inference_results(args.results_file)
            evaluate_mcq_performance(inference_results)
        except FileNotFoundError:
            print(f"Error: Results file '{args.results_file}' not found. Run inference first or specify correct file path.")