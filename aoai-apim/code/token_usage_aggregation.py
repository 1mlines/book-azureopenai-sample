import pandas as pd
import json
import argparse

# 응답 본문(response body)에서 토큰수, 사용자 이름, 모델 이름을 추출하는 함수
def extract_tokens_username_and_model(row):
    # 초기값 설정
    completion_tokens = float('nan')
    prompt_tokens = float('nan')
    preferred_username = float('nan')
    model_name = float('nan')
    
    # completion_tokens, prompt_tokens, model 추출
    try:
        json_data = json.loads(row['ResponseBody'])
        completion_tokens = json_data['usage']['completion_tokens']
        prompt_tokens = json_data['usage']['prompt_tokens']
        model_name = json_data['model']
    except Exception as e:
        pass

    # preferred_username 추출
    try:
        trace_records = json.loads(row['TraceRecords'])
        preferred_username = trace_records[0]['message']
    except Exception as e:
        pass

    return pd.Series([completion_tokens, prompt_tokens, preferred_username, model_name])


def main(input_file, output_file, endpoint):
    # CSV 파일 불러오기
    df = pd.read_csv(input_file, encoding='utf-8')

    # URL과 응답 코드로 필터링
    filtered_df = df[(df['Url'] == endpoint) & (df['ResponseCode'] == 200)]

    # 각 행마다 함수를 적용해서 새로운 열 추가
    filtered_df[['completion_tokens', 'prompt_tokens', 'preferred_username', 'model_name']] = filtered_df.apply(extract_tokens_username_and_model, axis=1)

    # 데이터를 집계해서 CSV 파일로 저장
    aggregation = filtered_df.groupby(['ApimSubscriptionId', 'preferred_username', 'model_name']) \
    .agg({
        'completion_tokens': 'sum', 
        'prompt_tokens': 'sum',
        'Url': 'count'
    }) \
    .rename(columns={'Url': 'api_call_count'})

    aggregation.to_csv(output_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="구독 키, 사용자, 모델, 지역별로 토큰수를 집계한 결과를 CSV 파일로 저장하는 프로그램")
    parser.add_argument("--input_file", type=str, required=True)
    parser.add_argument("--output_file", type=str, required=True)
    parser.add_argument("--endpoint", type=str, required=True)
    
    args = parser.parse_args()

    main(args.input_file, args.output_file, args.endpoint)
