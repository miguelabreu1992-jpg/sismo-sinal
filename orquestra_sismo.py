"""Orquestra continental de 21 estacoes, atualizada a cada 15 segundos."""

import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
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
WAVEFORM_LOG = "orquestra_sismo_waveforms.json"

# As estacoes foram escolhidas por atividade RMS recente, mantendo distancia
# geografica entre elas dentro de cada continente.
ESTACOES = [
    {"nome": "ANMO", "continente": "America do Norte", "network": "IU", "station": "ANMO", "channel": "BHZ", "min_note": 36, "max_note": 44},
    {"nome": "COLA", "continente": "America do Norte", "network": "IU", "station": "COLA", "channel": "BHZ", "min_note": 45, "max_note": 52},
    {"nome": "HRV", "continente": "America do Norte", "network": "IU", "station": "HRV", "channel": "BHZ", "min_note": 53, "max_note": 60},
    {"nome": "RCBR", "continente": "America do Sul", "network": "IU", "station": "RCBR", "channel": "BHZ", "min_note": 41, "max_note": 49},
    {"nome": "LCO", "continente": "America do Sul", "network": "IU", "station": "LCO", "channel": "BHZ", "min_note": 50, "max_note": 57},
    {"nome": "BOCO", "continente": "America do Sul", "network": "IU", "station": "BOCO", "channel": "BHZ", "min_note": 58, "max_note": 65},
    {"nome": "KONO", "continente": "Europa", "network": "IU", "station": "KONO", "channel": "BHZ", "min_note": 48, "max_note": 55},
    {"nome": "KEV", "continente": "Europa", "network": "IU", "station": "KEV", "channel": "BHZ", "min_note": 56, "max_note": 63},
    {"nome": "ANTO", "continente": "Europa", "network": "IU", "station": "ANTO", "channel": "BHZ", "min_note": 64, "max_note": 71},
    {"nome": "MAJO", "continente": "Asia", "network": "IU", "station": "MAJO", "channel": "BHZ", "min_note": 56, "max_note": 64},
    {"nome": "MAKZ", "continente": "Asia", "network": "IU", "station": "MAKZ", "channel": "BHZ", "min_note": 65, "max_note": 73},
    {"nome": "TATO", "continente": "Asia", "network": "IU", "station": "TATO", "channel": "BHZ", "min_note": 74, "max_note": 82},
    {"nome": "TSUM", "continente": "Africa", "network": "IU", "station": "TSUM", "channel": "BHZ", "min_note": 42, "max_note": 50},
    {"nome": "LSZ", "continente": "Africa", "network": "IU", "station": "LSZ", "channel": "BHZ", "min_note": 51, "max_note": 59},
    {"nome": "MACI", "continente": "Africa", "network": "IU", "station": "MACI", "channel": "BHZ", "min_note": 60, "max_note": 68},
    {"nome": "CTAO", "continente": "Oceania", "network": "IU", "station": "CTAO", "channel": "BHZ", "min_note": 48, "max_note": 56},
    {"nome": "SNZO", "continente": "Oceania", "network": "IU", "station": "SNZO", "channel": "BHZ", "min_note": 57, "max_note": 65},
    {"nome": "NWAO", "continente": "Oceania", "network": "IU", "station": "NWAO", "channel": "BHZ", "min_note": 66, "max_note": 74},
    {"nome": "CASY", "continente": "Antartida", "network": "IU", "station": "CASY", "channel": "BHZ", "min_note": 44, "max_note": 52},
    {"nome": "PMSA", "continente": "Antartida", "network": "IU", "station": "PMSA", "channel": "BHZ", "min_note": 53, "max_note": 61},
    {"nome": "SBA", "continente": "Antartida", "network": "IU", "station": "SBA", "channel": "BHZ", "min_note": 62, "max_note": 70},
]
CONTINENTES = ["America do Norte", "America do Sul", "Europa", "Asia", "Africa", "Oceania", "Antartida"]

client = Client("EARTHSCOPE")
osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)
last_peak_by_station = {station["nome"]: -999.0 for station in ESTACOES}


def forma_onda(trace, data):
    """Cria uma forma de onda normalizada com escala fixa entre estacoes."""
    sample_count = min(len(data), 600)
    indices = np.linspace(0, len(data) - 1, sample_count, dtype=int)
    maximum = max(np.max(np.abs(data)), np.finfo(float).eps)
    samples = (data[indices] / maximum).astype(float).tolist()
    return {
        "start_time_utc": trace.stats.starttime.isoformat(),
        "end_time_utc": trace.stats.endtime.isoformat(),
        "sample_rate": float(trace.stats.sampling_rate),
        "samples": samples,
    }


def guardar_formas_onda(waveforms):
    temporary_path = f"{WAVEFORM_LOG}.tmp"
    with open(temporary_path, "w", encoding="utf-8") as waveform_file:
        json.dump(waveforms, waveform_file, separators=(",", ":"))
    os.replace(temporary_path, WAVEFORM_LOG)


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
        centered_data = data - np.mean(data)
        max_abs = max(np.max(np.abs(centered_data)), np.finfo(float).eps)
        normalized = np.abs(centered_data / max_abs)
        sample_rate = trace.stats.sampling_rate

        for index in range(1, len(normalized) - 1):
            is_local_max = normalized[index] > normalized[index - 1] and normalized[index] > normalized[index + 1]
            if is_local_max and normalized[index] > THRESHOLD:
                event_time = trace.stats.starttime + index / sample_rate
                enviar_pico(station, event_time, float(normalized[index]))
        return forma_onda(trace, centered_data), centered_data


def main():
    names = ", ".join(station["nome"] for station in ESTACOES)
    print(f"Orquestra ativa: {names}")
    print(f"A atualizar a cada {INTERVALO_ENTRE_PEDIDOS}s com janelas de {JANELA_SEGUNDOS}s.")
    print("Ctrl+C para parar.\n")

    while True:
        end = UTCDateTime.now()
        start = end - JANELA_SEGUNDOS
        waveforms = {}
        grouped_samples = {continent: [] for continent in CONTINENTES}
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {
                executor.submit(processar_estacao, station, start, end): station
                for station in ESTACOES
            }
            for future in as_completed(futures):
                station = futures[future]
                try:
                    result = future.result()
                    if result:
                        waveform, centered_data = result
                        waveforms[station["nome"]] = waveform
                        grouped_samples[station["continente"]].append(centered_data)
                except Exception as exception:
                    print(f"{station['nome']}: falha ao obter dados ({exception})")
        for continent, station_samples in grouped_samples.items():
            if station_samples:
                shortest = min(len(samples) for samples in station_samples)
                summed = np.sum([samples[:shortest] for samples in station_samples], axis=0)
                aggregate_trace = type("AggregateTrace", (), {"stats": type("Stats", (), {
                    "starttime": start, "endtime": end, "sampling_rate": 1 / (float(end - start) / shortest),
                })()})()
                waveforms[f"continent:{continent}"] = forma_onda(aggregate_trace, summed)
        guardar_formas_onda(waveforms)
        elapsed = float(UTCDateTime.now() - end)
        time.sleep(max(0, INTERVALO_ENTRE_PEDIDOS - elapsed))


if __name__ == "__main__":
    main()
