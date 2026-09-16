"""Consulta sismos relevantes e transforma novos eventos em notas OSC."""

import csv
import json
import os
import time
import urllib.parse
import urllib.request

from obspy import UTCDateTime
from pythonosc.udp_client import SimpleUDPClient

EVENT_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
JANELA_HORAS = 24
INTERVALO_ENTRE_CONSULTAS = 300
MAGNITUDE_MINIMA = 5.0
MIN_NOTE, MAX_NOTE = 48, 84
OSC_IP = "127.0.0.1"
OSC_PORT = 57120
EVENT_LOG = "notable_events.csv"

osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)
seen_events = set()


def magnitude_to_freq(magnitude):
    note = MIN_NOTE + (min(max(magnitude, MAGNITUDE_MINIMA), 9.0) - MAGNITUDE_MINIMA) * (
        (MAX_NOTE - MIN_NOTE) / (9.0 - MAGNITUDE_MINIMA)
    )
    return 440.0 * (2 ** ((round(note) - 69) / 12.0)), round(note)


def registar_evento(event):
    file_exists = os.path.exists(EVENT_LOG)
    with open(EVENT_LOG, "a", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=[
            "event_id", "event_time_utc", "magnitude", "place", "frequency_hz",
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "event_id": event["id"],
            "event_time_utc": UTCDateTime(event["time_ms"] / 1000).isoformat(),
            "magnitude": event["magnitude"],
            "place": event["place"],
            "frequency_hz": f"{event['frequency']:.3f}",
        })


def obter_eventos():
    end = UTCDateTime.now()
    params = urllib.parse.urlencode({
        "format": "geojson",
        "starttime": str(end - JANELA_HORAS * 3600),
        "endtime": str(end),
        "minmagnitude": MAGNITUDE_MINIMA,
        "orderby": "time",
        "limit": 100,
    })
    with urllib.request.urlopen(f"{EVENT_API}?{params}", timeout=30) as response:
        payload = json.load(response)

    events = []
    for feature in payload.get("features", []):
        properties = feature.get("properties", {})
        magnitude = properties.get("mag")
        if magnitude is None:
            continue
        frequency, note = magnitude_to_freq(float(magnitude))
        events.append({
            "id": feature["id"],
            "time_ms": properties["time"],
            "magnitude": float(magnitude),
            "place": properties.get("place") or "local desconhecido",
            "frequency": frequency,
            "note": note,
        })
    return events


def main():
    print(f"A consultar eventos notaveis (magnitude >= {MAGNITUDE_MINIMA})")
    print(f"Consulta a cada {INTERVALO_ENTRE_CONSULTAS}s. Ctrl+C para parar.\n")

    while True:
        try:
            events = obter_eventos()
            new_events = [event for event in events if event["id"] not in seen_events]
            print(f"Eventos encontrados: {len(events)} | novos: {len(new_events)}")

            for event in new_events:
                seen_events.add(event["id"])
                amplitude = min(max((event["magnitude"] - 4.5) / 4.5, 0.2), 0.9)
                osc_client.send_message("/sismo", [event["frequency"], amplitude])
                registar_evento(event)
                print(
                    f"Evento M{event['magnitude']:.1f} | {event['place']} | "
                    f"nota {event['note']} ({event['frequency']:.1f} Hz)"
                )
                time.sleep(1)

        except Exception as exception:
            print(f"Aviso: falha ao consultar eventos ({exception})")

        time.sleep(INTERVALO_ENTRE_CONSULTAS)


if __name__ == "__main__":
    main()
