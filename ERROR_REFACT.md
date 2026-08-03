# Refactoring futuro - Gestione degli errori dell'encoder

> **Stato:** decisioni architetturali approvate.
>
> **Priorità:** posticipato a dopo l'implementazione completa della generazione delle animazioni.

---

# Situazione attuale

La prima implementazione di `encoder.py` utilizza eccezioni standard di Python (`ValueError`, `RuntimeError`, `FileNotFoundError`, `BrokenPipeError`, ecc.).

Questa scelta è stata adottata esclusivamente per completare l'infrastruttura dell'encoder senza introdurre immediatamente una nuova gerarchia di errori.

L'encoder **non gestisce definitivamente gli errori**.

Ogni eccezione:

1. esegue la pulizia delle risorse interne (pipe, processo FFmpeg, file temporanei);
2. viene rilanciata al chiamante.

L'encoder non comunica direttamente con la UI e non produce messaggi destinati all'utente.

---

# BrokenPipeError

`BrokenPipeError` **non è stato implementato nel progetto**.

È una normale eccezione di Python (sottoclasse di `OSError`) che può essere sollevata automaticamente quando FFmpeg termina prematuramente e la scrittura sulla pipe fallisce.

L'encoder la intercetta esclusivamente per eseguire la pulizia delle risorse, dopodiché la rilancia.

---

# Necessità del refactoring

L'encoder dovrà essere integrato nella gerarchia degli errori PBD.

L'obiettivo è evitare che il resto del progetto debba conoscere eccezioni standard di Python.

L'encoder dovrà quindi produrre esclusivamente eccezioni appartenenti alla propria gerarchia.

---

# Gerarchia dedicata

È stata approvata la creazione di una gerarchia dedicata:

```text
PBDError
└── EncoderError
    ├── ...
    ├── ...
    └── ...
```

Tutte le eccezioni prodotte da `encoder.py` dovranno appartenere a questa gerarchia.

Le classi definitive verranno progettate durante il refactoring.

---

# Problema individuato nella hierarchy attuale

Durante la discussione è emerso un limite dell'attuale sistema `PBDError.hierarchy()`.

La traduzione globale delle eccezioni native non è sufficientemente flessibile.

Esempio:

```text
FileNotFoundError
```

può significare:

- file di configurazione mancante;
- eseguibile FFmpeg mancante;
- frame mancante;
- metadata mancante;
- altra risorsa assente.

Una traduzione globale produce inevitabilmente ambiguità.

---

# Decisione architetturale

La responsabilità della traduzione deve appartenere al dominio che conosce il significato dell'errore.

Si introduce quindi il concetto di **hierarchy specializzata per dominio**.

Schema previsto:

```text
PBDError
│
├── gestione comune
│
├── ConfigError
│   └── hierarchy()
│
├── EncoderError
│   └── hierarchy()
│
├── DownloaderError
│   └── hierarchy()
│
└── ...
```

Ogni famiglia di errori sarà responsabile della traduzione delle eccezioni native nel proprio contesto.

---

# Responsabilità di PBDError

La classe base dovrà limitarsi alle funzionalità comuni:

- rappresentazione dell'errore;
- concatenazione delle cause (`raise ... from ...`);
- reportistica comune;
- eventuali traduzioni realmente universali.

Non dovrà più contenere la logica di traduzione specifica dei singoli moduli.

---

# Responsabilità delle hierarchy specializzate

Ogni sottoclasse (`EncoderError`, `ConfigError`, ecc.) implementerà la propria funzione `hierarchy()`.

Ad esempio:

```python
EncoderError.hierarchy(error)
```

oppure

```python
ConfigError.hierarchy(error)
```

La sottoclasse conosce il proprio dominio e può quindi assegnare il corretto significato alle eccezioni native.

---

# Vantaggi della nuova architettura

- eliminazione della traduzione globale rigida;
- migliore separazione delle responsabilità;
- nessuna dipendenza da stringhe identificative del modulo;
- ogni dominio traduce solamente gli errori che conosce;
- maggiore estendibilità del sistema;
- riduzione dell'accoppiamento tra moduli.

---

# Stato della decisione

La soluzione è stata approvata a livello architetturale.

L'implementazione viene rimandata a un refactoring successivo, successivamente al completamento dell'integrazione dell'encoder e della generazione delle animazioni.