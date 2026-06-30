#### Questo repository contiene il codice funzionante. E' stato deployato sul azure devops
**Il codice contiene un ampia gamma di funzionalita**
- Generazione del testo
- Elaborazione del browsing
- Generazione del testo da audio
- Generazione del audio da testo
- Generazione del mecanismo raccomandazione
- generazione del summarizzation sulla domanda della utente
- generazione della raffinamento delle domanda della utente
- il branch si chiama: server_tts_deploy_002
- il branch si chiama:server_tts_dev_simply_003 e' stata migliorata molto 30.01.2024(per il rag informativo)
- il branch  titolato: server_tts_deploy_simply_004  e' stata migliorata molto 03.02.2024 e distribuito sulla azure 
- il branch (dev04_adaptive_rag_v4) contiene ultimi aggiornamenti per la rag informativo v4 e sta in esercizio

Seguenti Endpoint sono funzionanti:

```python
# uninettuno_assitant
self.app.add_url_rule('/api/uninettuno_assistant', view_func=self.handleUserInput, methods=['GET','POST'])


# endpoint for health check
self.app.add_url_rule('/api/backend_health', view_func = self.verify_health_check, methods=['GET'])

# browsing
self.app.add_url_rule('/api/uninettuno_browsering', view_func=self.browseringUninettuno, methods=['POST'])

#speech recognition
self.app.add_url_rule('/api/uninettuno_audio_to_text', view_func=self.postprocessedSpeech, methods=['POST'])

# text to speech 
self.app.add_url_rule('/api/uninettuno_text_to_speech', view_func=self.convert_TextTo_Speech, methods=['POST'])

# get recommendation
self.app.add_url_rule('/api/uninettuno_recommendation_question', view_func=self.get_recommendation_from_llm, methods=['POST'])

# summarize topics
self.app.add_url_rule('/api/uninettuno_topic_summarization', view_func = self.get_summarization_from_llm, methods=['POST'])
```