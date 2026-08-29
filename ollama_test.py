import requests

def call_ollama_generate(prompt, model="gemma4"):
    """
    Ollama의 /api/generate 엔드포인트를 호출하여 텍스트를 생성합니다.
    """
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False # True로 설정하면 스트리밍 방식으로 응답을 받습니다.
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # HTTP 에러 발생 시 예외 처리
        
        result = response.json()
        return result.get("response", "")
        
    except requests.exceptions.RequestException as e:
        print(f"Ollama 호출 중 에러가 발생했습니다: {e}")
        return None

def call_ollama_chat(messages, model="gemma4"):
    """
    Ollama의 /api/chat 엔드포인트를 호출하여 채팅 형식으로 텍스트를 생성합니다.
    """
    url = "http://localhost:11434/api/chat"
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result.get("message", {}).get("content", "")
        
    except requests.exceptions.RequestException as e:
        print(f"Ollama 호출 중 에러가 발생했습니다: {e}")
        return None

if __name__ == "__main__":
    # 로컬에 설치된 Ollama 모델명으로 변경해주세요 (예: llama3, qwen, gemma 등)
    TARGET_MODEL = "gemma4"
    
    print(f"--- Generate API 테스트 ({TARGET_MODEL}) ---")
    prompt_text = "양자 컴퓨팅에 대해 한 문장으로 설명해줘."
    print(f"질문: {prompt_text}")
    print("답변 생성 중...\n")
    
    generate_response = call_ollama_generate(prompt_text, model=TARGET_MODEL)
    if generate_response:
        print(f"답변:\n{generate_response}\n")


    print(f"--- Chat API 테스트 ({TARGET_MODEL}) ---")
    chat_messages = [
        {"role": "system", "content": "너는 친절하고 유용한 AI 어시스턴트야."},
        {"role": "user", "content": "안녕! 오늘 기분 어때?"}
    ]
    print(f"메시지: {chat_messages}")
    print("답변 생성 중...\n")
    
    chat_response = call_ollama_chat(chat_messages, model=TARGET_MODEL)
    if chat_response:
        print(f"답변:\n{chat_response}")
