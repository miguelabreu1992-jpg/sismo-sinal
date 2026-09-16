"""Recebe atividade sismica continuamente e envia os picos para SuperCollider."""

import csv
import os

import numpy as np
from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient
from pythonosc.udp_client import SimpleUDPClient

NETWORK = "IU"
STATION = "MACI"
CHANNEL = "BHZ"
SEEDLINK_URL = "rtserve.iris.washington.edu:18000"

THRESHOLD = 0.01
MIN_GAP_SECONDS = 1.5
MIN_NOTE, MAX_NOTE = 36, 84
OSC_IP = "127.0.0.1"
OSC_PORT = 57120
EVENT_LOG = "sismo_sound_events.csv"

osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)
last_event_time = None


def midi_to_freq(note):
    return 440.0 * (2 ** ((note - 69) / 12.0))


def registar_evento(event_time, amplitude_signal, midi_note, freq, amp):
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


def enviar_pico(event_time, amplitude_signal):
    global last_event_time

    if last_event_time is not None and event_time - last_event_time <= MIN_GAP_SECONDS:
        return

    midi_note = MIN_NOTE + amplitude_signal * (MAX_NOTE - MIN_NOTE)
    midi_note = min(max(midi_note, MIN_NOTE), MAX_NOTE)
    midi_note = round(midi_note)
    freq = midi_to_freq(midi_note)
    amp = min(max(amplitude_signal, 0.1), 0.9)

    osc_client.send_message("/sismo", [float(freq), float(amp)])
    registar_evento(event_time, amplitude_signal, midi_note, freq, amp)
    last_event_time = event_time
    print(f"Pico {event_time} | amplitude={amplitude_signal:.3f} | freq={freq:.1f} Hz")


class SismoClient(EasySeedLinkClient):
    def on_data(self, trace):
        data = trace.data.astype(float)
        if len(data) < 3:
            return

        max_abs = max(np.max(np.abs(data)), np.finfo(float).eps)
        norm = np.abs(data / max_abs)
        sample_rate = trace.stats.sampling_rate

        for index in range(1, len(norm) - 1):
            is_local_max = norm[index] > norm[index - 1] and norm[index] > norm[index + 1]
            if is_local_max and norm[index] > THRESHOLD:
                event_time = trace.stats.starttime + index / sample_rate
                enviar_pico(event_time, float(norm[index]))

    def on_seedlink_error(self):
        print("Erro do servidor SeedLink.")

    def on_seedlink_exception(self, exception):
        print(f"Erro de ligacao SeedLink: {exception}")


def main():
    print(f"A ligar ao fluxo em tempo real: {NETWORK}.{STATION}.{CHANNEL}")
    print(f"Servidor: {SEEDLINK_URL} | Threshold: {THRESHOLD}")
    client = SismoClient(SEEDLINK_URL, autoconnect=False)
    client.conn.timeout = 10
    client.connect()
    client.select_stream(NETWORK, STATION, CHANNEL)
    print("Ligado. A aguardar dados sismicos... Ctrl+C para parar.")
    client.run()


if __name__ == "__main__":
    main()
