# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
from typing import Optional, Union

try:
    from unstructured.documents.elements import Element
except ImportError:
    Element = None

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import BaseModelBackend
from camel.prompts import TextPrompt
from camel.storages.graph_storages.graph_element import (
    GraphElement,
    Node,
    Relationship,
)
from camel.types import RoleType

# AgentOps decorator setting
try:
    import os

    if os.getenv("AGENTOPS_API_KEY") is not None:
        from agentops import track_agent
    else:
        raise ImportError
except (ImportError, AttributeError):
    from camel.utils import track_agent


text_prompt = """
Verilen içerikten düğümleri (nodes) ve ilişkileri (relationships) çıkarmanız ve bunları Node ile Relationship nesnelerine dönüştürmeniz bekleniyor. İşte yapmanız gerekenlerin özeti:

İçerik Çıkarma:
Girdi içeriğini işleyebilmeniz ve içinde geçen varlıkları (entities) tanımlayabilmeniz gerekir.
Varlıklar, bağlamda ayrı varlıkları temsil eden ad öbekleri veya kavramlar olabilir.

Düğüm (Node) Çıkarma:
Tanımlanan her varlık için bir Node nesnesi oluşturmalısınız.
Her Node nesnesinin benzersiz bir tanımlayıcısı (id) ve bir türü (type) olmalıdır.
Düğüme ait ek özellikler de çıkarılıp saklanabilir.

İlişki (Relationship) Çıkarma:
İçerikte geçen varlıklar arasındaki ilişkileri belirlemelisiniz.
Her ilişki için bir Relationship nesnesi oluşturun.
Bir Relationship nesnesi, ilişkide yer alan varlıkları temsil eden Node nesneleri olan bir özne (subj) ve bir nesneye (obj) sahiptir.
Her ilişkinin ayrıca bir türü (type) ve uygulanabilirse ek özellikleri olmalıdır.

Çıktı Biçimlendirme:
Çıkarılan düğüm ve ilişkiler, sağlanan Node ile Relationship sınıflarının örnekleri olarak biçimlendirilmelidir.
Elde edilen verilerin sınıflarda tanımlanan yapıya uygun olduğundan emin olun.
Çıktıyı, verilen koda karşı kolayca doğrulanabilecek bir biçimde üretin.

Sizin İçin Talimatlar:
– Verilen içeriği dikkatlice okuyun.
– İçerikte geçen farklı varlıkları belirleyin ve bunları düğümler olarak kategorize edin.
– Bu varlıklar arasındaki ilişkileri saptayın ve yönlendirilmiş ilişkiler şeklinde temsil edin.
– Çıkarılan düğüm ve ilişkileri aşağıdaki belirtilen biçimde verin.

Sizin için Örnek:

Örnek İçerik:
"Ahmet, XYZ Şirketi'nde çalışıyor. Kendisi bir yazılım mühendisidir. Şirket İstanbul'da bulunmaktadır."

Beklenen Çıktı:

Düğümler:

Node(id='Ahmet', type='Person')
Node(id='XYZ Şirketi', type='Organization')
Node(id='İstanbul', type='Location')

İlişkiler:

Relationship(subj=Node(id='Ahmet', type='Person'), obj=Node(id='XYZ Şirketi', type='Organization'), type='Calisir')
Relationship(subj=Node(id='Ahmet', type='Person'), obj=Node(id='İstanbul', type='Location'), type='IkametEder')

===== TASK =====
Lütfen verilen içerikten düğümleri ve ilişkileri Türkçe dilinde çıkararak bunları Node ve Relationship nesnelerine yapılandırın.

{task}
"""


@track_agent(name="KnowledgeGraphAgent")
class KnowledgeGraphAgent(ChatAgent):
    r"""An agent that can extract node and relationship information for
    different entities from given `Element` content.

    Attributes:
        task_prompt (TextPrompt): A prompt for the agent to extract node and
            relationship information for different entities.
    """

    def __init__(
        self,
        model: Optional[BaseModelBackend] = None,
    ) -> None:
        r"""Initialize the `KnowledgeGraphAgent`.

        Args:
        model (BaseModelBackend, optional): The model backend to use for
            generating responses. (default: :obj:`OpenAIModel` with
            `GPT_4O_MINI`)
        """
        system_message = BaseMessage(
            role_name="Graphify",
            role_type=RoleType.ASSISTANT,
            meta_dict=None,
            content="Your mission is to transform unstructured content in Turkish Language"
            "into structured graph data also in Turkish. Extract nodes and relationships with "
            "precision, and let the connections unfold. Your graphs will "
            "illuminate the hidden connections within the chaos of "
            "information.",
        )
        super().__init__(system_message, model=model)

    def run(
        self,
        element: Union[str, Element],
        parse_graph_elements: bool = False,
    ) -> Union[str, GraphElement]:
        r"""Run the agent to extract node and relationship information.

        Args:
            element (Union[str, Element]): The input element or string.
            parse_graph_elements (bool, optional): Whether to parse into
                `GraphElement`. Defaults to `False`.

        Returns:
            Union[str, GraphElement]: The extracted node and relationship
                information. If `parse_graph_elements` is `True` then return
                `GraphElement`, else return `str`.
        """
        self.reset()
        self.element = element

        knowledge_graph_prompt = TextPrompt(text_prompt)
        knowledge_graph_generation = knowledge_graph_prompt.format(
            task=str(element)
        )

        knowledge_graph_generation_msg = BaseMessage.make_user_message(
            role_name="Graphify", content=knowledge_graph_generation
        )

        response = self.step(input_message=knowledge_graph_generation_msg)

        content = response.msg.content

        if parse_graph_elements:
            content = self._parse_graph_elements(content)

        return content

    def _validate_node(self, node: Node) -> bool:
        r"""Validate if the object is a valid Node.

        Args:
            node (Node): Object to be validated.

        Returns:
            bool: True if the object is a valid Node, False otherwise.
        """
        return (
            isinstance(node, Node)
            and isinstance(node.id, (str, int))
            and isinstance(node.type, str)
        )

    def _validate_relationship(self, relationship: Relationship) -> bool:
        r"""Validate if the object is a valid Relationship.

        Args:
            relationship (Relationship): Object to be validated.

        Returns:
            bool: True if the object is a valid Relationship, False otherwise.
        """
        return (
            isinstance(relationship, Relationship)
            and self._validate_node(relationship.subj)
            and self._validate_node(relationship.obj)
            and isinstance(relationship.type, str)
        )

    def _parse_graph_elements(self, input_string: str) -> GraphElement:
        r"""Parses graph elements from given content.

        Args:
            input_string (str): The input content.

        Returns:
            GraphElement: The parsed graph elements.
        """
        import re

        # Regular expressions to extract nodes and relationships
        node_pattern = r"Node\(id='(.*?)', type='(.*?)'\)"
        rel_pattern = (
            r"Relationship\(subj=Node\(id='(.*?)', type='(.*?)'\), "
            r"obj=Node\(id='(.*?)', type='(.*?)'\), type='(.*?)'\)"
        )

        nodes = {}
        relationships = []

        # Extract nodes
        for match in re.finditer(node_pattern, input_string):
            id, type = match.groups()
            properties = {'source': 'agent_created'}
            if id not in nodes:
                node = Node(id=id, type=type, properties=properties)
                if self._validate_node(node):
                    nodes[id] = node

        # Extract relationships
        for match in re.finditer(rel_pattern, input_string):
            subj_id, subj_type, obj_id, obj_type, rel_type = match.groups()
            properties = {'source': 'agent_created'}
            if subj_id in nodes and obj_id in nodes:
                subj = nodes[subj_id]
                obj = nodes[obj_id]
                relationship = Relationship(
                    subj=subj, obj=obj, type=rel_type, properties=properties
                )
                if self._validate_relationship(relationship):
                    relationships.append(relationship)

        return GraphElement(
            nodes=list(nodes.values()),
            relationships=relationships,
            source=self.element,
        )
