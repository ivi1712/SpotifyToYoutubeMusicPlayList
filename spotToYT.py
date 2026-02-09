import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtube_search import YoutubeSearch
import time

# URL de la playlist pública de Spotify
PLAYLIST_URL = input("Introduce la URL de la playlist de Spotify: ")
OUTPUT_FILE = input("Introduce el nombre del archivo de salida (por ejemplo, lista_youtube.txt): ")

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
    
    # 1. Autenticación con Spotify
    try:
        auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, 
                                                client_secret=SPOTIPY_CLIENT_SECRET)
        sp = spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        print(f"Error de autenticación con Spotify: {e}")
        return

    # 2. Obtener canciones de la playlist
    print("Obteniendo canciones de Spotify...")
    try:
        results = sp.playlist_tracks(PLAYLIST_URL)
        tracks = results['items']
        
        # Manejar paginación (si la lista tiene más de 100 canciones)
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
            
        print(f"Se encontraron {len(tracks)} canciones.")
    except Exception as e:
        print(f"Error al leer la playlist. Verifica que sea pública. Detalle: {e}")
        return

    # 3. Buscar en YouTube y guardar
    print(f"Buscando enlaces en YouTube y guardando en {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for index, item in enumerate(tracks):
            try:
                track = item['track']
                if track is None: continue # Saltar tracks vacíos
                
                artist_name = track['artists'][0]['name']
                song_name = track['name']
                
                # Crear término de búsqueda (Ej: "Queen Bohemian Rhapsody audio")
                search_query = f"{artist_name} - {song_name} audio"
                
                # Buscar en YouTube (obtiene el primer resultado)
                yt_results = YoutubeSearch(search_query, max_results=1).to_dict()
                
                if yt_results:
                    video_id = yt_results[0]['id']
                    #video_url = f"https://www.youtube.com/watch?v={video_id}"
                    #video_title = yt_results[0]['title']
                    
                    # Escribir en el archivo
                    #line = f"{video_url} | {artist_name} - {song_name}"
                    f.write(video_id + "\n")
                    
                    print(f"[{index + 1}/{len(tracks)}] Encontrado: {song_name}")
                else:
                    #f.write(f"NO ENCONTRADO | {artist_name} - {song_name}\n")
                    print(f"[{index + 1}/{len(tracks)}] No encontrado: {song_name}")

                # Pequeña pausa para evitar bloqueo por spam
                time.sleep(0.5)

            except Exception as e:
                print(f"Error procesando canción {index + 1}: {e}")

    print("--- ¡Listo! El archivo se ha generado exitosamente. ---")

if __name__ == "__main__":
    main()