# Chatbot Socrates Multi-Agent

Questo repository ospita due progetti principali dedicati alla gestione di sistemi RAG (Retrieval-Augmented Generation): una parte formativa (`rag_formativo`) e una parte informativa (`rag_informative`). Ogni cartella contiene codice Python, dipendenze e configurazioni Docker per avviare servizi che integrano modelli LLM, ricerca semantica, estrazione da PDF e servizi di testo-audio.

## Struttura del repository

- `rag_formativo/`
- `rag_informative/`

## `rag_formativo`

Questa cartella contiene un servizio Flask che implementa un assistente Socrates per utilizzo formativo e motivazionale. Il sistema è pensato per rispondere in modo socratico e usare ricerche su contenuti esterni per risposte più dettagliate.

File principali:

- `Dockerfile`
  - Definisce l'immagine container per il servizio formativo.
  - Installa dipendenze di sistema e Python, copia il codice e avvia l'app Flask.

- `rag_formativo_socrates.py`
  - Applicazione Flask principale.
  - Inizializza il client Azure OpenAI e il servizio di ricerca Azure.
  - Definisce template di sistema per risposte socratiche in italiano e inglese.
  - Registra endpoint API, tra cui:
    - `/api-socrates/uninettuno_assistant`
    - `/api-socrates/uninettuno_translator`
    - `/api-socrates/uninettuno_speech_to_text`
    - `/api-socrates/uninettuno_text_to_speech`
    - `/api-socrates/uninettuno_recommendation_question`
    - `/api-socrates/uninettuno_topic_summarization`
  - Gestisce conversazione, controlli di salute e generazione di risposte con stile Socratico.

- `search_api.py`
  - Wrapper per Azure Cognitive Search.
  - Crea query vettoriali con embeddings e usa la ricerca semantica per recuperare documenti rilevanti.
  - Mappa i risultati della ricerca in un formato strutturato e gestisce metadata come titolo, pagina e contenuto.

- `urls_handler.py`
  - Utility per estrarre parole chiave o numeri di pagina da URL.
  - Serve a interpretare link che contengono riferimenti a pagine o documenti.

- `requirements.txt`
  - Elenca le dipendenze Python richieste per il servizio formativo.
  - Include pacchetti come `openai`, `Flask`, `azure-search-documents`, `python-dotenv` e `gunicorn`.

## `rag_informative`

Questa cartella contiene il codice per un servizio informativo avanzato e multi-funzione, con funzioni di indicizzazione, estrazione da PDF, ricerca Google, sintesi vocale e servizi API.

File principali:

- `Dockerfile` / `Dockerfile2`
  - Contengono istruzioni per creare l'immagine Docker del servizio informativo.
  - Installano dipendenze di sistema audio e Python.
  - Copiano il codice sorgente e avviano il servizio principale.

- `advance_indexing.py`
  - Gestisce l'indicizzazione avanzata dei contenuti.
  - Supporta la creazione o l'aggiornamento di indici per il retrieval.

- `extract_pdf.py`
  - Estrae testo dai file PDF.
  - Trasforma documenti PDF in contenuti testuali utilizzabili per ricerca e indicizzazione.

- `google_search.py`
  - Integrazione per eseguire ricerche su Google.
  - Recupera informazioni esterne per arricchire le risposte.

- `lang2_search.py`
  - Gestisce ricerche multilingua o query in varie lingue.
  - Supporta il recupero di informazioni in diverse lingue.

- `streaming_tts.py`
  - Componente di sintesi vocale in streaming.
  - Genera audio da testo e supporta la riproduzione in real time.

- `uninettuno_interogation.py`
  - Applicazione principale del servizio informativo.
  - Definisce endpoint API per assistente, browser, audio, TTS, raccomandazioni e sommario.

- `utils.py`
  - Contiene funzioni di utilità condivise.
  - Supporta operazioni generiche di parsing, formattazione e gestione dati.

- `readme.md`
  - Fornisce istruzioni pratiche per installazione, deploy e uso del servizio.

- `requirements.txt`
  - Elenca le dipendenze Python necessarie per il servizio informativo.

## Contesto generale

Questo repository è organizzato in due progetti complementari:

1. `rag_formativo`: un assistente Socrates dedicato all'ambito formativo, con focus su conversazioni motivazionali, classificazione delle domande e uso di Azure Search per risposte informate.
2. `rag_informative`: un sistema informativo più ampio, con supporto per estrazione da PDF, ricerca esterna, sintesi vocale e deploy container.

## Note aggiuntive

- Per la cartella `rag_informative`, esiste un `readme.md` interno con istruzioni dettagliate per installazione e deploy.
- Il servizio `rag_formativo` utilizza Azure OpenAI, Azure Search e un template di sistema che definisce il comportamento socratico dell'assistente.
- Entrambi i progetti sono pensati per funzionare in ambienti Docker e possono essere estesi con nuovi moduli di ricerca, indicizzazione e interfacce.
