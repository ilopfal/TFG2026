import os
import sys
import queue
import threading
import asyncio
import numpy as np
import joblib
import warnings
import time
import scipy.io.wavfile as wavfile
import speech_recognition as sr  
import tkinter as tk            
warnings.filterwarnings("ignore")
from bleak import BleakClient
import sounddevice as sd

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.ole32.CoInitializeEx(None, 0x2)
    except: pass

MAC_ADDRESS = "8C:94:DF:6E:11:56"
UUID_LUCES = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
UUID_PRESION = "d27038e2-6302-421b-851f-506e7a27572d"
UUID_IMU = "cba1d466-344c-4be3-ab3f-189f80dd7518"

NOMBRE_MODELO = 'modelo_final_valencias_90_56.pkl'
NOMBRE_ENCODER = 'label_encoder_valencias90_56.pkl'

FS = 44100  
SEGUNDOS_VENTANA = 10
MUESTRAS_TOTALES = FS * SEGUNDOS_VENTANA
buffer_audio = np.zeros(MUESTRAS_TOTALES, dtype=np.float32)

color_led_virtual = "#000000"
texto_estado_virtual = "Inicializando..."
val_presion_gui = "0"
val_imu_gui = "0.00"
val_motivo_gui = "Esperando..."
val_pilares_gui = "P1: - | P2: - | P3: -"
val_txt_gui = ""

print(" INICIANDO SCRIPT ")

try:
    modelo_svm = joblib.load(NOMBRE_MODELO)
    le = joblib.load(NOMBRE_ENCODER)
    print("Módulo 2: Modelos cargados con éxito.")
except Exception as e:
    print("[ERROR] Archivos pkl: " + str(e)); exit()

reconocedor = sr.Recognizer()
print("Módulo 3: Google Nube activo.")

def pilar3_analisis_texto(texto):
    t = texto.lower()
    if any(w in t for w in ["enfadado", "rabia", "no"]): return "ENFADO"
    if any(w in t for w in ["triste", "llorar", "mal"]): return "TRISTEZA"
    if any(w in t for w in ["bien", "feliz", "alegre"]): return "ALEGRIA"
    return "NEUTRAL"

def pilar1_analisis_matematico(audio_data):
    energia_promedio = np.mean(np.abs(audio_data)) * 150
    amplitud_maxima = np.max(np.abs(audio_data)) * 150
    variabilidad_energia = np.std(np.abs(audio_data)) * 150
    zcr = np.mean(np.diff(np.sign(audio_data)) != 0)
    
    print(f"\nMétricas calculadas -> Energía: {energia_promedio:.2f} | Var: {variabilidad_energia:.2f} | ZCR: {zcr:.3f} | AmpMax: {amplitud_maxima:.2f}")

    if energia_promedio < 0.3: 
        print(f" -> CUMPLIDO: (energia_promedio < 0.3) -> SILENCIO.")
        return "SILENCIO"
        
    if 0.3 <= energia_promedio <= 5.5:
        if (energia_promedio < 4.00 and variabilidad_energia < 12.00) or (variabilidad_energia < 2.00): 
            print(f" -> TRISTEZA -> Voz baja o plana.")
            return "TRISTEZA"
            
        elif variabilidad_energia >= 12.00 and 0.05 <= zcr <= 0.16:
            return "TRISTEZA"
            
        else: 
            print(f" -> Evaluado como NEUTRAL.")
            return "NEUTRAL"
            
    if energia_promedio > 5.5:
        if amplitud_maxima > 80.0 and zcr > 0.18: 
            print(f" -> ENFADO")
            return "ENFADO"
        else: 
            print(f" -> ALEGRIA")
            return "ALEGRIA"
            
    return "NEUTRAL"

def pilar2_predecir_svm(audio_data):
    rms_mean = np.mean(np.sqrt(np.maximum(audio_data**2, 0)))
    rms_std = np.std(np.sqrt(np.maximum(audio_data**2, 0)))
    zcr_mean = np.mean(np.diff(np.sign(audio_data)) != 0)
    
    if rms_std < 0.002 or rms_mean < 0.003:
        return "NEUTRAL"
        
    f0_mean = f0_std = f0_max = 0.0  
    mfcc_means = [rms_mean * (i+1) * 0.1 for i in range(25)]
    features = np.array([rms_mean, rms_std, zcr_mean, f0_mean, f0_std, f0_max, *mfcc_means]).reshape(1, -1)
    try:
        pred_idx = modelo_svm.predict(features)[0]
        return le.classes_[pred_idx].upper()
    except: return "NEUTRAL"

def determinar_emocion_voz(p1, p2, p3):
    if p1 == "SILENCIO": return "NEUTRAL"
    
    ia_emocion = "NEUTRAL"
    if p2 == "POSITIVO" or p2 == "ALEGRIA": ia_emocion = "ALEGRIA"
    elif p2 == "NEGATIVO" or p2 == "TRISTEZA": ia_emocion = "TRISTEZA"
    elif p2 == "ENFADO": ia_emocion = "ENFADO"

    if p1 == ia_emocion: return p1
    if p1 == p3: return p1
    if ia_emocion == p3: return p3

    if p2 == "NEGATIVO" and (p1 == "ENFADO" or p3 == "ENFADO"): return "ENFADO"

    return "NEUTRAL"

