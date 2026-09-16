"""Orquestra de quatro estacoes sismicas, atualizada a cada 15 segundos."""

import csv
import os
import time

import numpy as np
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from pythonosc.udp_client import SimpleUDPClient

INTERVALO_ENTRE_PEDIDOS = 15
JANELA_SEGUNDOS = 15
THRESHOLD = 0.01
MIN_GAP_SECONDS = 1.5
OSC_IP = "127.0.0.1"
OSC_PORT = 57120
EVENT_LOG = "orquestra_sismo_events.csv"

# Cada estacao ocupa uma regiao diferente para funcionar como uma voz.
ESTACOES = [
    {"nome": "ANMO", "network": "IU", "station": "ANMO", "channel": "BHZ", "min_note": 36, "max_note": 52},
    {"nome": "COLA", "network": "IU", "station": "COLA", "channel": "BHZ", "min_note": 48, "max_note": 64},
    {"nome": "KONO", "network": "IU", "station": "KONO", "channel": "BHZ", "min_note": 60, "max_note": 76},
    {"nome": "MAJO", "network": "IU", "station": "MAJO", "channel": "BHZ", "min_note": 72, "max_note": 88},
]

client = Client("EARTHSCOPE")
osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)
last_peak_by_station = {station["nome"]: -999.0 for station in ESTACOES}


def midi_to_freq(note):
    return 440.0 * (2 ** ((note - 69) / 12.0))


def registar_evento(event_time, station_name, amplitude_signal, midi_note, freq, amp):
    file_exists = os.path.exists(EVENT_LOG)
    with open(EVENT_LOG, "a", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=[
            "station", "event_time_utc", "signal_amplitude", "midi_note",
            "frequency_hz", "synth_amplitude",
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "station": station_name,
            "event_time_utc": event_time.isoformat(),
            "signal_amplitude": f"{amplitude_signal:.6f}",
            "midi_note": midi_note,
            "frequency_hz": f"{freq:.3f}",
            "synth_amplitude": f"{amp:.6f}",
        })


def enviar_pico(station, event_time, amplitude_signal):
    station_name = station["nome"]
    event_seconds = float(event_time)
    if event_seconds - last_peak_by_station[station_name] <= MIN_GAP_SECONDS:
        return

    note = station["min_note"] + amplitude_signal * (station["max_note"] - station["min_note"])
    midi_note = round(min(max(note, station["min_note"]), station["max_note"]))
    freq = midi_to_freq(midi_note)
    amp = min(max(amplitude_signal, 0.1), 0.9)

    osc_client.send_message("/sismo", [float(freq), float(amp)])
    registar_evento(event_time, station_name, amplitude_signal, midi_note, freq, amp)
    last_peak_by_station[station_name] = event_seconds
    print(f"{station_name}: pico {event_time} | nota {midi_note} | {freq:.1f} Hz")


def processar_estacao(station, start, end):
    stream = client.get_waveforms(
        station["network"], station["station"], "*", station["channel"], start, end
    )
    stream.merge(method=1, fill_value="interpolate")

    for trace in stream:
        data = trace.data.astype(float)
        if len(data) < 3:
            continue
        max_abs = max(np.max(np.abs(data)), np.finfo(float).eps)
        normalized = np.abs(data / max_abs)
        sample_rate = trace.stats.sampling_rate

        for index in range(1, len(normalized) - 1):
            is_local_max = normalized[index] > normalized[index - 1] and normalized[index] > normalized[index + 1]
            if is_local_max and normalized[index] > THRESHOLD:
                event_time = trace.stats.starttime + index / sample_rate
                enviar_pico(station, event_time, float(normalized[index]))


def main():
    names = ", ".join(station["nome"] for station in ESTACOES)
    print(f"Orquestra ativa: {names}")
    print(f"A atualizar a cada {INTERVALO_ENTRE_PEDIDOS}s com janelas de {JANELA_SEGUNDOS}s.")
    print("Ctrl+C para parar.\n")

    while True:
        end = UTCDateTime.now()
        start = end - JANELA_SEGUNDOS
        for station in ESTACOES:
            try:
                processar_estacao(station, start, end)
            except Exception as exception:
                print(f"{station['nome']}: falha ao obter dados ({exception})")
        elapsed = float(UTCDateTime.now() - end)
        time.sleep(max(0, INTERVALO_ENTRE_PEDIDOS - elapsed))


if __name__ == "__main__":
    main()
