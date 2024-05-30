import logging
from typing import Any, AsyncGenerator, Coroutine

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
)

from azure.search.documents.aio import SearchClient
from azure.search.documents.models import (
    QueryType,
    VectorizedQuery
)

from core.messagebuilder import MessageBuilder
from core.modelhelper import get_token_limit
from text import nonewlines

class ChatReadRetrieveReadApproach:
    """
    Azure AI Search(구 Azure Cognitive Search)와 OpenAI의 Python SDK를 사용한 retrieve-then-read 구현 예시다.
    이 예시는 우선 GPT로 검색 쿼리를 생성하여 검색 엔진에서 문서를 추출한다. 그리고 추출된 결과를 활용해 프롬프트를 구성하여 GPT로 보완된 응답을 생성한다.
    """

    # Chat roles
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

    # System prompt
    system_message_chat_conversation = """
너는 한국의 무신정권 역사에 관한 문제를 답변해주는 역사 교수야.
If you cannot guess the answer to a question from the SOURCE, answer "I don't know".
Answers must be in Korean.

# Restrictions
- The SOURCE prefix has a colon and actual information after the filename, and each fact used in the response must include the name of the source.
- To reference a source, use a square bracket. For example, [info1.pdf]. Do not combine sources, but list each source separately. For example, [info1.pdf][info2.pdf].

{follow_up_questions_prompt}
{injected_prompt}
"""
    # Follow-up question prompt
    follow_up_questions_prompt_content = """
답변에는 사용자의 질문에 대한 후속 질문을 3개 첨부해야 해. 후속 질문 규칙은 '제한사항'에 정의되어 있어.

- Please answer only questions related to the history of the Goryeo military regime in Korea. If the question is not related to the history of Goryeo military regime in Korea, answer "I don't know".
- Use double angle brackets to reference the questions, e.g. <<What did Kyong Tae-sung do? >>.
- Try not to repeat questions that have already been asked.
- Do not add SOURCES to follow-up questions.
- Do not use bulleted follow-up questions. Always enclose them in double angle brackets.
- Follow-up questions should be ideas that expand the user's curiosity.
- Only generate questions and do not generate any text before or after the questions, such as 'Next Questions'

EXAMPLE:###
Q:이순신에 대해서 알려줘.
A:이순신은 조선 시대의 유명한 장군으로, 조선 중기에 살았습니다. 그는 조선 역사상 가장 뛰어난 해군 지휘관 중 하나로 꼽히며, 일본의 침략에 맞서 싸웠습니다. 이순신은 1545년 경남 통영에서 태어났으며, 어려서부터 군사적 재능을 보였습니다. 조선 왕조의 해군을 이끌면서, 수많은 전쟁에서 승리를 거두었으며 특히, 한산도 대첩과 함포장 대첩은 그의 뛰어난 전술과 지휘력을 잘 보여주는 전투였습니다.[이순신-2.pdf][이순신-11.pdf]<<이순신이 해군 지휘관으로서 어떤 전술적 재능을 보였나요?>><<이순신이 명량 해전에서 어떤 전략을 펼쳤고, 그 전투에서 어떤 요소가 승리에 기여했나요?>><<이순신의 사후에 대해 논란이 있던데, 그의 사후에 대한 다양한 평가에는 어떤 것들이 있나요?>>

Q:한산도 대첩에 대해서 알려줘.
A:한산도 대첩은 1592년에 일어난 임진왜란 중에 조선 수군이 일본 수군을 대파한 해전입니다. 이 전투는 특히 조선과 일본 양국의 지휘관들의 전술과 지도력이 돋보인 사건으로 평가받고 있습니다. 이순신 장군은 조선 수군의 총사령관으로, 그의 지휘 하에 한산도 대첩에서 조선 수군은 일본 수군에게 압도적인 승리를 거두었습니다. 와키자카 야스하루는 이 전투에서 일본 수군의 주요 지휘관 중 한 명이었습니다. 그는 본래 성공적인 해전 경험을 가지고 있었지만, 한산도 대첩에서는 이순신의 전략에 효과적으로 대응하지 못했습니다. 와키자카의 수군은 조선의 강력한 해군 전력과 거북선에 의해 큰 손실을 입었습니다.[이순신-2.pdf][와키자카-11.pdf]<<이후 전쟁의 결과는 어떻게 됐나요?>><<이순신과 와키자카는 어떤 인물이었나요?>><<한산도 대첩 외에 유명한 전투는 어떤 것들이 있나요?>>
###
"""
    # Query generation prompt
    query_prompt_template = """
아래는 사용자들의 질문이야. 과거 대화 이력과 한국사 지식을 검색해서 응답해야해.
대화 이력과 질문에 기반해서 검색 쿼리를 생성해줘.
검색 쿼리에는 인용한 파일이나 문서명(info.txt 혹은 doc.pdf)을 포함시켜야해.
검색 쿼리에는 괄호([] 혹은 <<>>) 안에 있는 텍스트는 포함시키면 안돼.
검색 쿼리를 생성할 수 없으면 숫자 0만 응답해줘.
"""
    query_prompt_few_shots = [
        {'role' : USER, 'content' : '이순신은 어떤 인물이야?' },
        {'role' : ASSISTANT, 'content' : '이순신 인물 역사' },
        {'role' : USER, 'content' : '이순신의 공적에 대해서 알려줘.' },
        {'role' : ASSISTANT, 'content' : '이순신 인물 공적' }
    ]

    def __init__(self, search_client: SearchClient, openai_client: AsyncOpenAI, chatgpt_deployment: str, chatgpt_model: str, embedding_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.openai_client = openai_client
        self.chatgpt_deployment = chatgpt_deployment
        self.chatgpt_model = chatgpt_model
        self.embedding_deployment = embedding_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        self.chatgpt_token_limit = get_token_limit(chatgpt_model)

    async def run_until_final_call(self, history: list[dict[str, str]], overrides: dict[str, Any], should_stream: bool = False) -> tuple[dict[str, Any], Coroutine[Any, Any, AsyncStream[ChatCompletionChunk]]]:
        has_text = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        has_vector = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        use_semantic_captions = True if overrides.get("semantic_captions") and has_text else False
        top = overrides.get("top") or 3
        exclude_category = overrides.get("exclude_category") or None
        filter = "category ne '{}'".format(exclude_category.replace("'", "''")) if exclude_category else None
        
        # ===================================================================================
        # STEP 1: 최근 질문 및 채팅 이력을 기반으로 GPT에 최적화된 키워드 검색 쿼리를 생성한다.
        # ===================================================================================
        user_q = 'Generate search query for: ' + history[-1]["user"]
        messages = self.get_messages_from_history(
            self.query_prompt_template,
            self.chatgpt_model,
            history,
            user_q,
            self.query_prompt_few_shots,
            self.chatgpt_token_limit - len(user_q)
            )
        
        # ChatCompletion API로 검색 쿼리를 생성한다.
        chat_completion: ChatCompletion = await self.openai_client.chat.completions.create(
            messages=messages,
            model=self.chatgpt_deployment if self.chatgpt_deployment else self.chatgpt_model,
            temperature=0.0,
            max_tokens=100,
            n=1)

        query_text = chat_completion.choices[0].message.content
        if query_text.strip() == "0":
            query_text = history[-1]["user"] # 더 나은 쿼리를 생성하지 못하면 마지막에 입력된 쿼리를 사용한다.

        # ================================================================================
        # STEP 2: GPT로 생성한 쿼리를 사용해서 검색 인덱스로부터 관련 문서를 취득한다.
        # ================================================================================
        # 검색 모드에 벡터가 포함되어 있으면 쿼리를 임베딩한다.
        if has_vector:
            embedding = await self.openai_client.embeddings.create(
                model=self.embedding_deployment,
                input=query_text
            )
            query_vector = embedding.data[0].embedding
        else:
            query_vector = None

        # 검색 모드로 텍스트를 사용하면 텍스트 쿼리만 남기고 나머지는 삭제한다.
        if not has_text:
            query_text = None

        # 검색 모드로 텍스트나 하이브리드(벡터 + 텍스트)를 사용하면 요청에 따라 의미 체계 검색을 사용한다.
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
            results =[" SOURCE:" + doc[self.sourcepage_field] + ": " + nonewlines(" . ".join([c.text for c in doc['@search.captions']])) async for doc in r]
        else:
            results =[" SOURCE:" + doc[self.sourcepage_field] + ": " + nonewlines(doc[self.content_field]) async for doc in r]
        content = "\n".join(results) # 검색 결과

        # =============================================================================
        # STEP 3: 검색 결과와 채팅 이력을 사용해서 문맥이나 내용에 맞는 응답을 생성한다.
        # =============================================================================
        
        follow_up_questions_prompt = self.follow_up_questions_prompt_content if overrides.get("suggest_followup_questions") else ""
        # 프롬프트 템플릿 덮어쓰기
        # 클라이언트가 프롬프트 전체를 변경하거나, 접두사 '>>>'를 사용해서 기존 프롬프트에 주입할 수 있도록 한다.
        prompt_override = overrides.get("prompt_template")
        if prompt_override is None:
            system_message = self.system_message_chat_conversation.format(injected_prompt="", follow_up_questions_prompt=follow_up_questions_prompt)
        elif prompt_override.startswith(">>>"):
            system_message = self.system_message_chat_conversation.format(injected_prompt=prompt_override[3:] + "\n", follow_up_questions_prompt=follow_up_questions_prompt)
        else:
            system_message = prompt_override.format(follow_up_questions_prompt=follow_up_questions_prompt)

        print(system_message) # 합성된 시스템 프롬프트 확인
        
        messages = self.get_messages_from_history(
            system_message,
            self.chatgpt_model,
            history,
            history[-1]["user"]+ "\n\n " + content, # 모델은 시스템 메시지가 너무 길어지면 프롬프트를 제대로 처리하지 못한다. 후속 질문 프롬프트의 처리를 위해 사용자의 최근 대화로 소스를 이동한다.
            max_tokens=self.chatgpt_token_limit)
        msg_to_display = '\n\n'.join([str(message) for message in messages])

        extra_info = {"data_points": results, "thoughts": f"Searched for:<br>{query_text}<br><br>Conversations:<br>" + msg_to_display.replace('\n', '<br>')}
        
        # ChatCompletion 방식으로 응답을 생성한다.
        chat_coroutine = self.openai_client.chat.completions.create(
            model=self.chatgpt_deployment if self.chatgpt_deployment else self.chatgpt_model,
            messages=messages,
            temperature=overrides.get("temperature") or 0.0,
            max_tokens=1024,
            n=1,
            stream=should_stream
        )
        return (extra_info, chat_coroutine)

    async def run_without_streaming(self, history: list[dict[str, str]], overrides: dict[str, Any]) -> dict[str, Any]:
        extra_info, chat_coroutine = await self.run_until_final_call(history, overrides, should_stream=False)
        chat_content = (await chat_coroutine).choices[0].message.content
        extra_info["answer"] = chat_content
        return extra_info

    async def run_with_streaming(self, history: list[dict[str, str]], overrides: dict[str, Any]) -> AsyncGenerator[dict, None]:
        extra_info, chat_coroutine = await self.run_until_final_call(history, overrides, should_stream=True)
        yield {
            "choices": [
                {
                    "delta": {"role": self.ASSISTANT},
                    "context": extra_info,
                    "finish_reason": None,
                    "index": 0,
                }
            ],
            "object": "chat.completion.chunk",
        }
        async for event_chunk in await chat_coroutine:
            # "2023-07-01-preview" API version has a bug where first response has empty choices
            event = event_chunk.model_dump()  # Convert pydantic model to dict
            if event["choices"]:
                content = event["choices"][0]["delta"].get("content")
                content = content or ""  # content may either not exist in delta, or explicitly be None
                yield event

    def get_messages_from_history(self, system_prompt: str, model_id: str, history: list[dict[str, str]], user_conv: str, few_shots = [], max_tokens: int = 4096) -> list:
        message_builder = MessageBuilder(system_prompt, model_id)

        # 채팅으로 어떤 응답을 원하는지 예시를 추가한다. 채팅은 시스템 메시지의 규칙과 일치하는지 확인하며 어떤 응답이든 모방을 시도한다.
        for shot in few_shots:
            message_builder.append_message(shot.get('role'), shot.get('content'))

        user_content = user_conv
        append_index = len(few_shots) + 1

        message_builder.append_message(self.USER, user_content, index=append_index)

        for h in reversed(history[:-1]):
            if bot_msg := h.get("bot"):
                message_builder.append_message(self.ASSISTANT, bot_msg, index=append_index)
            if user_msg := h.get("user"):
                message_builder.append_message(self.USER, user_msg, index=append_index)
            if message_builder.token_length > max_tokens:
                break

        messages = message_builder.messages
        return messages
