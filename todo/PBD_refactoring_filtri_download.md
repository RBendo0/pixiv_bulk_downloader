# PBD --- Refactoring filtri di download

## Stato

Decisioni architetturali fissate il 29 agosto 2026.

Il refactoring **non viene implementato ora**. Questo documento
raccoglie le decisioni già prese per poter riprendere il lavoro in
seguito senza dover ricostruire il ragionamento.

## Obiettivo

Aggiungere al sottomenu di download dei bookmark una preselezione delle
opere basata sui dati già disponibili nel metadata.

I filtri previsti sono:

-   **tipo di opera**;
-   **tag**;
-   combinazione di tipo e tag.

La preselezione deve avvenire durante `retrieve_bookmarks()`, **prima
del salvataggio dell'indice dell'opera**.

## Nuovo modulo `filter.py`

La logica dei filtri verrà isolata in un nuovo modulo `filter.py`.

Il modulo avrà come responsabilità principale la validazione di **un
singolo `PixivMetadata`** rispetto ai filtri attualmente impostati.

``` text
PixivMetadata + filtri impostati
              ↓
           filter
              ↓
       accettato / escluso
```

`filter.py` non deve occuparsi del download effettivo né modificare il
comportamento dei downloader.

## Punto di applicazione

Il filtro verrà applicato in `retrieve_bookmarks()` dopo la costruzione
e la validazione iniziale di `PixivMetadata`, ma prima dell'acquisizione
dei metadata Ugoira aggiuntivi, dell'eventuale metadata autore, di
`save_metadata()` e dell'inserimento nell'indice destinato al download.

``` text
bookmark Pixiv
      ↓
costruzione PixivMetadata
      ↓
validazione iniziale metadata
      ↓
filter
   ├── escluso  → opera successiva
   └── accettato
          ↓
     dati accessori
          ↓
     save_metadata()
          ↓
     indice download
```

Questo evita anche chiamate API accessorie per opere che sono già state
escluse.

## Filtro per tipo di opera

La selezione per tipo deve essere esplicita. I tipi costituiscono un
insieme chiuso conosciuto dall'applicazione, indicativamente:

-   illustrazione;
-   manga;
-   Ugoira.

Deve essere possibile selezionare uno o più tipi. In assenza di una
selezione per tipo, nessun tipo viene escluso.

Un uso importante è il **testing mirato**: selezionando esclusivamente
le Ugoira sarà possibile ottenere rapidamente un insieme di download
pertinente quando si provano modifiche all'Encoder, nuovi codec o altre
funzionalità specifiche delle animazioni.

## Filtro per tag

I tag sono già disponibili nel metadata e quindi non richiedono nuove
richieste a Pixiv per effettuare il filtro.

A differenza dei tipi di opera, i tag costituiscono un vocabolario
aperto. Non è quindi opportuno codificare manualmente un elenco completo
e statico.

Il filtro dovrà permettere la selezione delle opere sulla base di uno o
più tag.

La semantica precisa della selezione multipla dei tag --- per esempio
corrispondenza con almeno un tag oppure con tutti i tag selezionati ---
verrà definita durante l'implementazione.

## Catalogo locale dei tag

`filter.py` potrà contenere anche la logica per costruire e mantenere un
**catalogo dei tag conosciuti**.

Una funzione prevista potrà:

1.  scansionare i metadata delle opere già presenti nell'archivio
    locale;
2.  estrarre tutti i tag incontrati;
3.  catalogarli;
4.  salvare il catalogo in un file JSON.

Il catalogo rappresenterà i tag **osservati localmente**, non un elenco
normativo o necessariamente completo dei tag esistenti su Pixiv.

Una struttura iniziale potrebbe essere:

``` json
{
    "tags": [
        "original",
        "風景",
        "女の子"
    ]
}
```

Informazioni aggiuntive, come frequenza o ultima occorrenza, verranno
valutate solo se emergerà una necessità concreta.

## Interfaccia utente futura

Al download successivo il catalogo locale potrà essere usato per
riproporre i tag conosciuti tramite un menu a selezione multipla /
toggle.

``` text
Filtra per tag

[A] original
[B] 風景
[C] 女の子
...
```

La UI raccoglie i criteri scelti dall'utente; `filter.py` li interpreta
e valida i metadata. La logica della UI non deve quindi essere
incorporata nella logica di validazione del filtro.

## Composizione dei filtri

Tipo e tag sono dimensioni indipendenti e devono poter essere combinate.

Esempi:

``` text
solo Ugoira
solo manga
illustrazioni + manga
solo Ugoira con un determinato tag
più tipi limitati a determinati tag
```

La regola generale prevista è:

``` text
criterio tipo AND criterio tag
```

Un criterio non impostato non introduce restrizioni sulla propria
dimensione.

## Confini architetturali

``` text
UI / bookmarks.py
    raccoglie i criteri scelti
              ↓
filter.py
    conosce e applica i criteri
    conosce i tipi di opera
    gestisce/cataloga il vocabolario locale dei tag
              ↓
retrieve_bookmarks()
    decide quando sottoporre ogni metadata al filtro
              ↓
download
    riceve soltanto le opere accettate
```

`PixivBaseDownloader.download()` deve restare ignaro dell'esistenza dei
filtri: continuerà a ricevere semplicemente la lista dei `PixivMetadata`
da scaricare.

## Decisioni rinviate

Non sono ancora stati definiti:

-   la struttura concreta delle classi/funzioni di `filter.py`;
-   il tipo dati con cui rappresentare i criteri;
-   la struttura definitiva del JSON dei tag;
-   la semantica AND/OR fra più tag selezionati;
-   il comportamento esatto e l'aspetto del menu;
-   quando e come aggiornare automaticamente il catalogo locale;
-   eventuale inserimento manuale di tag non ancora presenti nel
    catalogo.

Questi aspetti verranno decisi a partire dai casi d'uso reali durante il
refactoring, evitando astrazioni preventive.
