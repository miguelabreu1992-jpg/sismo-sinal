"""
SONIFICAÇÃO DE ATIVIDADE SÍSMICA RECENTE (loop)
=================================================
Em vez de esperar por um sismo ao vivo, vai buscando periodicamente a
janela mais recente de dados já registados (ex: os últimos 10 minutos),
deteta os picos e toca-os em modo comprimido (acelerado) via OSC para o
SuperCollider. Repete em loop, sempre com a janela mais atual.

Como o ruído microssísmico de fundo já produz picos pequenos constantes,
vais ouvir som com muito mais frequência do que à espera de um sismo real.

REQUISITOS:
    pip install obspy python-osc --break-system-packages

COMO USAR:
1. Corre este script.
2. Corre o live_sismo_receptor.scd no SuperCollider (o recetor OSC é o
   mesmo dos dois modos, não precisas de mudar nada lá).
"""

import csv
import os
import time
import numpy as np
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
from pythonosc.udp_client import SimpleUDPClient

# ---------------------------------------------------------------
# 1. CONFIGURAÇÃO
# ---------------------------------------------------------------
NETWORK = "IU"
STATION = "MACI"
CHANNEL = "BHZ"

JANELA_MINUTOS = 10          # quantos minutos de dados pedir de cada vez
INTERVALO_ENTRE_PEDIDOS = 15  # segundos de espera real entre cada pedido novo
COMPRESSAO = 40               # 40x mais rápido: 10 min reais -> 15s de som

THRESHOLD = 0.01              # sensibilidade alta: apanha picos sísmicos pequenos
MIN_GAP_SECONDS_REAL = 1.5    # espaçamento mínimo entre picos, em tempo REAL do sinal
MIN_NOTE, MAX_NOTE = 36, 84

OSC_IP = "127.0.0.1"
OSC_PORT = 57120
EVENT_LOG = "sismo_sound_events.csv"

# ---------------------------------------------------------------
# 2. SETUP
# ---------------------------------------------------------------
client = Client("EARTHSCOPE")
osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)


def registar_evento(event_time, amplitude_signal, midi_note, freq, amp):
    """Guarda os valores do pico que foram enviados para o SuperCollider."""
    file_exists = os.path.exists(EVENT_LOG)
    with open(EVENT_LOG, "a", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=[
            "event_time_utc", "signal_amplitude", "midi_note",
            "frequency_hz", "synth_amplitude",
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "event_time_utc": event_time.isoformat(),
            "signal_amplitude": f"{amplitude_signal:.6f}",
            "midi_note": midi_note,
            "frequency_hz": f"{freq:.3f}",
            "synth_amplitude": f"{amp:.6f}",
        })


def midi_to_freq(note):
    return 440.0 * (2 ** ((note - 69) / 12.0))


def processar_janela(trace):
    """Deteta picos numa janela de dados já descarregada e toca-os
    em modo comprimido, respeitando o espaçamento relativo entre eles."""
    data = trace.data.astype(float)
    sample_rate = trace.stats.sampling_rate

    max_abs = max(abs(data.max()), abs(data.min()), np.finfo(float).eps)
    norm = data / max_abs

    peak_times = []
    peak_amps = []
    last_t = -999

    for i in range(1, len(norm) - 1):
        a = abs(norm[i])
        is_local_max = a > abs(norm[i - 1]) and a > abs(norm[i + 1])
        t = i / sample_rate
        if is_local_max and a > THRESHOLD and (t - last_t) > MIN_GAP_SECONDS_REAL:
            peak_times.append(t)
            peak_amps.append(a)
            last_t = t

    print(f"  Picos encontrados nesta janela: {len(peak_times)}")

    prev_t = peak_times[0] if peak_times else 0
    for t, a in zip(peak_times, peak_amps):
        wait_time = (t - prev_t) / COMPRESSAO
        if wait_time > 0:
            time.sleep(min(wait_time, 2.0))  # limite de segurança por nota

        midi_note = MIN_NOTE + a * (MAX_NOTE - MIN_NOTE)
        midi_note = min(max(midi_note, MIN_NOTE), MAX_NOTE)
        freq = midi_to_freq(round(midi_note))
        amp = min(max(a, 0.1), 0.9)

        osc_client.send_message("/sismo", [float(freq), float(amp)])
        registar_evento(trace.stats.starttime + t, a, round(midi_note), freq, amp)
        prev_t = t


def main():
    print(f"Estação: {NETWORK}.{STATION}.{CHANNEL}")
    print(f"A repetir a cada {INTERVALO_ENTRE_PEDIDOS}s, janela de {JANELA_MINUTOS} min, "
          f"comprimida {COMPRESSAO}x. Registo: {EVENT_LOG}. Ctrl+C para parar.\n")

    while True:
        try:
            end = UTCDateTime.now()
            start = end - JANELA_MINUTOS * 60

            print(f"[{end}] A pedir dados recentes...")
            st = client.get_waveforms(NETWORK, STATION, "*", CHANNEL, start, end)
            st.merge(method=1, fill_value="interpolate")
            trace = st[0]

            processar_janela(trace)

        except Exception as e:
            print(f"  Aviso: falha a obter/processar dados ({e}). A tentar de novo...")

        time.sleep(INTERVALO_ENTRE_PEDIDOS)


if __name__ == "__main__":
    main()
