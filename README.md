Questo è un progetto realizzato in Python che implementa un semplice gioco multiplayer basato su parole, con funzionalità client-server. Il gioco consente a più utenti di connettersi a un server centrale, partecipare in tempo reale, scambiarsi messaggi e visualizzare una classifica aggiornata in base ai punteggi. L’interfaccia grafica lato client è realizzata con la libreria Dear PyGui, mentre la logica di rete utilizza i socket TCP per la comunicazione tra client e server.

USER STORIES
Come giocatore:
Voglio potermi connettere al server inserendo il mio nickname, così da poter partecipare al gioco con altri utenti.
Voglio vedere i messaggi del server e degli altri giocatori in una chat, in ordine cronologico, per seguire lo svolgimento del gioco.
Voglio visualizzare la classifica dei punteggi aggiornata, così da sapere chi sta vincendo.
Voglio che la classifica venga aggiornata automaticamente, senza dover fare nulla, così da avere sempre informazioni aggiornate.


Come server:
Voglio gestire le connessioni dei client, assegnando un nickname ad ogni giocatore connesso.
Voglio mantenere e aggiornare i punteggi dei giocatori in tempo reale, così da poter mostrare la classifica corretta.
volio poter salvare il punteggio in un file txt 
Voglio inviare messaggi a tutti i client, in modo da condividere aggiornamenti o risultati.
Voglio scegliere casualmente una parola da indovinare da una lista, per rendere il gioco variabile e interessante.
Voglio mostrare lo stato parziale della parola in base alle lettere indovinate, per guidare i giocatori nel gioco.
Voglio che più client possano connettersi contemporaneamente senza che si verifichino errori o crash.

link presentazione canva: 
https://www.canva.com/design/DAGms47q7WU/O0z9AnNej4XyCsrWPS_mtw/edit?utm_content=DAGms47q7WU&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton




