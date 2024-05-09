# Jupyter Notebook 예제

Azure OpenAI Service로 시작하는 ChatGPT/LLM 시스템 구축 입문의 Jupyter Notebook 예제다.

## 노트북 구성
### 핵심
- [00_DataIngest_AzureAISearch_PythonSDK.ipynb](./00_DataIngest_AzureAISearch_PythonSDK.ipynb): 노트북에 있는 콘텐츠들을 실행하기 위해 필요한 Azure AI Search의 검색 인덱스를 생성한다. 
- [01_AzureAISearch_PythonSDK.ipynb](./01_AzureAISearch_PythonSDK.ipynb): Azure AI Search의 키워드 검색, 벡터 검색, 시맨틱 하이브리드 검색을 사용한다.
- [02_RAG_AzureAISearch_PythonSDK.ipynb](./02_RAG_AzureAISearch_PythonSDK.ipynb): Azure AI Search로 RAG 아키텍처를 구현한다. 검색 쿼리 생성, 검색 결과 취득, 응답 생성의 세 단계로 나눠 실행한다.
- [03_ReAct_ToolSelection_LangChain.ipynb](./03_ReAct_ToolSelection_LangChain.ipynb): ReAct로 툴을 선택한다. 예제 코드에서는 2개의 툴(Azure AI Search, CSV 룩업 테이블)을 사용해서 정보를 검색한다.
- [04_ReAct_MusinCafeReservationPlugins_LangChain.ipynb](./04_ReAct_MusinCafeReservationPlugins_LangChain.ipynb): 무신 카페 검색 & 예약 플러그인 예제다. 두 가지 시스템을 ChatGPT 플러그인으로 공개하고, 이를 오케스트레이터인 LangChain에서 호출한다.
- [05_AzureAISearch_LangChain.ipynb](./05_AzureAISearch_LangChain.ipynb): LangChain으로 Azure AI Search의 검색 쿼리를 사용한다.

### 기초
- [01_AzureOpenAI_completion.ipynb](./basic/01_AzureOpenAI_completion.ipynb): Azure OpenAI의 Completion API를 활용하여 여러 작업을 수행한다.
- [02_AzureOpenAI_chatcompletion.ipynb](./basic/02_AzureOpenAI_chatcompletion.ipynb): Azure OpenAI Chat Completion API의 기본적인 기능들을 사용해보는 예제다.
- [03_AzureOpenAI_functioncalling.ipynb](./basic/03_AzureOpenAI_functioncalling.ipynb): Azure OpenAI의 Function Calling(함수 호출) 기능을 사용해보는 예제다.
- [04_AzureOpenAI_embeddings.ipynb](./basic/04_AzureOpenAI_embeddings.ipynb): Azure OpenAI Embeddings API의 기본적인 기능들을 사용해보는 예제다.
- [05_SemanticKernel.ipynb](./basic/05_SemanticKernel.ipynb): SemanticKernel의 기본적인 기능들을 사용해보는 예제다.
- [06_AzureAIDocumentIntelligence.ipynb](./basic/06_AzureAIDocumentIntelligence.ipynb): Azure AI Document Intelligence로 PDF에서 정보를 추출하는 예제다.

## 환경설정

예제 코드를 실행하려면 다음과 같은 환경이 필요하다. 아래 내용을 참고하여 설정한다.

### 1. Python 3.10.11 설치

[Python 3.10.11](https://www.python.org/ftp/python/3.10.11/python-3.10.11.exe)을 다운받아 실행한다.

참고로 Linux（Ubuntu）나 macOS는 기본으로 파이썬이 설치되어 있어 별도의 설치 과정 없이도 사용할 수 있다. 단, 기본으로 설치된 파이썬은 오래된 버전인 경우가 있다. 이 책에서는 Python 3.10.11을 사용하므로 실행에 문제가 있으면 이 버전을 설치하는 것을 권장한다.

### 2. Jupyter Notebook 설치

CMD 혹은 터미널에서 다음 커맨드를 입력하여 Jupyter Notebook을 설치한다.

```bash
pip install notebook
```

설치가 완료되면 Jupyter Notebook을 실행하는 아래 커맨드를 입력한다.

```bash
jupyter notebook
```

여기까지 진행하면 기본 브라우저에서 Jupyter UI가 나타나야 한다.

## 라이센스
라이센스는 [MIT 라이센스](../LICENSE.md)를 따른다.