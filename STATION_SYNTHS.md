# Modo synths por estacao

O launcher alternativo e:

```text
start_estacoes_synths.bat
```

Ele usa o mesmo processamento e a mesma fila cronologica, mas inicia `live_sismo_estacoes.scd`.

Cada evento envia:

```text
/sismoEstacao [frequency_hz, amplitude, station_name]
```

Mapeamento de timbres:

- ANMO, COLA, HRV: Pulse
- RCBR, LCO, BOCO: Saw
- KONO, KEV, ANTO: SinOsc com modulacao
- MAJO, MAKZ, TATO: PMOsc
- TSUM, LSZ, MACI: PinkNoise + SinOsc
- CTAO, SNZO, NWAO: SinOsc com modulacao de fase
- CASY, PMSA, SBA: timbre grave combinado

O modo principal continua a ser `start_visualizer.bat`.
