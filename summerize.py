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
Verilen tıbbi kaynaktan (rapor, makale veya kitap) aşağıdaki kategorilere kesinlikle uyarak yapılandırılmış bir özet oluşturun. Özet, her kategori altında kilit bilgileri 'CATEGORY_NAME: Önemli bilgi' biçiminde kısaca listelemelidir. Kategorilerle doğrudan ilişkili olmadıkça ek açıklama veya ayrıntılı tanımlara gerek yoktur:

ANATOMICAL_STRUCTURE: Özellikle ele alınan anatomik yapıları belirtin.
BODY_FUNCTION: Vurgulanan vücut işlevlerini listeleyin.
BODY_MEASUREMENT: Kan basıncı, vücut sıcaklığı gibi normal ölçümleri ekleyin.
BM_RESULT: Bu ölçümlerin sonuçları.
BM_UNIT: Her ölçümün birimleri.
BM_VALUE: Bu ölçümlerin değerleri.
LABORATORY_DATA: Bahsedilen laboratuvar testlerini özetleyin.
LAB_RESULT: Bu testlerin sonuçları (örn. 'artmış', 'azalmış').
LAB_VALUE: Testlerden elde edilen spesifik değerler.
LAB_UNIT: Bu değerlerin ölçü birimleri.
MEDICINE: Ele alınan ilaçların adları.
MED_DOSE, MED_DURATION, MED_FORM, MED_FREQUENCY, MED_ROUTE, MED_STATUS, MED_STRENGTH, MED_UNIT, MED_TOTALDOSE: Her ilaç için bu özniteliklere dair öz bilgileri verin.
PROBLEM: Tespit edilen tıbbi durum veya bulguları belirtin.
PROCEDURE: Herhangi bir prosedürü tanımlayın.
PROCEDURE_RESULT: Bu prosedürlerin sonuçları.
PROC_METHOD: Kullanılan yöntemler.
SEVERITY: Bahsi geçen durumların şiddeti.
MEDICAL_DEVICE: Kullanılan tıbbi cihazları listeleyin.
SUBSTANCE_ABUSE: Belirtilen madde kötüye kullanımı varsa belirtin.

Her kategori yalnızca tıbbi kaynağın içeriğiyle ilgiliyse ele alınmalıdır. Özet, hızlı başvuru için net ve doğrudan olmalıdır.
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
            max_tokens=500, # max tokens was max
             n=1,
            stop=None  
            )
        print("GPT-4o-mini is called in summerize.py")
        return response.choices[0].message.content
    except BadRequestError as e:
        if "content_filter" in str(e):
            print(f"Content filter triggered. Deleting problematic file...")
            delete_problematic_file(chunk)  # Pass the problematic content to delete the file
        raise  # Re-raise the exception after handling

# look why there are spaces
def split_into_chunks(text, tokens=500):
    encoding = tiktoken.encoding_for_model('gpt-4o-mini')
    print("GPT-4o-mini is called for encoding in summerize.py")
    # print(f"Text before encoding = {text}")
    words = encoding.encode(text)
    # print(f"Text after encoding = {words}")
    chunks = [] 
    for i in range(0, len(words), tokens):
        chunks.append(' '.join(encoding.decode(words[i:i + tokens])))
    #     print(f"Decoding chunk number {i} = {chunks}")
    # print(f"chunks after decoding = {chunks}")
    return chunks

def process_chunks(content):
    chunks = split_into_chunks(content)

    # Processes chunks in parallel
    with ThreadPoolExecutor() as executor:
        try:
            print(f"chunks in summerize.py/process_chunks = {chunks}")
            responses = list(executor.map(call_openai_api, chunks))
            print(f"responses in summerize.py/process_chunks = {responses}")
        except BadRequestError:
            print("Skipping chunk due to content filter violation.")
            responses = []
    print(f"All responses in summerize.py/process_chunks = {responses}")
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