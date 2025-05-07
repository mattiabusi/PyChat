# Indovina la Parola - Gioco Multiplayer in Python

Un gioco multiplayer basato su socket che permette a più giocatori di connettersi a un server e competere per indovinare una parola segreta. Il gioco include un'interfaccia grafica creata con DearPyGUI.

## Caratteristiche Principali

- **Gameplay semplice ma coinvolgente**: indovina una parola segreta, lettera per lettera o provando la soluzione completa
- **Multiplayer in tempo reale**: gioca con altri partecipanti sulla stessa rete
- **Chat integrata**: comunica con gli altri giocatori durante la partita
- **Sistema di punteggi**: viene tenuta traccia dei punteggi tra le sessioni di gioco
- **Interfaccia grafica moderna**: realizzata con DearPyGUI per un'esperienza utente fluida
- **Comandi intuitivi**: utilizza un sistema di comandi semplice con prefisso "!" per i tentativi

## Struttura del Progetto

- `server_modificato.py`: Server del gioco che gestisce le connessioni, le partite e i punteggi
- `client.py`: Client grafico che si connette al server e fornisce l'interfaccia utente
- `parole.txt`: Database di parole italiane utilizzate per il gioco
- `scores.txt`: File di salvataggio dei punteggi (generato automaticamente)

## Requisiti

- Python 3.6 o superiore
- Libreria DearPyGui (`pip install dearpygui`)
- Connessione di rete funzionante (per il multiplayer sulla stessa rete locale)

## Come Giocare

1. **Connettiti al server** con un nickname univoco
2. **Indovina lettere** digitando `!` seguito da una lettera (es: `!a`)
3. **Indovina la parola completa** digitando `!` seguito dalla parola (es: `!casa`)
4. **Chatta con altri giocatori** scrivendo messaggi senza il prefisso `!`
5. **Usa i comandi** per accedere a funzionalità aggiuntive

## Comandi Disponibili

### Comandi Server
- `/help` - Mostra tutti i comandi disponibili
- `/score` o `/classifica` - Mostra la classifica
- `/online` - Mostra i giocatori connessi
- `/hint` - Richiedi un suggerimento (una lettera casuale)
- `/exit` o `/esci` - Disconnettiti dal server

### Comandi Client
- `/clear` o `/pulisci` - Pulisce la chat
- `/nome` - Mostra il tuo soprannome
- `/time` o `/ora` - Mostra l'ora attuale
- `/exit` o `/esci` - Esce dal gioco

### Comandi Amministratore
- `/kick <nome>` - Espelle un giocatore (disponibile solo per admin e moderatori)

## Funzionamento Tecnico

### Server

Il server gestisce:
- Connessioni multiple di client tramite threading
- Logica del gioco e verifica dei tentativi
- Sistema di punteggi e salvataggio permanente
- Chat e comandi
- Cambio automatico delle parole tra le partite

### Client

Il client fornisce:
- Interfaccia grafica con DearPyGUI
- Connessione al server tramite socket
- Visualizzazione aggiornata della parola da indovinare
- Visualizzazione della classifica in tempo reale
- Chat con gli altri giocatori
- Gestione dei comandi locali

## Personalizzazione

### Aggiungere nuove parole
Aggiungi parole al file `parole.txt`, una per riga. Il server le caricherà automaticamente all'avvio.

### Cambiare la porta
Modifica la variabile `PORT` nel server e `PORTA_SERVER` nel client.

### Modificare l'aspetto grafico
Personalizza i colori e lo stile modificando i parametri nel tema grafico nel file `client.py`.

## Risoluzione dei problemi

- **Errore di connessione**: Verifica che l'indirizzo IP e la porta siano corretti e che non ci siano firewall che bloccano la connessione
- **Nickname già in uso**: Scegli un nickname diverso
- **Errore "Address already in use"**: Attendi qualche secondo o cambia la porta se il server è stato chiuso recentemente

# USER STORIES

## User Stories per Giocatori

- Come giocatore, voglio poter inserire un nickname univoco così da essere identificato durante la partita
- Come giocatore, voglio vedere la parola parzialmente rivelata (con underscore) così da capire quali lettere mancano
- Come giocatore, voglio avere un'interfaccia chiara che mi mostri la chat e la classifica così da seguire il gioco -facilmente
- Come giocatore, voglio vedere un elenco dei comandi disponibili così da conoscere tutte le funzionalità
- Come giocatore, voglio poter provare a indovinare l'intera parola così da guadagnare punti quando sono sicuro
- Come giocatore, voglio essere notificato quando qualcun altro indovina una lettera così da seguire i progressi della partita
- Come giocatore, voglio poter chattare con gli altri giocatori così da socializzare durante la partita
- Come giocatore, voglio ricevere notifiche quando altri giocatori entrano o escono così da sapere chi sta giocando
- Come giocatore, voglio poter pulire la chat così da migliorare la leggibilità


## User Stories per Amministratori

- Come amministratore, voglio poter espellere giocatori problematici così da mantenere un ambiente di gioco positivo
- Come amministratore, voglio che i punteggi vengano salvati in un file così da mantenerli tra le sessioni di gioco
- Come amministratore, voglio vedere messaggi di log sul server così da monitorare l'attività del gioco
- Come amministratore, voglio essere informato quando inizia una nuova partita così da verificare il corretto funzionamento del gioco

## User Stories Tecniche

- Come sviluppatore, voglio che il client gestisca correttamente la perdita di connessione così da permettere ai giocatori di riconnettersi
- Come sviluppatore, voglio che il server gestisca in modo thread-safe le operazioni critiche così da evitare race condition
- Come sviluppatore, voglio fornire un'interfaccia grafica reattiva con DearPyGUI così da offrire una buona esperienza utente
- Come sviluppatore, voglio implementare un sistema di rotazione casuale delle parole così da mantenere il gioco interessante

# Link presentazione canva: 

https://www.canva.com/design/DAGms47q7WU/O0z9AnNej4XyCsrWPS_mtw/edit?utm_content=DAGms47q7WU&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton




