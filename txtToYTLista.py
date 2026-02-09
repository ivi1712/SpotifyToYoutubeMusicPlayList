import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

# Configuración
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
CLIENT_SECRETS_FILE = "client_secret.json" # Tu archivo de credenciales descargado de Google

def autenticar_youtube():
    # Realiza la autenticación OAuth 2.0
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=0)
    return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def crear_playlist(youtube, nombre, descripcion):
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
          "snippet": {
            "title": nombre,
            "description": descripcion
          },
          "status": {
            "privacyStatus": "private" # O 'public' / 'unlisted'
          }
        }
    )
    response = request.execute()
    return response["id"]

def agregar_video_a_playlist(youtube, playlist_id, video_id, mis_videos_set):
    try:
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        )
        response = request.execute()
        print(f"Video {video_id} agregado correctamente.")
        #si se agrega correctamente elimina el video_id de una variable para luego imprimir en un txt los que no se podiddo añadir
        mis_videos_set.discard(video_id)
        
    except Exception as e:
        print(f"Error agregando video {video_id}: {e}")

# --- EJECUCIÓN PRINCIPAL ---
def leer_ids_desde_txt(archivo_entrada):
    ids_encontrados = []

    try:
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            print(f"--- Leyendo {len(lineas)} líneas del archivo... ---")

            for linea in lineas:
                video_id = linea.strip()
                if video_id:
                    ids_encontrados.append(video_id)

        if ids_encontrados:
            print(f"✅ Éxito. Se leyeron {len(ids_encontrados)} IDs.")
            return ids_encontrados
        else:
            print("⚠️ El archivo no contiene IDs.")
            return []

    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{archivo_entrada}'.")
        return []

# EJECUCIÓN


if __name__ == "__main__":
    # 1. Lista de IDs de videos que quieres meter en la playlist
    exit = True
    while exit:
        
        #añade un pequeño menu con la opcion de poder recueprar la lista o crear nueva
        opcion = input("¿Quieres (1) crear una nueva playlist o (2) recuperar una existente? (1/2): ").strip()
        if opcion == '2':
            playlist_id = input("Introduce el ID de la playlist que quieres recuperar: ").strip()
        archivo_entrada = input("Introduce el nombre del archivo de entrada (por ejemplo, lista_videos.txt): ")
        mis_videos = leer_ids_desde_txt(archivo_entrada)
        mis_videos_set = set(mis_videos)  # Para seguimiento de cuáles se agregan o no
        nombre_sin_extension = archivo_entrada.removesuffix(".txt")
        #pedir el nombre de la lista que va a crear
        if opcion == '1':
            nombre_lista = input("Introduce el nombre de la playlist que se va a crear: ").strip()
        try:
            # 2. Conectarse a YouTube
            yt = autenticar_youtube()
            
            # 3. Crear la nueva lista
            
            if opcion == '1':
                playlist_id = crear_playlist(yt, nombre_lista, "Spotify to YouTube Playlist")
                print(f"Playlist creada con ID: {playlist_id}")
            
            # 4. Meter los videos en la lista
            for vid in mis_videos:
                agregar_video_a_playlist(yt, playlist_id, vid, mis_videos_set)
                
            print("¡Proceso terminado!")
            
        except FileNotFoundError:
            print("Error: No se encontró el archivo 'client_secret.json'. Necesitas credenciales de Google.")
        
        # Escribir en un archivo, nombre archivo orignal + restantes, los videos que no se pudieron agregar (si es que hubo alguno)
        if mis_videos_set:
            print("\n⚠️ No se pudieron agregar los siguientes videos (posiblemente ya estaban en la playlist o hubo otro error):")
            with open(f"{nombre_sin_extension}_no_agregados.txt", 'w', encoding='utf-8') as f:
                for vid in mis_videos_set:
                    f.write(vid + "\n")


        respuesta = input("¿Quieres procesar otro archivo? (s/n): ").strip().lower()
        if respuesta != 's':
            exit = False