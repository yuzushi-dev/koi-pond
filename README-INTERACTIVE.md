# Dao Ho Koi Pond per Cinnamon X11

Questa variante usa GTK e WebKitGTK. Crea uno sfondo animato per ogni monitor
e lo colloca sotto le finestre delle icone di Nemo.

## Requisiti e avvio

Servono Cinnamon su X11, Python 3, PyGObject, python3-xlib, GTK 3 e WebKitGTK 4.1
(oppure 4.0). Wayland non è supportato. Node.js/npm e curl servono solo per
compilare il renderer con `setup.sh`.

```sh
sudo apt install python3-gi python3-xlib gir1.2-gtk-3.0 gir1.2-webkit2-4.1
./setup.sh
./wallpaper-interactive.sh
```

Se `pond.js` è già presente non serve ripetere `setup.sh`. Entrambi i launcher,
`wallpaper-interactive.sh` e `wallpaper-start.sh`, avviano lo stesso `wallpaper.py`.
`xwinwrap`, `xterm` e il vecchio `wallpaper-x11.py` non sono usati.

Il cursore viene letto tramite GDK senza intercettare i clic destinati a Nemo.
`Alt + clic sinistro` dà cibo ai pesci. Cinnamon può usare la stessa combinazione
per spostare le finestre; il programma non modifica questa scorciatoia.

## Consumo ridotto

- Animazione a 16 fps, simulazione a 30 passi/s e risoluzione del canvas 1×.
- Pausa indipendente per monitor quando una finestra opaca copre tutta l'area
  di lavoro; ripresa entro circa un secondo. Finestre trasparenti, minimizzate
  o di altri spazi di lavoro non attivano la pausa. Più finestre che coprono
  insieme il monitor non sono riconosciute come copertura completa.
- Mouse controllato ogni 125 ms; JavaScript viene aggiornato solo se cambia
  la posizione o arriva un comando per il cibo, e solo sui monitor attivi.
- Le due WebView condividono un processo WebKit tramite
  [`new_with_related_view`](https://webkitgtk.org/reference/webkit2gtk/2.42.3/ctor.WebView.new_with_related_view.html).

Misure locali del 26 ottobre 2026, inclusi Python e tutti i figli WebKit:

| Stato | CPU, 100% = una CPU logica | Motore render GPU Intel | RAM PSS |
| --- | ---: | ---: | ---: |
| Prima, desktop coperto | 80% | 21% | 280 MiB |
| Versione a 8 fps, desktop coperto | 0,5–0,7% | 0% | 221–229 MiB |
| Versione a 8 fps, entrambi i desktop visibili | 27% | 7,6% | 228 MiB |

Campioni brevi: 20 s CPU/10 s GPU per la versione iniziale, 6 s per stato per
la versione finale. CPU e GPU sono attribuite ai processi dello sfondo:
il compositore Cinnamon è escluso. PSS ripartisce le pagine di memoria condivise.
Non sono misure di potenza elettrica o di autonomia. Dal 26 ottobre 2026
l'impostazione scelta è 16 fps: le misure a 8 fps restano storiche e non
quantificano il consumo della configurazione attuale. La pausa riguarda
l'area di lavoro, quindi congela anche lo sfondo
eventualmente visibile attraverso un pannello trasparente.

Il programma ricrea le finestre quando GDK segnala un cambio dei monitor.
Ogni secondo controlla l'ordine delle finestre e, se necessario, invia una
richiesta `_NET_RESTACK_WINDOW` sotto la finestra più bassa di Nemo: il solo
`keep_below` non determina l'ordine fra finestre di tipo DESKTOP su Muffin.

Verificato il 26 ottobre 2026 su Cinnamon 6.4.8/Nemo 6.4.5: animazione su
DP-3-1 (1920×1080) ed eDP-1 (1920×1200), icone visibili sopra lo sfondo, pausa e
ripresa dal vivo, nove test Python e un controllo JavaScript del ciclo animato.
Riavvio della sessione e scollegamento fisico dei monitor
non verificati.

Test: `/usr/bin/python3 -m unittest -v test_wallpaper` e `node test_main.cjs`.
Per terminare un avvio da terminale: `Ctrl+C`.
L'avvio automatico esistente è `~/.config/autostart/koi-pond.desktop` e punta
a `wallpaper-interactive.sh`. I file originali sono in `backup-20261026/`;
la versione precedente all'ottimizzazione è in `backup-before-low-power-20261026/`.
