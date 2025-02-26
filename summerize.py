import openai
from concurrent.futures import ThreadPoolExecutor
import tiktoken
import os
from openai import AzureOpenAI
# from langchain_openai import AzureChatOpenAI
from openai import BadRequestError

# Add your own OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")

sum_prompt = """
Generate a structured summary from the provided medical source (report, paper, or book), strictly adhering to the following categories. The summary should list key information under each category in a concise format: 'CATEGORY_NAME: Key information'. No additional explanations or detailed descriptions are necessary unless directly related to the categories:

ANATOMICAL_STRUCTURE: Mention any anatomical structures specifically discussed.
BODY_FUNCTION: List any body functions highlighted.
BODY_MEASUREMENT: Include normal measurements like blood pressure or temperature.
BM_RESULT: Results of these measurements.
BM_UNIT: Units for each measurement.
BM_VALUE: Values of these measurements.
LABORATORY_DATA: Outline any laboratory tests mentioned.
LAB_RESULT: Outcomes of these tests (e.g., 'increased', 'decreased').
LAB_VALUE: Specific values from the tests.
LAB_UNIT: Units of measurement for these values.
MEDICINE: Name medications discussed.
MED_DOSE, MED_DURATION, MED_FORM, MED_FREQUENCY, MED_ROUTE, MED_STATUS, MED_STRENGTH, MED_UNIT, MED_TOTALDOSE: Provide concise details for each medication attribute.
PROBLEM: Identify any medical conditions or findings.
PROCEDURE: Describe any procedures.
PROCEDURE_RESULT: Outcomes of these procedures.
PROC_METHOD: Methods used.
SEVERITY: Severity of the conditions mentioned.
MEDICAL_DEVICE: List any medical devices used.
SUBSTANCE_ABUSE: Note any substance abuse mentioned.
Each category should be addressed only if relevant to the content of the medical source. Ensure the summary is clear and direct, suitable for quick reference.
"""

azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_deployment = os.getenv("AZURE_DEPLOYMENT_NAME")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

llm = AzureOpenAI(
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
  api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
  api_version="2024-08-01-preview"
)

# def call_openai_api(chunk):
#     try:
#         response = llm.invoke([
#                 {"role": "system", "content": sum_prompt},
#                 {"role": "user", "content": f" {chunk}"},
#             ])
#         return response.content
#     except BadRequestError as e:
#         if "content_filter" in str(e):
#             print(f"Content filter triggered. Deleting problematic file...")
#             delete_problematic_file(chunk)  # Pass the problematic content to delete the file
#         raise  # Re-raise the exception after handling

def call_openai_api(chunk):
    try:
        response = llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
            {"role": "system", "content": sum_prompt},
            {"role": "user", "content": f" {chunk}"}],
            temperature=0.5,
            max_tokens=500,
            n=1,
            stop=None  
            )
        return response.choices[0].message.content
    except BadRequestError as e:
        if "content_filter" in str(e):
            print(f"Content filter triggered. Deleting problematic file...")
            delete_problematic_file(chunk)  # Pass the problematic content to delete the file
        raise  # Re-raise the exception after handling

def split_into_chunks(text, tokens=500):
    encoding = tiktoken.encoding_for_model('gpt-4o-mini')
    words = encoding.encode(text)
    chunks = [] 
    for i in range(0, len(words), tokens):
        chunks.append(' '.join(encoding.decode(words[i:i + tokens])))
    print(f"chunks = {chunks}")
    return chunks   

def process_chunks(content):
    chunks = split_into_chunks(content)

    # Processes chunks in parallel
    with ThreadPoolExecutor() as executor:
        try:
            responses = list(executor.map(call_openai_api, chunks))
        except BadRequestError:
            print("Skipping chunk due to content filter violation.")
            responses = []
    print(responses)
    return responses

def delete_problematic_file(content):
    """
    Identify and delete the problematic file based on the content that caused the error.
    """
    # Specify the directory containing your .txt files
    directory = 'dataset'
    
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as file:
                file_content = file.read()
                if content in file_content:  # Check if the problematic content is in this file
                    print(f"Deleting problematic file: {filename}")
                    os.remove(filepath)
                    return  # Exit after deleting the problematic file

if __name__ == "__main__":
    content = " sth you wanna test"
    process_chunks(content)
    print(f"DONE")

# Can take up to a few minutes to run depending on the size of your data input