def audio_callback(indata, frames, time_info, status):
    global buffer_audio
    buffer_audio = np.roll(buffer_audio, -frames)
    buffer_audio[-frames:] = indata[:, 0]

async def bucle_control(client):
    global color_led_virtual, texto_estado_virtual, val_presion_gui, val_imu_gui, val_motivo_gui, val_pilares_gui, val_txt_gui
    print("\n (Ventana: 10s).")
    texto_estado_virtual = "CALIBRANDO SENSORES..."
    await asyncio.sleep(20)
    
    while True:
        t_inicio = time.time()
        texto_estado_virtual = "ESCUCHANDO..."
        
        audio_data = np.copy(buffer_audio[-MUESTRAS_TOTALES:])
        audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=0.0, neginf=0.0)
        temp_filename = "temp_chunk.wav"
        
        try:
            texto_transcrito = ""
            wavfile.write(temp_filename, FS, (audio_data * 32767).astype(np.int16))
            with sr.AudioFile(temp_filename) as fuente:
                audio_listo = reconocedor.record(fuente)
            try:
                # CORREGIDO: Unificada la cadena del idioma de Google
                texto_transcrito = reconocedor.recognize_google(audio_listo, language="es-ES").strip()
            except: texto_transcrito = ""  
            
            p1 = pilar1_analisis_matematico(audio_data) 
            p2 = pilar2_predecir_svm(audio_data) 
            p3 = pilar3_analisis_texto(texto_transcrito)
            
            emocion_voz = determinar_emocion_voz(p1, p2, p3)
            
            presion_sumada = 0
            movimiento = 0.0
            if client and client.is_connected:
                try:
                    raw_p = await client.read_gatt_char(UUID_PRESION)
                    presion_sumada = int(raw_p.decode())
                    raw_i = await client.read_gatt_char(UUID_IMU)
                    movimiento = float(raw_i.decode())
                except: pass

            val_presion_gui = str(presion_sumada)
            val_imu_gui = f"{movimiento:.2f}"
            val_txt_gui = f'Texto: "{texto_transcrito}"'
            val_pilares_gui = f"Módulos Voz -> P1: {p1} | P2: {p2} | P3: {p3}"

            UMBRAL_PRESION_ALTA = 2650   
            UMBRAL_MOV_SACUDIDA = 180.0  

            emocion_final_absoluta = "NEUTRAL"
            motivo = "Esperando..."

            if emocion_voz == "ENFADO":
                emocion_final_absoluta = "ENFADO"
                color_led_virtual = "#B0A8FF" # Violeta pastel
                motivo = "Voz validada por coincidencia acústica."
                
            elif emocion_voz == "TRISTEZA":
                emocion_final_absoluta = "TRISTEZA"
                color_led_virtual = "#FFD2A8" # Amarillo/Melocotón pastel
                motivo = "Voz validada por coincidencia acústica."
                
            elif emocion_voz == "ALEGRIA":
                emocion_final_absoluta = "ALEGRIA"
                color_led_virtual = "#46FF46" # Verde menta
                motivo = "Interacción positiva confirmada por voz."
                
            else:
                if p2 == "NEGATIVO" and movimiento > UMBRAL_MOV_SACUDIDA:
                    emocion_final_absoluta = "ENFADO"
                    color_led_virtual = "#B0A8FF"
                    motivo = "Filtro acústico negativo y sacudida física."
                    
                elif p2 == "NEGATIVO" and presion_sumada > UMBRAL_PRESION_ALTA and movimiento <= UMBRAL_MOV_SACUDIDA:
                    emocion_final_absoluta = "TRISTEZA"
                    color_led_virtual = "#FFD2A8"
                    motivo = "Filtro acústico negativo y presión alta."
                
                else:
                    if movimiento > UMBRAL_MOV_SACUDIDA:
                        emocion_final_absoluta = "ENFADO"
                        color_led_virtual = "#B0A8FF"
                        motivo = "Movimiento brusco detectado."
                    elif presion_sumada > UMBRAL_PRESION_ALTA and movimiento <= UMBRAL_MOV_SACUDIDA:
                        emocion_final_absoluta = "TRISTEZA"
                        color_led_virtual = "#FFD2A8"
                        motivo = "Filtro físico: Abrazo fuerte o presión."
                    else:
                        # CORREGIDO: Errata de nomenclatura resuelta (terminaba en e)
                        emocion_final_absoluta = "NEUTRAL" 
                        color_led_virtual = "#000000"
                        motivo = "Reposo general o ausencia de patrones."

            texto_estado_virtual = f"EMOCIÓN: {emocion_final_absoluta}"
            val_motivo_gui = motivo
            
            if client and client.is_connected:
                try:
                    orden = "4" if emocion_final_absoluta == "ENFADO" else "1" if emocion_final_absoluta == "TRISTEZA" else "2" if emocion_final_absoluta == "ALEGRIA" else "0"
                    await client.write_gatt_char(UUID_LUCES, orden.encode())
                except: pass

        except Exception as e: print("Error: " + str(e))
        filename_to_remove = temp_filename
        if os.path.exists(filename_to_remove): os.remove(filename_to_remove)
        
        t_procesado = time.time() - t_inicio
        tiempo_espera = max(0.1, 10.0 - t_procesado)
        await asyncio.sleep(tiempo_espera)

