
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

# RGF 프로젝트 최상위 폴더의 .env 파일을 불러온다.
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class OpenAIJSONClient:
    def __init__(self, model=None):
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

        self.model = model or os.getenv("OPENAI_MODEL")

        if not self.model:
            raise RuntimeError("OPENAI_MODEL이 설정되지 않았습니다.")

        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError(
                "openai 패키지가 설치되지 않았습니다. requirements.txt를 설치하세요."
            ) from e

        self.client = OpenAI()

    def parse(self, prompt: str, schema: type[BaseModel]):
        response = self.client.responses.parse(
            model=self.model,
            input=prompt,
            text_format=schema,
        )

        if response.output_parsed is None:
            raise ValueError(
                "모델 응답을 구조화 JSON으로 해석하지 못했습니다."
            )

        return response.output_parsed
