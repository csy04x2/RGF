import os
from pydantic import BaseModel
class OpenAIJSONClient:
    def __init__(self,model=None):
        if not os.getenv('OPENAI_API_KEY'): raise RuntimeError('OPENAI_API_KEY가 설정되지 않았습니다.')
        self.model=model or os.getenv('OPENAI_MODEL')
        if not self.model: raise RuntimeError('OPENAI_MODEL이 설정되지 않았습니다.')
        try:
            from openai import OpenAI
        except ImportError as e: raise RuntimeError('openai 패키지가 설치되지 않았습니다. requirements.txt를 설치하세요.') from e
        self.client=OpenAI()
    def parse(self,prompt:str,schema:type[BaseModel]):
        r=self.client.responses.parse(model=self.model,input=prompt,text_format=schema)
        if r.output_parsed is None: raise ValueError('모델 응답을 구조화 JSON으로 해석하지 못했습니다.')
        return r.output_parsed
