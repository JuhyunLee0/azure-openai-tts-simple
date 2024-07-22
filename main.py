import os
import requests
import base64
import time
import streamlit as st
from streamlit.components.v1 import html
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

aoai_api_key = os.getenv("AZURE_OPENAI_KEY")
aoai_api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
aoai_api_deployment_name = os.getenv("AZURE_OPENAI_GPT4_DEPLOYMENT_NAME")
aoai_tts_deploy_name = os.getenv("AZURE_OPENAI_TTS_DEPLOYMENT_NAME")
# alloy, echo, fable, onyx, nova, and shimmer.
aoai_tts_voice_name = "nova"

# Initialize session state
if 'text_ready' not in st.session_state:
    st.session_state.text_ready = False
if 'audio_ready' not in st.session_state:
    st.session_state.audio_ready = False
if 'button_disabled' not in st.session_state:
    st.session_state.button_disabled = False


def get_chat_response(user_input):
    client = AzureOpenAI(
        api_key=aoai_api_key,
        api_version="2023-05-15",
        azure_endpoint=aoai_api_endpoint
    )

    conversaion = [
        {"role": "system", "content": "you are helpful assistant that answer is short and concise manner."},
        {"role": "user", "content": user_input}
    ]

    response = client.chat.completions.create(
        model=aoai_api_deployment_name,
        messages=conversaion,
    )
    print(response)

    responseText = response.choices[0].message.content
    return responseText

def text_to_speech(text):

    # Define the variables
    azure_openai_endpoint = f"{aoai_api_endpoint}/openai/deployments/{aoai_tts_deploy_name}/audio/speech"
    api_version = "2024-02-15-preview"
    headers = {
        "api-key": aoai_api_key,
        "Content-Type": "application/json"
    }
    data = {
        "model": "tts-1-hd",
        "input": text,
        "voice": aoai_tts_voice_name
    }

    try:
        # Make the POST request
        response = requests.post(f"{azure_openai_endpoint}?api-version={api_version}", json=data, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Error generating speech: {e}")
        return None

    return response.content

# Streamlit app logic
st.title("Voice-Enabled Chatbot")

with st.form("user_form"):
    msg = st.text_input("Message: ", value = "")
    submit_button = st.form_submit_button(label="Send")

st.divider()

if submit_button:
    if not st.session_state.button_disabled:
        st.session_state.button_disabled = True

        if not st.session_state.text_ready:
            with st.spinner('Thinking...'):
                # Get chat response from Azure OpenAI
                response_text = get_chat_response(msg)
                
                st.markdown(f"<p>{response_text}</p>", unsafe_allow_html=True)

                st.session_state.text_ready = True

            if st.session_state.text_ready:
                with st.spinner('Generating audio...'):
                    # Convert text to speech
                    speech_data = text_to_speech(response_text)

                    # Encode the speech data for embedding in HTML
                    b64_audio = base64.b64encode(speech_data).decode()

                    # Set the audio ready flag in session state
                    st.session_state.audio_ready = True

                    # Wait for the next iteration to display the audio player
                    time.sleep(1)        

        # Only display the audio player if the audio is ready
        if st.session_state.audio_ready:
            audio_tag = f"""
            <div style='margin-top:20px;'>
            <audio controls>
                <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
            </div>
            """
            
            # Display the audio player in Streamlit
            st.markdown(audio_tag, unsafe_allow_html=True)


# Reset button state after displaying the response
if st.session_state.audio_ready:
    st.session_state.text_ready = False
    st.session_state.audio_ready = False
    st.session_state.button_disabled = False