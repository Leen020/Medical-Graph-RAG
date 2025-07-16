from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
import uuid
import os
from typing import Optional
from pydantic import BaseModel
from langchain.chains.openai_functions import create_extraction_chain_pydantic
from dotenv import load_dotenv

load_dotenv()

class AgenticChunker:
    def __init__(self, azure_openai_api_key=None, azure_deployment=None, azure_endpoint=None):
        self.chunks = {}
        self.id_truncate_limit = 5

        # Whether or not to update/refine summaries and titles as you get new information
        self.generate_new_metadata_ind = True
        self.print_logging = True

        # Load API credentials from environment variables if not provided
        if azure_openai_api_key is None:
            azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if azure_deployment is None:
            azure_deployment = os.getenv("AZURE_DEPLOYMENT_NAME")

        if azure_endpoint is None:
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        # Ensure API key is provided
        if not azure_endpoint:
            raise ValueError("Azure OpenAI ENDPOINT must be provided or set in environment variables")
        
        # Ensure API key is provided
        if not azure_openai_api_key:
            raise ValueError("Azure OpenAI API key must be provided or set in environment variables")
        
        if not azure_deployment:
            raise ValueError("Azure deployment name must be provided or set in environment variables")
        
        # model for text extraction
        self.llm = AzureChatOpenAI(
            model="gpt-4o-mini", 
            api_key=azure_openai_api_key,
            api_version="2024-08-01-preview",
            azure_endpoint=azure_endpoint,
            azure_deployment=azure_deployment
        )
        print("GPT-4o-mini is called in agentic_chunker.py")
        print(f"FINISHED INITIALIZING LLM WITHOUT ERRORS")
    # allows batch addition of propositions, while add_proposition handles each one individually.
    def add_propositions(self, propositions):
        for proposition in propositions:
            self.add_proposition(proposition)
    
    def add_proposition(self, proposition):
        if self.print_logging:
            print (f"\nAdding: '{proposition}'")

        # If it's your first chunk, just make a new chunk and don't check for others
        if len(self.chunks) == 0:
            if self.print_logging:
                print ("No chunks, creating a new one")
            self._create_new_chunk(proposition)
            return

        chunk_id = self._find_relevant_chunk(proposition)

        # If a chunk was found then add the proposition to it
        if chunk_id and chunk_id in self.chunks:
            if self.print_logging:
                print (f"Chunk Found ({self.chunks[chunk_id]['chunk_id']}), adding to: {self.chunks[chunk_id]['title']}")
            self.add_proposition_to_chunk(chunk_id, proposition)
            return
        else:
            # Handle invalid chunk_id (treat as no chunk found)
            if self.print_logging:
                print(f"Invalid chunk ID {chunk_id} or no chunk found. Creating new chunk.")
            # If a chunk wasn't found, then create a new one
            self._create_new_chunk(proposition)
        

    def add_proposition_to_chunk(self, chunk_id, proposition):
        # Add then
        self.chunks[chunk_id]['propositions'].append(proposition)

        # Then grab a new summary
        if self.generate_new_metadata_ind:
            self.chunks[chunk_id]['summary'] = self._update_chunk_summary(self.chunks[chunk_id])
            self.chunks[chunk_id]['title'] = self._update_chunk_title(self.chunks[chunk_id])

    def _update_chunk_summary(self, chunk):
        """
        If you add a new proposition to a chunk, you may want to update the summary or else they could get stale
        """
        PROMPT = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    Benzer bir konudan bahseden cümle gruplarını temsil eden chunk kümelerinin sorumlususunuz.
                    Chunk’larınızdan birine yeni bir proposition eklendi; izleyicilere bu chunk grubunun ne hakkında
                    olduğunu bildirecek, çok kısa (1 cümle) bir özet üretmelisiniz.

                    İyi bir özet, chunk’ın konusunu belirtir ve chunk’a ne eklenebileceğine dair net talimatlar sunar.

                    Size, chunk içindeki proposition’ların listesi ve chunk’ın mevcut özeti verilecek.

                    Özetleriniz genelleştirmeyi göz önünde bulundurmalıdır. Örneğin, bir proposition elmalarla ilgiliyse
                    bunu “yiyecek” olarak genelleyin; bir ay adı geçiyorsa “tarih ve zaman” olarak genelleyin.

                    Örnek:
                    Girdi: Proposition: Greg likes to eat pizza
                    Çıktı: Bu chunk, Greg’in yemekten hoşlandığı yiyecek türleri hakkında bilgiler içerir.

                    Yalnızca chunk’ın yeni özetini döndürün, başka hiçbir şey yazmayın.
                    """,
                ),
                (
                    "user",
                    "Chunk'ın proposition'ları:\n{proposition}\n\nMevcut chunk özeti:\n{current_summary}",
                ),
            ]
        )

        runnable = PROMPT | self.llm

        new_chunk_summary = runnable.invoke({
            "proposition": "\n".join(chunk['propositions']),
            "current_summary": chunk['summary']
        }).content

        return new_chunk_summary

    
    def _update_chunk_title(self, chunk):
        """
        If you add a new proposition to a chunk, you may want to update the title or else it can get stale
        """
        PROMPT = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    Benzer bir konudan bahseden cümle gruplarını temsil eden chunk kümelerinin sorumlususunuz.
                    Chunk’larınızdan birine yeni bir proposition eklendi; izleyicilere bu chunk grubunun ne
                    hakkında olduğunu bildirecek, çok kısa bir güncellenmiş başlık üretmelisiniz.

                    İyi bir başlık, chunk’ın konusunu açıkça belirtir.

                    Size chunk’taki proposition’ların listesi, chunk özeti ve mevcut chunk başlığı verilecek.

                    Başlığınız genelleştirmeyi göz önünde bulundurmalıdır. Örneğin, bir proposition elmalarla
                    ilgiliyse bunu “yiyecek” olarak genelleyin; bir ay adı geçiyorsa “tarih ve zaman” olarak
                    genelleyin.

                    Örnek:
                    Girdi: Summary: This chunk is about dates and times that the author talks about
                    Çıktı: Dates & Times

                    Yalnızca yeni chunk başlığını döndürün, başka hiçbir şey yazmayın.
                    """,
                ),
                (
                    "user",
                    "Chunk'ın proposition'ları:\n{proposition}\n\nChunk özeti:\n{current_summary}\n\nMevcut chunk başlığı:\n{current_title}",
                ),
            ]
        )

        runnable = PROMPT | self.llm

        updated_chunk_title = runnable.invoke({
            "proposition": "\n".join(chunk['propositions']),
            "current_summary": chunk['summary'],
            "current_title": chunk['title']
        }).content

        return updated_chunk_title

    def _get_new_chunk_summary(self, proposition):
        PROMPT = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    Benzer konulardan bahseden cümle gruplarını (chunk’ları) yöneten sorumlusunuz.
                    İzleyicilere bu chunk grubunun ne hakkında olduğunu bildirecek, çok kısa (1 cümle) bir özet üretmelisiniz.

                    İyi bir özet, chunk’ın konusunu belirtmeli ve chunk’a neler eklenebileceğine dair açıklayıcı talimatlar vermelidir.

                    Size, yeni bir chunk’a eklenecek bir proposition verilecek. Bu yeni chunk’ın bir özete ihtiyacı var.

                    Özetiniz genelleştirmeyi göz önünde bulundurmalıdır. Bir proposition elmalarla ilgiliyse “yiyecek” olarak genelleyin;
                    bir ay adı içeriyorsa “tarih ve zaman” olarak genelleyin.

                    Örnek:
                    Input: Proposition: Greg likes to eat pizza
                    Output: This chunk contains information about the types of food Greg likes to eat.

                    Yalnızca yeni chunk özetini döndürün, başka hiçbir şey yazmayın.
                    """,
                ),
                (
                    "user",
                    "Bu proposition'ın ekleneceği yeni chunk'ın özetini belirleyin:\n{proposition}"
                ),
            ]
        )

        runnable = PROMPT | self.llm

        new_chunk_summary = runnable.invoke({
            "proposition": proposition
        }).content

        return new_chunk_summary
    
    def _get_new_chunk_title(self, summary):
        PROMPT = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    Benzer bir konudan bahseden cümle gruplarını (chunk’ları) yöneten sorumlusunuz.
                    İzleyicilere bu chunk grubunun ne hakkında olduğunu bildirecek, birkaç kelimelik çok kısa bir chunk başlığı üretmelisiniz.

                    İyi bir chunk başlığı kısadır ama chunk’ın konusunu kapsar.

                    Size başlığa ihtiyaç duyan bir chunk özetini vereceğiz.

                    Başlıklarınız genelleştirmeyi göz önünde bulundurmalıdır. Bir proposition elmalarla ilgiliyse “yiyecek” olarak genelleyin;
                    bir ay adı içeriyorsa “tarih ve zaman” olarak genelleyin.

                    Örnek:
                    Girdi: Summary: This chunk is about dates and times that the author talks about
                    Çıktı: Dates & Times

                    Yalnızca yeni chunk başlığını döndürün, başka hiçbir şey yazmayın.
                    """,
                ),
                (
                    "user",
                    "Bu özetin ait olduğu chunk'ın başlığını belirleyin:\n{summary}"
                ),
            ]
        )

        runnable = PROMPT | self.llm

        new_chunk_title = runnable.invoke({
            "summary": summary
        }).content

        return new_chunk_title


    def _create_new_chunk(self, proposition):
        new_chunk_id = str(uuid.uuid4())[:self.id_truncate_limit] # I don't want long ids
        print(f"new chunk id = {new_chunk_id}")
        new_chunk_summary = self._get_new_chunk_summary(proposition)
        print(f"summary {new_chunk_summary}")
        new_chunk_title = self._get_new_chunk_title(new_chunk_summary)

        self.chunks[new_chunk_id] = {
            'chunk_id' : new_chunk_id,
            'propositions': [proposition],
            'title' : new_chunk_title,
            'summary': new_chunk_summary,
            'chunk_index' : len(self.chunks)
        }
        if self.print_logging:
            print (f"Yeni chunk oluşturuldu ({new_chunk_id}): {new_chunk_title}")
    
    def get_chunk_outline(self):
        """
        Get a string which represents the chunks you currently have.
        This will be empty when you first start off
        """
        chunk_outline = ""

        for chunk_id, chunk in self.chunks.items():
            single_chunk_string = f"""Chunk ID: {chunk['chunk_id']}\nChunk Adı: {chunk['title']}\nChunk Özeti: {chunk['summary']}\n\n"""
            chunk_outline += single_chunk_string
        
        return chunk_outline

    def _find_relevant_chunk(self, proposition):
        current_chunk_outline = self.get_chunk_outline()
        print(current_chunk_outline)

        PROMPT = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    "Proposition"ın mevcut chunk'lardan herhangi birine ait olup olmadığını belirleyin.

                    Bir proposition, anlamı, yönü veya amacı benzerse bir chunk'a eklenmelidir.
                    Amaç, benzer proposition’ları ve chunk’ları gruplaştırmaktır.

                    Bir proposition’ın mevcut bir chunk ile birleştirilmesi gerektiğini düşünüyorsanız, ilgili chunk kimliğini döndürün.
                    Bir öğenin mevcut chunk’lardan herhangi biriyle birleştirilmemesi gerektiğini düşünüyorsanız yalnızca "No chunks" döndürün.

                    Örnek:
                    Input:
                        - Proposition: "Greg köfte yemekten gerçekten hoşlanır"
                        - Current Chunks:
                            - Chunk ID: 2n4l3
                            - Chunk Name: İstanbul’daki Yerler
                            - Chunk Summary: İstanbul’da gezilecek yerlerle ilgili genel bakış

                            - Chunk ID: 93833
                            - Chunk Name: Greg'in Sevdiği Yiyecekler
                            - Chunk Summary: Greg'in sevdiği yiyecek ve yemeklerin listesi
                    Output: 93833
                    """,
                ),
                (
                    "user",
                    "Mevcut Chunk'lar:\n--Mevcut chunk'ların başlangıcı--\n{current_chunk_outline}\n--Mevcut chunk'ların sonu--"
                ),
                (
                    "user",
                    "Aşağıdaki ifadeyi yukarıda listelenen chunk'lardan birine dahil etmek gerekip gerekmediğini belirleyin:\n{proposition}"
                ),
            ]

        )

        runnable = PROMPT | self.llm

        chunk_found = runnable.invoke({
            "proposition": proposition,
            "current_chunk_outline": current_chunk_outline
        }).content

        # Pydantic data class
        class ChunkID(BaseModel):
            """Extracting the chunk id"""
            chunk_id: Optional[str]
            
        # Extraction to catch-all LLM responses. This is a bandaid
        extraction_chain = create_extraction_chain_pydantic(pydantic_schema=ChunkID, llm=self.llm)
        extraction_found = extraction_chain.run(chunk_found)
        if extraction_found:
            chunk_found = extraction_found[0].chunk_id

        # If you got a response that isn't the chunk id limit, chances are it's a bad response or it found nothing
        # So return nothing
        if chunk_found is not None and len(chunk_found) != self.id_truncate_limit:
            return None

        return chunk_found
    
    def get_chunks(self, get_type='dict'):
        """
        This function returns the chunks in the format specified by the 'get_type' parameter.
        If 'get_type' is 'dict', it returns the chunks as a dictionary.
        If 'get_type' is 'list_of_strings', it returns the chunks as a list of strings, where each string is a proposition in the chunk.
        """
        if get_type == 'dict':
            return self.chunks
        if get_type == 'list_of_strings':
            chunks = []
            for chunk_id, chunk in self.chunks.items():
                chunks.append(" ".join([x for x in chunk['propositions']]))
            return chunks
    
    def pretty_print_chunks(self):
        print (f"\nYou have {len(self.chunks)} chunks\n")
        for chunk_id, chunk in self.chunks.items():
            print(f"Chunk #{chunk['chunk_index']}")
            print(f"Chunk ID: {chunk_id}")
            print(f"Title: {chunk['title']}")
            print(f"Summary: {chunk['summary']}")
            print(f"Propositions:")
            for prop in chunk['propositions']:
                print(f"    -{prop}")
            print("\n\n")

    def pretty_print_chunk_outline(self):
        print ("Chunk Outline\n")
        print(self.get_chunk_outline())

if __name__ == "__main__":
    ac = AgenticChunker()

    ## Comment and uncomment the propositions to your hearts content
    propositions = [
        'The month is October.',
        'The year is 2023.',
        "One of the most important things that I didn't understand about the world as a child was the degree to which the returns for performance are superlinear.",
        'Teachers and coaches implicitly told us that the returns were linear.',
        "I heard a thousand times that 'You get out what you put in.'",
        'Teachers and coaches meant well.',
        "The statement that 'You get out what you put in' is rarely true.",
        "If your product is only half as good as your competitor's product, you do not get half as many customers.",
        "You get no customers if your product is only half as good as your competitor's product.",
        'You go out of business if you get no customers.',
        'The returns for performance are superlinear in business.',
        'Some people think the superlinear returns for performance are a flaw of capitalism.',
        'Some people think that changing the rules of capitalism would stop the superlinear returns for performance from being true.',
        'Superlinear returns for performance are a feature of the world.',
        'Superlinear returns for performance are not an artifact of rules that humans have invented.',
        'The same pattern of superlinear returns is observed in fame.',
        'The same pattern of superlinear returns is observed in power.',
        'The same pattern of superlinear returns is observed in military victories.',
        'The same pattern of superlinear returns is observed in knowledge.',
        'The same pattern of superlinear returns is observed in benefit to humanity.',
        'In fame, power, military victories, knowledge, and benefit to humanity, the rich get richer.'
    ]
    
    ac.add_propositions(propositions)
    ac.pretty_print_chunks()
    ac.pretty_print_chunk_outline()
    print (ac.get_chunks(get_type='list_of_strings'))
