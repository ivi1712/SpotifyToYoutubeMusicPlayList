import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

# Configuración
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
CLIENT_SECRETS_FILE = "client_secret3.json" # Tu archivo de credenciales descargado de Google

#MAXIMO DE ERRORES PERMITIDOS ANTES DE ABORTAR EL PROCESO
RETRIES = 6
RETRIES_COUNT = 0

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

def agregar_video_a_playlist(youtube, playlist_id, video_id, no_agregados):
    global RETRIES_COUNT
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
        no_agregados.remove(video_id)
        
    except Exception as e:
        print(f"Error agregando video {video_id}: {e}")
        RETRIES_COUNT += 1

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
        raise

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
        no_agregados = list(mis_videos) #se guarda en una lista para no perder el orden original, luego se escribe en un txt al final del proceso
        nombre_no_agregadas = input(f"Introduce el nombre del archivo para no agregadas (deja en blanco para usar '{archivo_entrada.removesuffix('.txt')}'): ").strip()
        if not nombre_no_agregadas:
            nombre_no_agregadas = archivo_entrada.removesuffix(".txt")
            nombre_no_agregadas += "_no_agregados.txt"
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
            count = 0
            for vid in mis_videos:
                old_count = RETRIES_COUNT
                agregar_video_a_playlist(yt, playlist_id, vid, no_agregados)
                new_count = RETRIES_COUNT
                if new_count == old_count:
                    count += 1
                if RETRIES_COUNT >= RETRIES:
                    print(f"⚠️ Se han alcanzado {RETRIES_COUNT} errores. Abortando proceso.")
                    break
                
                
            print("¡Proceso terminado!")
            
        except FileNotFoundError as e:
            print(f"Error: {e}. Abortando ejecución.")
            break
        
        # Escribir en un archivo, nombre archivo orignal + restantes, los videos que no se pudieron agregar (si es que hubo alguno)
        if no_agregados:
            print("\n⚠️ No se pudieron agregar los siguientes videos, posiblemente hay un error con la couta de la API de YouTube:")
            print("\n Prueba a cambiar el client_secret por otro de tu cuenta de Google o espera un rato para que se restablezca la cuota.")
            with open(f"{nombre_no_agregadas}", 'w', encoding='utf-8') as f:
                for vid in no_agregados:
                    f.write(vid + "\n")

        #resumen final del proceso
        print(f"\nResumen del proceso")
        print(f"Total videos procesados: {count}")
        print(f"Videos agregados correctamente: {count - len(no_agregados)}")
        print(f"Id de la playlist creada/recuperada: {playlist_id}")

        respuesta = input("¿Quieres procesar otro archivo? (s/n): ").strip().lower()
        if respuesta != 's':
            exit = False
        else:
            RETRIES_COUNT = 0 #reiniciar contador de errores para el nuevo proceso