# Azure OpenAI common foundation with Azure API Management

Azure OpenAI의 공통 시스템을 자동으로 구축하는 예제 코드입니다.

<img width="800" src=".\assets\architecture.png">

조직 전체의 거버넌스를 확립한 뒤 Azure OpenAI의 이용을 촉진시키려면 다음 요건들을 충족하는 공통 기반을 마련하고, 사용자에게 공개해야 합니다.  

| No | 항목 | 요건 |
|:-:|:-----|:-|
| 1 | 인증•인가 | Microsoft Entra ID(구 Azure Active Directory)를 활용한 인증방식으로 통일하여 인가받은 앱이나 사용자에게만 Azure OpenAI의 사용을 허용한다 |
| 2 | 과금 | Azure OpenAI 이용료를 부서별 혹은 이용자별로 과금되도록 만든다 |
| 3 | 호출 제한 | 특정 부서나 팀이 할당량 제한을 전부 소모하지 않도록 부서나 이용자 단위로 요청수를 제한한다 |
| 4 | 로그 통합 | Azure OpenAI 이용시에 사용한 프롬프트나 생성된 출력 결과를 한 곳에 통합한다 |
| 5 | 폐쇄망 사용 | 레이어드 시큐리티의 관점에서 프라이빗 네트워크에 폐쇄된 형태로 Azure OpenAI를 이용할 수 있게 만든다 |
| 6 | 부하분산 | Azure OpenAI는 동일한 구독이나 리전에서 처리 가능한 TPM(토큰/분)을 제한하고 있으며, 할당량 제한 증가 신청에는 다소 시간이 걸릴 수 있다. 보다 신속하게 TPM 제한에 대응하려면 여러 리전으로의 부하분산을 통해 사용 가능한 TPM을 증가시키는 방법도 있다 |

이 예제 코드에서는 아래 요건을 충족하는 아키텍처를 자동화하여 구축합니다.

# 사전 설정

