from dotenv import load_dotenv
import os
import tempfile
import whisper
import ffmpeg
from langchain_openai import AzureChatOpenAI
from elevenlabs.client import ElevenLabs

# Load environment variables
load_dotenv()

# Whisper STT
whisper_model = whisper.load_model("base")
ELEVEN_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Chat
llm = AzureChatOpenAI(
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    temperature=0.7
)

def transcribe_audio(audio_file):
    """Transcribe using local Whisper model."""
    print("---TRANSCRIBING AUDIO with Whisper local---")
    
    temp_path = ""
    wav_file = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp:
            temp.write(audio_file.read())
            temp_path = temp.name

        wav_file = temp_path.replace(".webm", ".wav")
        
        (
            ffmpeg
            .input(temp_path)
            .output(wav_file, acodec='pcm_s16le', ac=1, ar='16k')
            .run(quiet=True, overwrite_output=True)
        )
        
        result = whisper_model.transcribe(wav_file)
        return result["text"]
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if wav_file and os.path.exists(wav_file):
            os.remove(wav_file)


def get_chat_response(history: list, user_input: str):
    """Gets a text response from the chat model."""
    print("---GETTING CHAT RESPONSE---")
    messages = history + [{"role": "user", "content": user_input}]
    response = llm.invoke(messages)
    return response.content

def synthesize_speech(text_input: str):
    """Synthesizes speech using the ElevenLabs client."""
    print("---SYNTHESIZING SPEECH WITH 11LABS---")

    client = ElevenLabs(api_key=ELEVEN_API_KEY)
    
    # ** THE FIX IS HERE **
    # Using the exact parameter names from the documentation
    audio_stream = client.text_to_speech.stream(
        text=text_input,
        voice_id=ELEVEN_VOICE_ID,      # Corrected parameter: voice_id
        model_id="eleven_multilingual_v2", # Corrected parameter: model_id
        voice_settings={              # Settings passed as a dictionary
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    )

    return audio_stream