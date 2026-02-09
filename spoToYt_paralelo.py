import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtube_search import YoutubeSearch
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random


PLAYLIST_URL = input("Introduce la URL de la playlist de Spotify: ")
OUTPUT_FILE = input("Introduce el nombre del archivo de salida (por ejemplo, lista_youtube.txt): ")

MAX_WORKERS = 8          # prueba 5-12
RETRIES = 3              # reintentos por si YouTube corta
BASE_SLEEP = 0.2         # pequeño jitter para no parecer bot (opcional)

def fetch_tracks(sp, playlist_url: str):
    results = sp.playlist_tracks(playlist_url)
    tracks = results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])
    return tracks

def search_youtube_video_id(artist: str, song: str) -> str | None:
    query = f"{artist} - {song} audio"
    # Reintentos con backoff + jitter
    for attempt in range(RETRIES):
        try:
            # Pequeña pausa aleatoria para repartir peticiones
            time.sleep(BASE_SLEEP + random.random() * 0.25)

            yt_results = YoutubeSearch(query, max_results=1).to_dict()
            if yt_results:
                return yt_results[0].get("id")
            return None
        except Exception:
            # backoff exponencial suave
            time.sleep((2 ** attempt) * 0.5 + random.random() * 0.2)
    return None

def main():

    # --- CONFIGURACIÓN ---
    print("--- Leyendo variables de entorno ---")
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("SPOTIPY_CLIENT_ID="):
                SPOTIPY_CLIENT_ID = line.strip().split("=")[1]
            elif line.startswith("SPOTIPY_CLIENT_SECRET="):
                SPOTIPY_CLIENT_SECRET = line.strip().split("=")[1]



    print("--- Iniciando proceso ---")

    # 1. Spotify auth
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        print(f"Error de autenticación con Spotify: {e}")
        return

    # 2. Obtener canciones
    print("Obteniendo canciones de Spotify...")
    try:
        items = fetch_tracks(sp, PLAYLIST_URL)
        songs = []
        for item in items:
            track = item.get("track")
            if not track:
                continue
            artist = track["artists"][0]["name"]
            name = track["name"]
            songs.append((artist, name))
        print(f"Se encontraron {len(songs)} canciones.")
    except Exception as e:
        print(f"Error al leer la playlist. Verifica que sea pública. Detalle: {e}")
        return

    # 3. Buscar en paralelo
    print(f"Buscando enlaces en YouTube (paralelo) y guardando en {OUTPUT_FILE}...")

    results_by_index = [None] * len(songs)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_index = {
            executor.submit(search_youtube_video_id, artist, song): i
            for i, (artist, song) in enumerate(songs)
        }

        done_count = 0
        for future in as_completed(future_to_index):
            i = future_to_index[future]
            artist, song = songs[i]
            try:
                video_id = future.result()
                results_by_index[i] = video_id
            except Exception as e:
                results_by_index[i] = None
                print(f"Error buscando [{i+1}] {artist} - {song}: {e}")

            done_count += 1
            if results_by_index[i]:
                print(f"[{done_count}/{len(songs)}] OK: {song}")
            else:
                print(f"[{done_count}/{len(songs)}] NO: {song}")

    # 4. Escribir en el mismo orden de la playlist
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for vid in results_by_index:
            if vid:
                f.write(vid + "\n")

    print("--- ¡Listo! Archivo generado. ---")

if __name__ == "__main__":
    main()