def actualizar_gui(root, canvas, label_info, label_pres, label_imu, label_mot, label_pilares, label_txt):
    global color_led_virtual, texto_estado_virtual, val_presion_gui, val_imu_gui, val_motivo_gui, val_pilares_gui, val_txt_gui
    canvas.itemconfig("led_circulo", fill=color_led_virtual)
    label_info.config(text=texto_estado_virtual, fg="#FFFFFF" if color_led_virtual == "#000000" else color_led_virtual)
    
    label_pres.config(text=f"Presión Sensores: {val_presion_gui}")
    label_imu.config(text=f"Movimiento IMU: {val_imu_gui}")
    label_mot.config(text=f"Decisión: {val_motivo_gui}")
    label_pilares.config(text=val_pilares_gui)
    label_txt.config(text=val_txt_gui)
    
    root.after(100, actualizar_gui, root, canvas, label_info, label_pres, label_imu, label_mot, label_pilares, label_txt)

def lanzar_interfaz_leds():
    root = tk.Tk()
    root.title("Simulador de LEDs - Dashboard Central")  
    root.configure(bg="#1E1E1E")
    root.geometry("420x530")  

    label_titulo = tk.Label(root, text="DASHBOARD CONTROL MULTIMODAL", font=("Arial", 11, "bold"), bg="#1E1E1E", fg="#FFFFFF")
    label_titulo.pack(pady=8)

    canvas = tk.Canvas(root, width=160, height=160, bg="#1E1E1E", highlightthickness=0)
    canvas.pack(pady=2)
    canvas.create_oval(10, 10, 150, 150, fill="#000000", outline="#FFFFFF", width=3, tags="led_circulo")

    label_info = tk.Label(root, text="Inicializando...", font=("Arial", 12, "bold"), bg="#1E1E1E", fg="#FFFFFF")
    label_info.pack(pady=5)

    frame_datos = tk.Frame(root, bg="#2A2A2A", bd=2, relief="groove")
    frame_datos.pack(pady=5, fill="x", padx=20)

    label_txt = tk.Label(frame_datos, text='Texto: ""', font=("Arial", 9, "italic"), bg="#2A2A2A", fg="#B0B0B0", anchor="w", justify="left", wraplength=350)
    label_txt.pack(fill="x", padx=10, pady=2)

    label_pilares = tk.Label(frame_datos, text="Módulos Voz -> P1: - | P2: - | P3: -", font=("Arial", 9, "bold"), bg="#2A2A2A", fg="#46FF46", anchor="w")
    label_pilares.pack(fill="x", padx=10, pady=2)

    label_pres = tk.Label(frame_datos, text="Presión Sensores: 0", font=("Arial", 10), bg="#2A2A2A", fg="#E0E0E0", anchor="w")
    label_pres.pack(fill="x", padx=10, pady=3)

    label_imu = tk.Label(frame_datos, text="Movimiento IMU: 0.00", font=("Arial", 10), bg="#2A2A2A", fg="#E0E0E0", anchor="w")
    label_imu.pack(fill="x", padx=10, pady=3)

    label_mot = tk.Label(frame_datos, text="Decisión: Esperando...", font=("Arial", 10, "italic"), bg="#2A2A2A", fg="#FFFFFF", anchor="w", justify="left", wraplength=350)
    label_mot.pack(fill="x", padx=10, pady=3)

    root.after(100, actualizar_gui, root, canvas, label_info, label_pres, label_imu, label_mot, label_pilares, label_txt)
    root.mainloop()

def arrancar_bucle_bluetooth(loop, mac):
    asyncio.set_event_loop(loop)
    async def conectar_y_correr():
        print("Buscando y conectando al peluche: " + mac)
        client = None
        try:
            async with BleakClient(mac, timeout=10.0) as b_client:
                client = b_client
                print("Conexión establecida con el peluche por BLE.")
                with sd.InputStream(samplerate=FS, channels=1, callback=audio_callback):
                    print("Micrófono inicializado correctamente.")
                    await bucle_control(client)
        except Exception as e:
            print("[AVISO] Modo Simulación Local Activo (Sin ESP32): " + str(e))
            with sd.InputStream(samplerate=FS, channels=1, callback=audio_callback):
                print("Micrófono inicializado en entorno local.")
                await bucle_control(None)

    loop.run_until_complete(conectar_y_correr())

if __name__ == "__main__":
    nuevo_loop = asyncio.new_event_loop()
    hilo_ble = threading.Thread(target=arrancar_bucle_bluetooth, args=(nuevo_loop, MAC_ADDRESS), daemon=True)
    hilo_ble.start()
    lanzar_interfaz_leds()
