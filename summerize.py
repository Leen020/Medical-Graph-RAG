import openai
from concurrent.futures import ThreadPoolExecutor
import tiktoken
import os
from openai import AzureOpenAI
# from langchain_openai import AzureChatOpenAI
from openai import BadRequestError

# Add your own OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")

# Generate a structured summary from the provided medical source (report, paper, or book), strictly adhering to the following categories. The summary should list key information under each category in a concise format: 'CATEGORY_NAME: Key information'. No additional explanations or detailed descriptions are necessary unless directly related to the categories:

sum_prompt = """
Verilen girdiden (bir cümle, rapor, makale, kitap veya çoktan seçmeli soru (MCQ) olabilir) yapılandırılmış bir tıbbi özet oluşturun. Yalnızca girdide sunulan tıbbi içeriğe odaklanın (cevap seçeneklerini, ilgili tıbbi gerçekler içermedikçe yok sayın).

Çıktı aşağıda belirtilen sırayla aşağıdaki tüm kategorileri içermelidir. Bir kategoriyle ilgili bilgi yoksa değer olarak "None" yazın. Özet, her kategori altında temel bilgileri şu özlü biçimde listelemelidir: 'CATEGORY_NAME: Önemli bilgi'. Kategorilerle doğrudan ilgili olmadıkça ek açıklamalara veya ayrıntılı betimlemelere gerek yoktur:

ANATOMICAL_STRUCTURE: Özellikle ele alınan anatomik yapılardan bahsedin.
BODY_FUNCTION: Vurgulanan vücut işlevlerini listeleyin.
BODY_MEASUREMENT: Kan basıncı veya vücut sıcaklığı gibi normal ölçümleri ekleyin.
BM_RESULT: Bu ölçümlerin sonuçları.
BM_UNIT: Her ölçümün birimleri.
BM_VALUE: Bu ölçümlerin değerleri.
LABORATORY_DATA: Bahsedilen laboratuvar testlerini özetleyin.
LAB_RESULT: Bu testlerin sonuçları (örn., "artmış", "azalmış").
LAB_VALUE: Testlerden elde edilen spesifik değerler.
LAB_UNIT: Bu değerlerin ölçü birimleri.
MEDICINE: Ele alınan ilaçların adlarını yazın.
MED_DOSE, MED_DURATION, MED_FORM, MED_FREQUENCY, MED_ROUTE, MED_STATUS, MED_STRENGTH, MED_UNIT, MED_TOTALDOSE: Her ilaç özniteliği için özlü ayrıntılar verin.
PROBLEM: Herhangi bir tıbbi durum veya bulguyu belirtin.
PROCEDURE: Herhangi bir işlemi (prosedürü) açıklayın.
PROCEDURE_RESULT: Bu işlemlerin sonuçları.
PROC_METHOD: Kullanılan yöntemler.
SEVERITY: Bahsedilen durumların şiddeti.
MEDICAL_DEVICE: Kullanılan tıbbi cihazları listeleyin.
SUBSTANCE_ABUSE: Bahsedilen herhangi bir madde kötüye kullanımını not edin.

Her kategori yalnızca tıbbi kaynağın içeriğiyle ilgiliyse ele alınmalıdır. Özeti hızlı başvuruya uygun olacak şekilde açık ve doğrudan tutun.
"""


azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_deployment = os.getenv("AZURE_DEPLOYMENT_NAME")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

llm = AzureOpenAI(
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
  api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
  api_version="2024-08-01-preview"
)

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
            print(f"responses in summerize.py/process_chunks = {responses}")
        except BadRequestError:
            print("Skipping chunk due to content filter violation.")
            responses = []
    # print(responses)
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