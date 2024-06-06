import azure.cognitiveservices.speech as speechsdk
import ollama
import time

# Configurazione di Azure per il riconoscimento vocale
speech_key, service_region = "YOUR API KEY HERE", "northeurope"
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_recognition_language = "it-IT"

# Configurazione di Azure per la sintesi vocale
speech_config.speech_synthesis_voice_name = "it-IT-ElsaNeural"

# Funzione per il riconoscimento vocale
def recognize_speech():
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
    result = speech_recognizer.recognize_once()
    return result

# Funzione per la generazione di testo usando il modello LLaMA con ollama
def generate_text(prompt, start_time):
    instruction = "Per favore aggiungi '~' alla fine di ogni frase."
    stream = ollama.chat(
        model='llama3',
        messages=[
            {'role': 'system', 'content': instruction},
            {'role': 'user', 'content': prompt}
        ],
        stream=True,
    )
    response_text = ""
    sentence = ""

    # Misura il tempo di inizio dell'elaborazione del modello LLaMA
    llama_start_time = time.time() * 1000  # Tempo in millisecondi

    # Calcola il tempo dalla fine della pronuncia all'inizio dell'elaborazione di LLaMA
    time_to_llama = llama_start_time - start_time
    print("Tempo dalla fine della pronuncia all'inizio dell'elaborazione di LLaMA: {:.2f} millisecondi".format(time_to_llama))

    for chunk in stream:
        sentence += chunk['message']['content']
        if '~' in sentence:  # Usa il carattere speciale ~ per determinare la fine di una frase
            parts = sentence.split('~')
            for part in parts[:-1]:
                response_text += part + '~'
                synthesize_text_chunk(part + '~')
            sentence = parts[-1]
    return response_text

# Funzione per sintetizzare un chunk di testo
def synthesize_text_chunk(text_chunk):
    # Utilizza una nuova istanza del sintetizzatore per evitare di interrompere la sintesi in corso
    local_speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    local_speech_config.speech_synthesis_voice_name = "it-IT-ElsaNeural"
    local_synthesizer = speechsdk.SpeechSynthesizer(speech_config=local_speech_config)
    local_synthesizer.speak_text_async(text_chunk).get()  # Aspetta che la sintesi sia completata

# Variabile per tracciare lo stato della modalità di ascolto
listening_mode = False

# Loop principale
while True:
    if not listening_mode:
        print("Say 'ascolta' to start listening.")
        result = recognize_speech()

        # Controllo del risultato del riconoscimento vocale
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            recognized_text = result.text.lower()
            print("Recognized: {}".format(recognized_text))

            if "ascolta" in recognized_text:
                print("Listening mode activated. Please ask your question.")
                listening_mode = True
                # Riproduzione del prompt per fare una domanda
                synthesize_text_chunk("Ciao Simone, fammi una domanda.")
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(result.no_match_details))
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
            break
    else:
        result = recognize_speech()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            recognized_text = result.text.lower()
            print("Recognized: {}".format(recognized_text))

            if "adesso puoi andare" in recognized_text:
                print("Stopping execution as per user request.")
                break

            start_time = time.time() * 1000  # Tempo in millisecondi

            response_text = generate_text(recognized_text, start_time)

            # Calcola il tempo trascorso da domanda a risposta
            end_time = time.time() * 1000  # Tempo in millisecondi
            processing_time = end_time - start_time
            print("Tempo di elaborazione da domanda a risposta: {:.2f} millisecondi".format(processing_time))

            print("Risposta generata: {}".format(response_text))

            # Dopo aver risposto, torna alla modalità di ascolto solo se il comando "ascolta" viene ripetuto
            if "ascolta" not in recognized_text:
                listening_mode = False
