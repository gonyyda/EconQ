from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

response = client.responses.create(
    model="gpt-5",
    input="한국의 기준금리가 경제에 미치는 영향을 한 문장으로 설명해줘."
)

print(response.output_text)