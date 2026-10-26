# Koi Pond

Esegue una simulazione ASCII delle koi in una pagina HTML indipendente da React e PostHog. I sorgenti TypeScript del renderer, della geometria e della simulazione sono inclusi nella repository. `setup.sh` installa il compilatore e prepara il bundle usando questi sorgenti. Dopo la preparazione funziona offline.

## Requisiti
Linux, Node.js/npm, Python 3 e browser con supporto Canvas 2D.

## Avvio
```bash
chmod +x setup.sh start.sh
./setup.sh
./start.sh
```
Apri http://127.0.0.1:8765/ nel browser. Con Chromium puoi usare `chromium --app=http://127.0.0.1:8765/`.

## Impostazioni
- Sfondo scuro: `http://127.0.0.1:8765/`
- Sfondo chiaro: `http://127.0.0.1:8765/?theme=light`
- Click: aggiunge cibo, i pesci nuotano verso di esso.
- Movimento del mouse: i pesci reagiscono al cursore.
- Puoi impostare `prefers-reduced-motion` per ottenere un fotogramma fermo.

## Uso come wallpaper
Il pacchetto include il motore del wallpaper, non un'integrazione specifica col desktop. Per lo sfondo animato usa un gestore di wallpaper che supporti pagine web locali come sorgenti e imposta `http://127.0.0.1:8765/` come URL. Il metodo per inserire una finestra nel layer desktop dipende da Cinnamon/X11, KDE/Wayland o GNOME.

La simulazione, il renderer e la geometria derivano dall'ASCII Koi Pond originale di **Dao Ho**: https://github.com/Dao-Ho/portfolio/tree/main/src/app/components/koi-pond. Questa variante aggiunge l'integrazione con Cinnamon X11 e la gestione dei consumi.
Verifica la licenza e le condizioni d'uso del progetto prima di redistribuire il lavoro.

## Cinnamon X11: wallpaper su tutti i monitor
Installa su Linux Mint: `sudo apt install python3-gi python3-xlib gir1.2-gtk-3.0 gir1.2-webkit2-4.1`
Se la tua release non ha WebKit 4.1, prova `gir1.2-webkit2-4.0`.
Dopo `./setup.sh`, esegui `./wallpaper-start.sh`. Non serve avviare il server HTTP:
WebKitGTK apre direttamente `index.html` tramite `file://`.
Il programma crea una finestra X11 DESKTOP per monitor e ne mantiene l'ordine sotto le icone di Nemo. Per terminarlo premi `Ctrl+C` nel terminale che lo ha avviato. Dettagli, verifiche e limiti in [README-INTERACTIVE.md](README-INTERACTIVE.md).

Per l'avvio automatico, aggiungi `wallpaper-start.sh` alle Applicazioni d'avvio di Cinnamon solo dopo averlo verificato manualmente.
