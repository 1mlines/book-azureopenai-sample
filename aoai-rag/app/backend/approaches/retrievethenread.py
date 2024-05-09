from typing import Any

from openai import AsyncOpenAI
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import (
    QueryType,
    VectorizedQuery
)
from approaches.approach import AskApproach
from core.messagebuilder import MessageBuilder
from text import nonewlines

class RetrieveThenReadApproach(AskApproach):
    """
    Simple retrieve-then-read implementation, using the Azure AI Search(Cognitive Search) and OpenAI APIs directly. It first retrieves
    top documents from search, then constructs a prompt with them, and then uses OpenAI to generate an completion
    (answer) with that prompt.
    Azure AI Search(Cognitive Search)와 Azure OpenAI의 API를 사용한 retrieve-then-read 구현 예시다.
    우선 검색에서 상위를 차지한 문서들을 활용해서 프롬프트를 작성하고, OpenAI로 보완된 응답을 생성한다.
    """

    system_chat_template = \
"너는 한국사 질문을 답변해주는 역사 교수야." + \
"질문자가 '나'로 질문해도 '당신'으로 질문자를 지칭해야해" + \
"다음 질문은 아래 출처에서 제공되는 정보만 사용해서 답변해줘." + \
"표로 나타낸 정보는 html 테이블로 반환해줘. 마크다운은 사용하면 안돼." + \
"각 출처에는 이름 뒤에 콜론과 실제 정보가 있고 답변에 사용하는 정보에는 반드시 출처를 기재해야해." + \
"아래 출처 중에서 답변할 수 없으면 '잘 모르겠습니다'라고만 답변해줘." 
    #shots/sample conversation
    question = """
'Question: '최충헌의 생에를 알려줘.'

Sources:
info1.txt: 1196년부터 1219년까지 23년 동안 고려 왕조의 실권을 맡았다. 최씨 정권을 연 첫 권력자이자 장군이다.
info2.pdf: 이의민을 제거하고 집권한 다섯번째 무인 집권자였으며, 무신 세습 정권을 구축하였다.
info3.pdf: 이후 경쟁자 두경승과 동생 최충수, 조카 박진재를 모두 제거한 뒤 일인 집권체제를 구축했고, 집권 기간 중 국왕인 명종과 희종을 폐위시켰다.
info4.pdf: 1219년 9월에 개성부 안흥리(安興里) 집에서 사망했는데, <고려사>에 의하면 그는 죽기 전 연회를 열다가 죽었다고 기록하고 있다.
"""
    answer = "최충헌(崔忠獻, 1149년 ~ 1219년 10월 29일)은 고려 시대 중기에서 후기에 활동한 무신이자 정치가로, 최씨 무신 정권의 첫 지도자입니다.[info1.txt] 그는 1196년부터 1219년까지 23년 동안 고려 왕조의 실권을 잡고, 국왕 명종과 희종을 폐위시키기도 했습니다. 또한 무신 세습 정권을 구축하고, 주요 경쟁자들을 제거하여 독재 체제를 확립했습니다.[info2.pdf][info3.pdf] 1219년에 사망하였고, 그의 장례식은 고려의 임금의 장례식과 다를 바 없었다고 전해집니다.[info4.pdf]"

    def __init__(self, search_client: SearchClient, openai_client: AsyncOpenAI, openai_deployment: str, chatgpt_model: str, embedding_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.openai_client = openai_client
        self.openai_deployment = openai_deployment
        self.chatgpt_model = chatgpt_model
        self.embedding_deployment = embedding_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field

    async def run(self, q: str, overrides: dict[str, Any]) -> dict[str, Any]:
        has_text = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        has_vector = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        use_semantic_captions = True if overrides.get("semantic_captions") and has_text else False
        top = overrides.get("top") or 3
        exclude_category = overrides.get("exclude_category") or None
        filter = "category ne '{}'".format(exclude_category.replace("'", "''")) if exclude_category else None

        # If retrieval mode includes vectors, compute an embedding for the query
        if has_vector:
            embedding = await self.openai_client.embeddings.create(
                model=self.embedding_deployment,
                input=q
            )
            query_vector = embedding.data[0].embedding
        else:
            query_vector = None

        # Only keep the text query if the retrieval mode uses text, otherwise drop it
        query_text = q if has_text else ""

        # Use semantic ranker if requested and if retrieval mode is text or hybrid (vectors + text)
        if overrides.get("semantic_ranker") and has_text:
            r = await self.search_client.search(search_text=query_text,
                                          filter=filter,
                                          query_type=QueryType.SEMANTIC,
                                          semantic_configuration_name="default",
                                          top=top,
                                          query_caption="extractive|highlight-false" if use_semantic_captions else None,
                                          vector_queries=[VectorizedQuery(vector=query_vector, k_nearest_neighbors=top, fields="embedding")] if query_vector else None)
        else:
            r = await self.search_client.search(search_text=query_text,
                                          filter=filter,
                                          top=top,
                                          vector_queries=[VectorizedQuery(vector=query_vector, k_nearest_neighbors=top, fields="embedding")] if query_vector else None)
        if use_semantic_captions:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(" . ".join([c.text for c in doc['@search.captions']])) async for doc in r]
        else:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(doc[self.content_field]) async for doc in r]
        content = "\n".join(results)

        message_builder = MessageBuilder(overrides.get("prompt_template") or self.system_chat_template, self.chatgpt_model)

        # add user question
        user_content = q + "\n" + f"Sources:\n {content}"
        message_builder.append_message('user', user_content)

        # Add shots/samples. This helps model to mimic response and make sure they match rules laid out in system message.
        message_builder.append_message('assistant', self.answer)
        message_builder.append_message('user', self.question)

        messages = message_builder.messages
        chat_coroutine = self.openai_client.chat.completions.create(
            model=self.openai_deployment if self.openai_deployment else self.chatgpt_model,
            messages=messages,
            temperature=overrides.get("temperature") or 0.3,
            max_tokens=1024,
            n=1
        )
        return {"data_points": results, "answer": (await chat_coroutine).choices[0].message.content, "thoughts": f"Question:<br>{query_text}<br><br>Prompt:<br>" + '\n\n'.join([str(message) for message in messages])}