1. Microsoft Entra ID에 애플리케이션 등록
    * Azure OpenAI API를 호출할 애플리케이션을 Microsoft Entra ID에 등록합니다. 이 작업에는 Microsoft Entra ID의 애플리케이션을 관리할 수 있는 권한이 필요합니다. 아래 Microsoft Entra ID 역할들은 필요한 권한을 가지고 있습니다.
        * 애플리케이션 관리자
        * 애플리케이션 개발자
        * 클라우드 애플리케이션 관리자
    * 다음 절차대로 애플리케이션을 등록합니다.
        1. [Azure portal](https://portal.azure.com/)에서 [앱 등록]을 검색하여 선택
        2. [새 등록]을 선택
        3. [애플리케이션 등록] 페이지가 나타나면, 다음과 같이 애플리케이션 등록정보를 입력한다
            * [이름]: 임의의 애플리케이션 이름을 입력합니다. 특별히 원하는 이름이 없으면 common-openai-api라고 지정합니다.
            * [지원되는 계정 유형]: 상황에 맞는 옵션을 선택하면 됩니다. 특별히 원하는 옵션이 없으면 [이 조직 디렉터리의 계정만(기본 디렉터리만 - 단일 테넌트)]를 선택합니다.
            * [리디렉션 URI]: 리다이렉트시키고 싶은 애플리케이션 URI가 있으면 입력합니다. 이후에 살펴볼 아키텍처 해설에서는 예제 파이썬 코드를 사용해서 실제로 Azure OpenAI API를 호출합니다. 예제 파이썬 코드를 사용하실 분은 플랫폼 선택에서 웹을 선택하고 URI에 http://localhost:5000/callback을 입력합니다. 리디렉션 URI는 이후에 사용하므로 메모해두어야 합니다.
            <img width="600" src=".\assets\regist-aoai-app.png">
        4. [등록]을 클릭해서 애플리케이션 생성
            * 앱의 [개요] 페이지에 표시된 [애플리케이션 ID]를 메모해 둡니다.
            <img width="600" src=".\assets\application-id.png">
        5. Microsoft Entra ID 메뉴의 [관리] 섹션에서 [앱 등록]을 선택하고 [모든 애플리케이션] 탭에서 방금 생성한 애플리케이션으로 들어갑니다. 그리고 [관리] 섹션에 있는 [API 표시]를 선택한 뒤 [범위 추가] 버튼을 클릭합니다.
        6. [애플리케이션 ID URI]값은 변경하지 않고 [저장 후 계속]버튼을 선택합니다.
            * [범위 이름]에는 API로 보호중인 데이터와 기능에 대한 접근을 제한하기 위한 범위를 지정합니다. 여기서는 'chat'을 지정합니다.
            <img width="300" src=".\assets\add-scope.png">
            * [동의할 수 있는 사람]에는 사용자도 동의할 수 있도록 [관리자 및 사용자]를 선택합니다.
            * 관리자나 사용자의 동의 표시 이름과 설명에는 임의의 값을 지정하면 됩니다.
            * [상태]는 '사용'으로 지정한다.
        7. [범위 추가] 버튼을 클릭해서 범위를 생성합니다.
            * 추가된 범위값(예: api://<애플리케이션 ID>/chat)은 이후에 사용하므로 메모해둡니다. 우측에 복사 버튼으로 복사할 수 있습니다.
            <img width="600" src=".\assets\copy-scope.png">

2. 배포할 사용자에 권한 부여하기
    * 배포할 사용자의 Microsoft Entra ID 계정에 배포할 구독의 Owner(소유자) 권한을 부여해야 합니다.

# 배포

1. 예제 코드 다운로드
    * 예제 코드를 아직 다운받지 않았다면 git clone으로 다운로드한 뒤 아래 디렉터리로 이동해주세요. 예제 코드의 라이센스는 MIT License입니다. PowerShell이나 Bash/Zsh을 열고 다음 커맨드를 실행합니다.
        ```
        git clone -b https://github.com/1mlines/book-azureopenai-sample.git
        cd book-azureopenai-sample/aoai-apim
        ```
2. 파라미터 설정
    * 배포에 필요한 모든 파라미터는 aoai-apim/infra/main.parameters.json에 있습니다. main.parameters.json의 내용을 다음 표를 보면서 수정해주세요.   

| 파라미터 이름 | 입력값 | 입력값 예시 |
|:-|:-|:-|
| environmentName | 배포시 미지정 |  |
| location | 배포시 미지정 |  |
| aoaiFirstLocation | Azure OpenAI 모델을 배포할 첫 번째 리전 | japaneast 등 |
| aoaiSecondLocation | Azure OpenAI 모델을 배포할 두 번째 리전 | eastus 등 |
| corsOriginUrl | 인증할 싱글 페이지 애플리케이션(SPA)의 도메인을 지정한다. 도메인이 정해져있지 않으면, 기본값으로 '*'를 지정할 수도 있다. 하지만 확정되는대로 실제 도메인을 지정하는 것을 권장한다. | *, example.com, yourapp.azurewebsites.net 등 |
| audienceAppId | 등록한 앱의 개요에 기재된 [애플리케이션(클라이언트) ID] | bcd1234-abcd-1234-abcd-1234abcd1234 |
| scopeName | 범위 이름 | chat |
| tenantId | Microsoft Entra ID 개요에 기재된 [테넌트 ID] | abcd1234-abcd-1234-abcd-1234abcd1234 |
| aoaiCapacity | 배포할 모델의 TPM(토큰/분) 제한을 지정한다. 여기에 지정한 수치에 1,000이 곱해진다(10으로 지정하면 1분당 10,000 토큰까지 처리할 수 있음을 의미한다) | 1, 10, 100 등 |

3. Azure Developer CLI 로그인
    * 다음 커맨드를 사용해서 배포할 구독에 포함된 Microsoft Entra ID 테넌트로 로그인합니다.
        ```
        azd auth login
        ```
    * 브라우저가 없는 환경에서는 --use-device-code, 테넌트를 명시적으로 지정하고 싶을 때는 --tenant-id를 추가로 지정해야 합니다.

4. 배포 실행
    * 다음 커맨드를 실행합니다.
        ```
        azd up
        ```
    * 질문이 나오면 다음과 같이 내용을 설정합니다.
        * 환경 이름(Enter a new environment name): 임의의 환경 이름을 입력합니다. rg-<환경 이름>으로 리소스 그룹이 생성됩니다.
        * 구독 선택(Select an Azure Subscription to use): 리소스 그룹을 생성할 구독을 선택합니다.
        * 위치 선택(Select an Azure location to use): Japan East 등 Azure OpenAI 이외의 Azure 서비스를 배포할 리전을 지정합니다.
    * 배포 완료까지는 20~30분 가량이 소요될 수 있습니다. 지정한 환경 이름 등은 .azure 디렉터리 하위에 저장되므로 매번 재지정하지 않아도 됩니다. 환경을 처음부터 재정의하고 싶다면 .azure 디렉터리를 삭제해야 합니다.