# ChatGPT + Enterprise data with Azure OpenAI and Azure AI Search

## Table of Contents

- [기능](#기능)
- [시작하며](#시작하며)
- [Azure에 배포하기](#Azure에-배포하기)
  - [비용 추정](#비용-추정)
  - [전제 조건](#전제-조건)
    - [로컬 환경에서 실행하기](#로컬-환경에서-실행하기)
    - [GitHub Codespaces 혹은 VS Code Remote Containers로 실행하기](#Github-Codespaces-혹은-VS-Code-Remote-Containers로-실행하기)
  - [새로 배포하기](#새로-배포하기)
  - [기존 리소스에 배포하기](#기존-리소스에-배포하기)
  - [재배포](#재배포)
- [환경 공유하기](#환경-공유하기)
- [로컬에서 실행하기](#로컬에서-실행하기)
- [웹앱 사용하기](#웹앱-사용하기)
- [옵션 기능 활성화](#옵션-기능-활성화)
  - [Application Insights 활성화](#application-insights-활성화)
  - [인증 기능 설정](#인증-기능-설정)
- [리소스](#리소스)
  - [FAQ](#faq)
  - [트러블 슈팅](#트러블-슈팅)


> [!IMPORTANT]
> 2024년 4월 2일부터는 오래된 버전의 Azure OpenAI Service API는 사용할 수 없습니다. 최신 GA API 버전인 `2024-02-01`나 `2024-03-01-preview`를 사용해주세요([Docs](https://learn.microsoft.com//azure/ai-services/openai/api-version-deprecation)).

이 예제에서는 자체 데이터에 Retrieval Augmented Generation(RAG) 패턴을 사용해서 ChatGPT와 유사한 경험을 하도록 만드는 방법들을 다룹니다. Azure OpenAI Service로 ChatGPT 모델(gpt-35-turbo)에 액세스하며, 데이터 인덱싱 및 검색에는 Azure AI Search를 사용합니다.

저장소에는 샘플 데이터가 포함되어 있어 바로 E2E로 실행할 수 있습니다. 예제 애플리케이션에는 고려 무신정권의 무신들에 관한 위키피디아 데이터가 있어서 무신정권이나 무신들에 대해 질문해볼 수 있습니다.

![RAG Architecture](docs/appcomponents.png)

## 기능

* 채팅 및 Q&A 인터페이스
* 인용, 소스 콘텐츠 추적 등 사용자가 답변의 신뢰성을 평가하기 위한 다양한 옵션 고려
* 데이터 준비, 프롬프트 작성, 모델(ChatGPT)과 Retriever(Azure AI Search) 연동 방법 보여주기 
* UI 설정으로 동작 조정 및 옵션 테스트
* 옵션: Application Insights를 활용한 성능 추적 및 모니터링

![Chat screen](docs/chatscreen.png)

## 시작하며

> **중요:** 이 예제를 배포하고 실행하려면 **Azure OpenAI Service를 사용할 수 있는** Azure 구독이 필요합니다. [여기](https://aka.ms/oaiapply)에서 사용 승인 요청을 보낼 수 있습니다. 또, [여기](https://azure.microsoft.com/free/cognitive-search/)에서는 무료 Azure 크레딧을 취득할 수 있습니다.

## Azure에 배포하기 

### 비용 추정

가격은 리전이나 서비스의 과금 방식에 따라 달라지기 때문에 정확한 예측이 어렵습니다. 대략적인 가격을 계산해보려면 [Azure 가격 계산기](https://azure.com/e/8ffbe5b1919c4c72aed89b022294df76)를 사용하세요.

- Azure App Service: Basic Tier, 1CPU 코어, 1.75GB RAM. 1시간당 [가격](https://azure.microsoft.com/pricing/details/app-service/linux/)
- Azure OpenAI: Standard Tier, ChatGPT, Ada 모델. 사용된 토큰 1,000개당 가격이 책정되며 질문당 최소 1K의 토큰을 사용합니다. [가격](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/)
- Form Recognizer: S0(Standard) Tier는 사전에 구축된 레이아웃을 사용합니다. 문서당 과금되는 구조입니다. [가격](https://azure.microsoft.com/pricing/details/form-recognizer/)
- Azure AI Search: Basic Tier, 1개의 복제본, 의미 체계 검색은 월 1,000개까지 무료. 1시간당 [가격](https://azure.microsoft.com/pricing/details/search/)
- Azure Blob Storage: Standard Tier LRS(지역 다중화). 스토리지 및 읽기 작업 당 과금。[가격](https://azure.microsoft.com/pricing/details/storage/blobs/)
- Azure Monitor: 종량제 과금. 비용은 수집된 데이터에 기반하여 책정됩니다. [가격](https://azure.microsoft.com/pricing/details/monitor/)

비용 절감을 위해 `infra` 폴더 하위에 있는 매개 변수 파일을 변경하면 Azure App Service, Azure AI Search, Form Recognizer를 무료 SKU로 변경할 수 있습니다. 무료 AI Search 리소스는 구독당 1개까지만 사용할 수 있으며, 무료 Form Recognizer 리소스는 각 문서에서 처음 두 페이지만 분석합니다. 또, `data` 폴더의 문서수를 줄이거나 `prepdocs.py` 스크립트를 실행하는 `azure.yaml`의 postprovision 훅을 제거하면 Form Recognizer 비용을 줄일 수 있습니다.

⚠️ 더 이상 앱을 사용하지 않으면 불필요한 비용을 지출하지 않기 위해 잊지 말고 앱을 삭제해주세요. 애저 포탈에서 리소스 그룹을 삭제하거나, `azd down`을 실행하면 됩니다.

### 전제 조건

#### 로컬 환경에서 실행하기

* [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
* [Python 3.10+](https://www.python.org/downloads/)
  * **중요**: 설치 스크립트를 실행하려면 Windows의 경로에 Python과 pip 패키지 매니저가 포함되어 있어야 합니다. 파이썬을 Microsoft Store를 통해 설치하면 제대로 실행되지 않을 수 있습니다. 파이썬 공식 사이트에서 인스톨러를 다운받아 직접 설치해주세요.
  * **중요**: 콘솔에서 `python --version`을 실행할 수 있는지 확인해야 합니다. Ubuntu에는 `python`을 `python3`로 링크하기 위해 `sudo apt install python-is-python3`을 실행해야 합니다.
* [Node.js 18+](https://nodejs.org/en/download/)
* [Git](https://git-scm.com/downloads)
* [Powershell 7+ (pwsh)](https://github.com/powershell/powershell) - Windows 사용자 한정.
  * **중요**: PowerShell에서 `pwsh.exe`를 실행할 수 있는지 확인해야 합니다. 실패하면 PowerShell을 업그레이드 해야 합니다.

>NOTE: Azure 계정에는 [User Access Administrator](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#user-access-administrator) 혹은 [Owner](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#owner) 등의 `Microsoft.Authorization/roleAssignments/write` 권한이 필요합니다.

#### GitHub Codespaces 혹은 VS Code Remote Containers로 실행하기

GitHub Codespaces 혹은 VS Code Remote Containers를 사용하면 이 저장소를 가상화해서 실행할 수 있습니다. 아래 버튼 중 하나를 클릭하고 옵션 중 하나를 선택하여 저장소를 열어주세요.

- 지금은 점검중입니다.

### 새로 배포하기

기존 서비스를 활용하지 않고 새로 배포하려면 아래와 같이 커맨드를 실행합니다.

1. `azd up` 실행 - `./data` 폴더에 있는 파일을 기반으로 검색 인덱스를 구축하는 등 Azure 리소스를 프로비저닝하고 리소스에 예제를 배포합니다.
    * 주요 리소스의 위치와 OpenAI 리소스의 위치는 [모델 요약 테이블 및 지역 가용성](https://learn.microsoft.com/azure/cognitive-services/openai/concepts/models#model-summary-table-and-region-availability)을 기반으로 하며 가용성이 변경되면 레거시가 될 수 있습니다.
    * MacOS에서는 `azd up`를 실행하기 전에 `./scripts/prepdocs.sh`에 실행 권한을 부여해야 합니다. 예: `chmod 755 ./scripts/prepdocs.sh`
2. 애플리케이션이 정상적으로 배포되면 터미널에 URL이 나타납니다. 이 URL을 클릭하여 브라우저에서 애플리케이션을 사용해주세요.

URL은 다음과 같이 나타납니다.

!['Output from running azd up'](assets/endpoint.png)

> NOTE: 애플리케이션이 완전히 배포될 때까지 1분 정도 걸릴 수 있습니다. "Python Developer" 시작 화면이 표시되면 잠시 기다린 후 페이지를 새로고침 해주세요.

## 기존 리소스에 배포하기
기존 리소스에 이미 배포되어 있는 경우 아래 환경변수에 값을 설정하고 `azd up`을 실행합니다.
1. Run `azd env set AZURE_OPENAI_SERVICE {기존 OpenAI 서비스 이름}`
2. Run `azd env set AZURE_OPENAI_RESOURCE_GROUP {OpenAI 서비스가 프로비저닝되는 기존 리소스 그룹 이름}`
3. Run `azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT {기존 ChatGPT 배포 이름}`. 배포된 ChatGPT 모델의 기본값이 'chat'이 아닐 때 필요합니다.
4. Run `azd env set AZURE_OPENAI_EMB_DEPLOYMENT {기존 GPT Emeddings 배포 이름}`. 배포된 embeddings 모델의 기본값이 'embedding'이 아닐 때 필요합니다.
5. Run `azd up` - 이 커맨드를 실행하면 나머지 애저 리소스가 프로비저닝되어 `./data` 폴더에 있는 파일을 기반으로 검색 인덱스를 구축하는 등 리소스에 예제를 배포합니다.

> NOTE: 기존 Search Account나 Storage Account를 사용할 수도 있습니다. 기존 리소스 설정을 위해 `azd env set`에 사용할 수 있는 환경변수 목록은 `./infra/main.parameters.json`을 참고해주세요.

### 재배포

`app` 폴더 내부의 백엔드/프런트엔드 코드만 수정한 경우에는 Azure 리소스를 다시 프로비저닝할 필요는 없습니다. 앱만 배포할 경우에는 아래 커맨드를 실행합니다.

```azd deploy```

인프라 파일(`infra` 폴더 혹은 `azure.yaml`)을 수정한 경우에는 애저 리소스를 다시 프로비저닝 해야 합니다. 아래 커맨드를 실행합니다.

```azd up```

## 환경 공유하기

배포 완료된 기존 환경에 다른 사람이 접근할 수 있게 하려면 다음 절차를 따라주세요: 

1. [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) 설치
2. `azd init -t azure-search-openai-demo`를 실행하거나 저장소를 클론합니다.
3. `azd env refresh -e {environment name}`를 실행합니다. azd 환경 이름, 구독 ID, 지역이 필요합니다. 이 값들은 `.azure/{env name}/.env` 파일에 있습니다. 이것으로 앱을 로컬에서 실행하기 위해 필요한 모든 설정이 azd 환경의 `.env` 파일에 채워집니다.
4. `.env` 파일 혹은 active shell에서 환경 변수 `AZURE_PRINCIPAL_ID`를 Azure ID로 설정합니다. 이 값은 `az ad signed-in-user show`로 얻을 수 있습니다.
5. `./scripts/roles.ps1` 혹은 `.scripts/roles.sh`를 실행하여 필요한 모든 역할을 사용자에 할당합니다. 사용자가 구독에서 역할을 생성하는 데 필요한 권한이 없는 경우에는, 해당 사용자가 이 스크립트를 실행해야 할 수도 있습니다. 스크립트가 실행되면 로컬에서 앱을 실행할 수 있습니다.

## 로컬에서 실행하기

`azd up` 커맨드 실행이 성공한 후에 로컬에서 실행이 가능합니다.  

1. `azd auth login` 실행
2. `cd app`을 입력하여 app 디렉토리로 이동
3. `./start.ps1` 혹은 `./start.sh`를 실행하거나 "VS Code Task： Start App "를 실행하여 프로젝트를 로컬에서 시작

## 웹앱 사용하기

* 애저에서 사용： azd 커맨드로 배포된 애저 웹앱으로 이동합니다. URL은 azd 커맨드 완료시에 출력되거나("Endpoint"로 출력) 애저 포탈에서 찾을 수 있습니다.
* 로컬 실행: `http://127.0.0.1:50505`을 브라우저에서 열기

웹앱에 접속하면:

* 채팅 혹은 문답으로 다양한 주제를 경험해보세요. 채팅으로 후속 질문이나 보다 명확한 설명을 요청할 수 있습니다. 또, 답변 요약을 부탁하거나 보다 자세한 설명을 요청해보세요.
* 인용 및 출처를 탐색할 수 있습니다.
* '설정'을 클릭해서 다양한 옵션을 활용하고 프롬프트를 조정할 수 있습니다.

## 옵션 기능 활성화

### Application Insights 활성화

Application Insights와 요청 추적, 에러 로그를 활성화하려면 `azd up`를 실행하기 전에 `AZURE_USE_APPLICATION_INSIGHTS` 변수를 true로 설정해야 합니다.

1. `azd env set AZURE_USE_APPLICATION_INSIGHTS true`를 실행
2. `azd up`를 실행

성능 데이터를 확인하려면 리소스 그룹의 Application Insights 리소스로 이동해서 "Investigate -> Performance" 블레이드를 클릭한 뒤 임의의 HTTP 요청으로 이동하여 타이밍 데이터를 확인합니다.
채팅 요청 성능을 검사하려면 "Drill into Samples" 버튼으로 임의의 채팅 요청에 사용된 모든 API 호출의 E2E 추적을 확인할 수 있습니다:

![Tracing screenshot](docs/transaction-tracing.png)

예외나 서버 에러를 확인하려면 "Investigate -> Failures" 블레이드로 이동한 뒤 필터링 툴을 사용해서 특정 예외를 찾을 수 있습니다. 우측에는 파이썬의 스택 트레이스가 나타납니다.

### 인증 기능 설정

배포된 애저 웹앱은 기본적으로 인증이나 접근제한이 활성화되어 있지 않아서 웹앱에 라우팅 가능한 네트워크 접근 권한만 있으면 누구라도 인덱싱된 데이터와 채팅을 할 수 있습니다.[빠른 시작: Azure 앱 Service에서 실행되는 웹앱에 앱 인증 추가](https://learn.microsoft.com/azure/app-service/scenario-secure-app-authentication-app-service) 튜토리얼에 따라 Microsoft Entra에 인증을 요청하여 배포된 웹앱에 이를 사용할 수 있습니다.

그리고 특정 사용자 혹은 그룹의 접근을 제한하려면, [Microsoft Entra 앱을 Microsoft Entra 테넌트에서 사용자 세트로 제한](https://learn.microsoft.com/azure/active-directory/develop/howto-restrict-your-app-to-a-set-of-users)의 절차에 따라 Enterprise Application 하위의 "Assignment Required?" 옵션을 변경하여 사용자/그룹에 접근 권한을 설정합니다. 명시적인 접근 권한이 없는 사용자에게는 "AADSTS50105: Your administrator has configured the application <app_name> to block users unless they are specifically granted ('assigned') access to the application."이라는 에러 메시지가 나타납니다.

## 리소스

* [Revolutionize your Enterprise Data with ChatGPT: Next-gen Apps w/ Azure OpenAI and AI Search](https://aka.ms/entgptsearchblog)
* [Azure AI Search](https://learn.microsoft.com/azure/search/search-what-is-azure-search)
* [Azure OpenAI Service](https://learn.microsoft.com/azure/cognitive-services/openai/overview)

### FAQ

<details>
<summary>Azure AI Search는 방대한 문서를 검색할 수 있는데도 왜 PDF를 청크로 분할하나요?</summary>

청크를 분할하면 OpenAI에 보내는 정보량을 줄여서 토큰 제한에 걸리지 않을 수 있기 때문입니다. 콘텐츠를 분할해두면 토큰 제한에 걸리지 않고 OpenAI에 보낼 수 있는 텍스트를 쉽게 찾을 수 있습니다. Azure AI Search는 한 청크가 끝나면 다음 청크가 시작하는 텍스트 슬라이딩 윈도우 방식으로 청크를 분할합니다. 이 방법을 사용하면 텍스트의 콘텍스트가 손상될 위험을 줄일 수 있습니다.

</details>

<details>
<summary>전부 재배포하지 않고 추가로 PDF 파일을 업로드할 수 있는 방법이 있나요?</summary>

추가로 PDF 파일을 업로드하려면 추가 파일을 `data/` 폴더에 넣고 `./scripts/prepdocs.sh` 혹은 `./scripts/prepdocs.ps1`를 실행하면 됩니다. 기존 문서를 재업로드 하지 않으려면 기존 문서들은 data 폴더 밖으로 이동시켜야 합니다. 이전에 업로드한 문서를 체크하는 기능을 구현해도 됩니다.
</details>

<details>
<summary>이 예제는 다른 Chat with Your Data 예제와 어떤 점이 다른가요?</summary>

이 예제는 아래 저장소를 기반으로 만들어졌습니다:
https://github.com/Microsoft/sample-app-aoai-chatGPT/

위 저장소는 Azure OpenAI Studio와 Azure Portal을 사용해서 설정하도록 설계되어 있습니다. 또, 완전히 처음부터 배포하고 싶은 분들을 위해 `azd` 지원도 포함되어 있습니다.

주요 차이점

* 이 저장소에는 (Azure OpenAI와 Azure AI Search의) 여러 API 호출 결과를 다양한 방식으로 활용하는 RAG(검색 증강 생성) 예제가 포함되어 있습니다. 다른 저장소에서는 ChatCompletions API의 내장 데이터 소스 옵션만 사용해서 지정된 Azure AI Search 인덱스로 RAG를 구현합니다. 이 방식으로도 대부분 잘 동작하지만, 보다 유연한 접근이 필요하면 이 저장소의 방식이 더 적합할 수 있습니다.
* 이 저장소는 다른 저장소처럼 Azure OpenAI Studio와 연동되어 있지 않기 때문에 보다 실험적인 방식을 사용합니다.
</details>

<details>
<summary>이 예제에서 GPT-4를 사용하려면 어떻게 하나요?</summary>

`infra/main.bicep`의 `chatGptModelName`를 'gpt-35-turbo'에서 'gpt-4'로 변경하면 됩니다. 단, 계정에 허용된 TPM 용량을 조정해야 할 수도 있습니다.
</details>


### 트러블 슈팅

자주 발생하는 문제와 이에 대한 해결 방법을 정리했습니다.

1. 구독(`AZURE_SUBSCRIPTION_ID`)이 Azure OpenAI Service에 접근할 수 없습니다.
`AZURE_SUBSCRIPTION_ID`가 [OpenAI 접근 요청](https://aka.ms/oai/access)에서 지정한 ID와 일치하는지 확인해주세요.

2. Azure OpenAI를 사용할 수 없는 리전(East US가 아닌 East US 2 등)에서 리소스를 생성하고 싶은데 모델을 사용할 수 없습니다.
[Azure OpenAI Service 모델](https://aka.ms/oai/models)을 참고해주세요.

3. 서비스 할당량(리전별 리소스 수)이 초과된 상태입니다.
서비스 할당량 및 제한을 다룬 [문서](https://learn.microsoft.com/ko-kr/azure/ai-services/openai/quotas-limits)를 참고해주세요.

4. "하위 도메인 이름이 이미 사용중입니다. 다른 이름을 선택하세요."라는 오류가 발생합니다. 매번 예제를 실행하고나서 리소스를 삭제했는데 계속 같은 오류가 발생합니다.
애저는 리소스를 삭제하면 48시간 동안 같은 이름으로 다른 리소스를 만들 수 없습니다. [삭제된 리소스 제거](https://learn.microsoft.com/azure/cognitive-services/manage-resources?tabs=azure-portal#purge-a-deleted-resource)를 참고해주세요.

5. `prepdocs.py` 스크립트를 실행하면 `CERTIFICATE_VERIFY_FAILED` 오류가 발생합니다.
이 오류는 일반적으로 SSL 인증서에 문제가 있을 때 발생합니다. 이 [StackOverflow 답변](https://stackoverflow.com/questions/35569042/ssl-certificate-verify-failed-with-python3/43855394#43855394)을 참고하여 해결해주세요.

6. `azd up`를 실행하고 웹 사이트에 접속했는데 브라우저에 '404 Not Found'가 나타납니다. 
아직 설정이 끝나지 않았을 수도 있기 때문에 10분 정도 기다린 뒤 다시 접속해주세요. 그리고 `azd deploy`를 실행한 뒤 다시 기다려주세요. 이렇게 해도 배포한 앱에 오류가 발생하면 [Tips for Debugging App Service app deployments](http://blog.pamelafox.org/2023/06/tips-for-debugging-flask-deployments-to.html)를 참고해주세요. 이 문서를 참고했는데도 문제가 해결되지 않으면 이슈를 남겨주세요.

## 감사의 말
이 예제는 [Azure-Samples/azure-search-openai-demo](https://github.com/Azure-Samples/azure-search-openai-demo)를 기반으로 만들어졌습니다.