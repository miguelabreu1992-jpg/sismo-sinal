# MIDI virtual

A orquestra envia OSC para o SuperCollider e, opcionalmente, MIDI para uma porta virtual Windows.

## Preparar

1. Instala o loopMIDI: https://www.tobias-erichsen.de/software/loopmidi.html
2. Cria uma porta com o nome exato:

   `Sismo Orchestra MIDI`

3. Inicia `start_visualizer.bat`.

Nao precisas de instalar `python-rtmidi`: no Windows, o projeto usa diretamente
a API MIDI nativa `winmm.dll`.

Se a porta existir, a consola mostra:

```text
MIDI ativo: Sismo Orchestra MIDI
```

Cada pico envia `note_on` e, 350 ms depois, `note_off`.

## Ableton Live

Em `Preferences > Link, Tempo & MIDI`, ativa `Track` para `Sismo Orchestra MIDI`. Numa pista MIDI, seleciona essa porta em `MIDI From`, ativa `Monitor: In` ou arma a pista.

## VCV Rack

Adiciona o módulo `MIDI-CV`, escolhe `Sismo Orchestra MIDI` e liga `V/OCT`, `GATE` e `VELOCITY` ao sintetizador.

Sem loopMIDI ou sem a porta criada, o OSC e o som do SuperCollider continuam a funcionar; o MIDI fica apenas desativado.
