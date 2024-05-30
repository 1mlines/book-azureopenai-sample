# book-azureopenai-sample

Azure OpenAI Service로 시작하는 ChatGPT/LLM 시스템 구축 입문의 예제 코드 저장소입니다.

원서 링크: https://gihyo.jp/book/2024/978-4-297-13929-2  

## 디렉토리 구성

- [aoai-rag](./aoai-rag/): Azure OpenAI Service와 Azure AI Search를 활용해 사내 문서 검색(RAG) 시스템을 구현하는 예제 코드입니다. 5장에서 주로 사용하며 6장에서 ChatGPT 플러그인을 구현할 때에도 사용합니다. 또, 각각의 컴포넌트들을 더 깊게 이해할 수 있도록 단계적으로 작성한 노트북을 제공합니다.([aoai-rag/notebooks](aoai-rag/notebooks))
- [aoai-flask-see](./aoai-flask-sse/): Azure OpenAI Service의 스트리밍 처리를 Flask와 SSE(Server-Sent Events)를 활용해서 구현하는 예제 코드입니다. 8장에서 사용합니다.
- [aoai-apim](./aoai-apim/): Azure API Management를 활용해서 Azure OpenAI Service를 사내 공통 시스템으로 사용하는 예제 코드입니다. 9장에서 사용합니다.


## 환경설정

예제 코드를 실행하려면 다음과 같은 환경이 필요합니다. 아래 내용을 참고하여 설정합니다.

1. Python 3.10 이상
2. Git
3. Azure Developer CLI
4. Node.js 18 이상
5. PowerShell 7 이상(pwsh) ※Windows 사용자 한정

### 1. Python 3.10.11 설치

[Python 3.10.11](https://www.python.org/ftp/python/3.10.11/python-3.10.11.exe)을 다운받아 실행합니다.

참고로 Linux（Ubuntu）나 macOS는 기본으로 파이썬이 설치되어 있어 별도의 설치 과정 없이도 사용할 수 있습니다. 단, 기본으로 설치된 파이썬은 오래된 버전인 경우가 있습니다. 이 책에서는 Python 3.10.11을 사용하므로 실행에 문제가 있으면 이 버전을 설치하는 것을 권장합니다.

### 2. Git 설치

[Git](https://git-scm.com/downloads) 홈페이지에서 자신의 운영체제를 클릭해서 설치를 진행합니다.

### 3. Azure Developer CLI 설치

Azure Developer CLI는 개발자용 도구로서 로컬 환경의 애플리케이션을 Azure 환경으로 이식하는 기능을 제공합니다.
아래에 기재된 설치 방법 및 트러블 슈팅 이외의 정보에 대해서 더 자세히 알고 싶다면 공식문서([azd](https://aka.ms/azd))를 참고 바랍니다.

#### Windows

Windows Package Manager（winget）[^1]가 사용가능한 경우에는 다음 커맨드를 실행합니다.

```powershell
winget install microsoft.azd
```

[^1]: winget은 Windows 10 1709(빌드 16299) 이후 버전 혹은 Windows 11에서 사용이 가능합니다.

#### Linux

다음 커맨드를 실행합니다.

```bash
curl -fsSL https://aka.ms/install-azd.sh | bash
```

#### macOS

Homebrew로 설치하는 것을 권장합니다.

```bash
brew tap azure/azd && brew install azd
```

### 4. Node.js 18 LTS 설치

[Node.js 18 LTS](https://nodejs.org/en/download)에서 LTS를 선택하고, 자신의 운영체제에 맞춰 설치를 진행합니다.

### 5. PowerShell 7 설치 (Windows 한정)

[PowerShell 7](https://github.com/PowerShell/PowerShell)에서 자신의 환경(x64 혹은 x86)에 맞는 PowerShell을 다운로드 받아 설치합니다. Download(LTS)열에서 .msi를 다운받습니다.
