# functions.py
import os
import sys
import random
import time
import json
import threading
import re
from datetime import datetime
from pathlib import Path

import wx
import openpyxl
import numpy as np
import sounddevice as sd
import soundfile as sf
import noisereduce as nr
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from locators import *
import constants as C
import config_manager


class WhatsAppBot:
    def __init__(self, ui):
        self.ui = ui
        self.driver = None
        self.running = False
        self.paused = False
        self.is_recording = False
        self.recorded_frames = []
        self.temp_audio_path = Path(
            os.getenv("TEMP")) / C.TEMP_AUDIO_FILENAME
        self.samplerate = C.AUDIO_SAMPLERATE
        self.channels = C.AUDIO_CHANNELS
        self.dtype = C.AUDIO_DTYPE

        self.main_app_dir = Path(os.path.expanduser(
            "~")) / "Desktop" / C.APP_DATA_DIR_NAME
        self.reports_dir = self.main_app_dir / C.REPORTS_SUBDIR_NAME
        os.makedirs(self.reports_dir, exist_ok=True)

        self.scheduler = None
        self.schedule_job = None

    def initialize_scheduler(self):
        self.ui.log_message(
            "[INFO] Inicializando o módulo de agendamento...", C.THEME_COLORS["accent_purple"])
        self.scheduler = BackgroundScheduler(
            daemon=True, timezone="America/Sao_Paulo")
        self.scheduler.start()
        self.load_and_reschedule_job()

    def get_reports(self):
        try:
            if not os.path.exists(self.reports_dir):
                return []
            files = [f for f in os.listdir(
                self.reports_dir) if f.endswith(".txt")]
            return sorted(files, reverse=True)
        except Exception as e:
            self.ui.log_message(
                f"[ERRO] Falha ao listar relatórios: {e}", "red")
            return []

    def get_report_content(self, filename):
        try:
            with open(self.reports_dir / filename, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.ui.log_message(
                f"[ERRO] Falha ao ler o relatório '{filename}': {e}", "red")
            return "Não foi possível carregar o conteúdo do relatório."

    def delete_report(self, filename):
        try:
            os.remove(self.reports_dir / filename)
            self.ui.log_message(
                f"[RELATÓRIO] Arquivo '{filename}' excluído.", "lightgreen")
            return True
        except Exception as e:
            self.ui.log_message(
                f"[ERRO] Falha ao excluir o relatório '{filename}': {e}", "red")
            return False

    def _format_phone_number(self, phone):
        if not phone:
            return ""
        phone_digits = re.sub(r"\D", "", str(phone))
        if phone_digits.startswith(C.PHONE_COUNTRY_CODE) and len(phone_digits) > 11:
            return phone_digits
        return f"{C.PHONE_COUNTRY_CODE}{phone_digits}"

    def _execute_scheduled_collection(self):
        self.ui.log_message(
            "[AGENDADOR] Disparando campanha de cobrança...", C.THEME_COLORS["accent_purple"])
        settings = config_manager.get_section("schedule_collection")
        if not self.driver or not self.is_whatsapp_ready():
            self.ui.log_message(
                "[AGENDADOR] WhatsApp não conectado. Tentando na próxima vez.", "orange")
            return
        campaign_config = {"source_type": C.SourceType.LIST, "contact_list_path": settings.get(
            "filepath"), "message": settings.get("message"), "image_pdf_path": settings.get("attachment"), "audio_path": None}
        if not campaign_config["contact_list_path"] or not os.path.exists(campaign_config["contact_list_path"]):
            self.ui.log_message(
                "[AGENDADOR] Arquivo de cobrança não encontrado.", "red")
            return
        threading.Thread(target=self.start_campaign, args=(
            campaign_config,), daemon=True).start()

    def load_and_reschedule_job(self):
        if not self.scheduler:
            return
        settings = config_manager.get_section("schedule_collection")
        if settings.get("enabled", "false").lower() == "true":
            if self.schedule_job:
                self.schedule_job.remove()
            try:
                hour, minute = map(int, settings.get(
                    "time", "09:00").split(":"))
                days_of_week = settings.get("days_of_week", "mon-fri")
                self.schedule_job = self.scheduler.add_job(self._execute_scheduled_collection, trigger=CronTrigger(
                    day_of_week=days_of_week, hour=hour, minute=minute))
                self.ui.log_message(
                    f"[AGENDADOR] Tarefa programada para {hour:02d}:{minute:02d} em '{days_of_week}'.", C.THEME_COLORS["accent_purple"])
            except Exception as e:
                self.ui.log_message(
                    f"[AGENDADOR] Erro ao programar: {e}", "red")

    def save_schedule_settings(self, settings_dict):
        for key, value in settings_dict.items():
            config_manager.save_setting("schedule_collection", key, str(value))
        self.load_and_reschedule_job()
        if settings_dict.get("enabled", "false").lower() == "false" and self.schedule_job:
            self.schedule_job.remove()
            self.schedule_job = None
            self.ui.log_message(
                "[AGENDADOR] Agendamento desativado.", "orange")

    def load_schedule_settings(self):
        return config_manager.get_section("schedule_collection")

    def is_whatsapp_ready(self):
        if not self.driver:
            return False
        try:
            WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, MAIN_PANEL)))
            return not self.driver.find_elements(By.CSS_SELECTOR, QR_CODE_CANVAS)
        except:
            return False

    def shutdown(self):
        self.ui.log_message("[INFO] Encerrando o agendador...", "orange")
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
        self.stop()
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.ui.log_message(f"Erro ao fechar navegador: {e}", "orange")
        self.discard_recorded_audio()
        if self.ui and hasattr(self.ui, "on_bot_shutdown"):
            wx.CallAfter(self.ui.on_bot_shutdown)

    def _handle_disconnection(self):
        self.ui.log_message(
            "[ALERTA] Conexão com o WhatsApp perdida!", "orange")
        self.ui.log_message(
            "[INFO] Pausando e tentando reconectar...", "yellow")
        for i in range(C.RECONNECT_ATTEMPTS):
            if not self.running:
                return False
            self.ui.log_message(
                f"[INFO] Tentativa {i + 1}/{C.RECONNECT_ATTEMPTS}. Aguardando {C.RECONNECT_WAIT_SECONDS}s...", "gray")
            time.sleep(C.RECONNECT_WAIT_SECONDS)
            if self.is_whatsapp_ready():
                self.ui.log_message(
                    "[SUCESSO] Conexão reestabelecida! Retomando...", "lightgreen")
                return True
        self.ui.log_message(
            "[FALHA] Não foi possível reconectar. Abortando campanha.", "red")
        return False

    def _process_audio(self, audio_data):
        self.ui.log_message("[ÁUDIO] Aplicando melhorias...", "lightblue")
        reduced_noise = nr.reduce_noise(y=audio_data, sr=self.samplerate)
        peak = np.max(np.abs(reduced_noise))
        normalized = reduced_noise / peak if peak > 0 else reduced_noise
        self.ui.log_message(
            "[ÁUDIO] Qualidade de áudio aprimorada!", "lightgreen")
        return normalized

    def start_recording(self):
        if self.is_recording:
            return
        self.is_recording = True
        self.recorded_frames = []
        self.ui.log_message("[ÁUDIO] Gravação iniciada...", "lightblue")
        threading.Thread(target=self._record_audio_thread, daemon=True).start()

    def _record_audio_thread(self):
        try:
            with sd.InputStream(samplerate=self.samplerate, channels=self.channels, dtype=self.dtype, callback=self._audio_callback):
                while self.is_recording:
                    sd.sleep(100)
        except Exception as e:
            self.ui.log_message(f"[ERRO] Microfone indisponível: {e}", "red")
            self.is_recording = False
            if hasattr(self.ui, "on_recording_error"):
                wx.CallAfter(self.ui.on_recording_error)

    def _audio_callback(self, indata, frames, time, status):
        if status:
            self.ui.log_message(f"[AVISO] Status do áudio: {status}", "orange")
        self.recorded_frames.append(indata.copy())

    def stop_recording(self):
        if not self.is_recording:
            return None
        self.is_recording = False
        self.ui.log_message(
            "[ÁUDIO] Gravação finalizada. Processando...", "lightblue")
        time.sleep(0.5)
        if not self.recorded_frames:
            self.ui.log_message("[ERRO] Nenhuma amostra gravada.", "red")
            return None
        try:
            raw_recording = np.concatenate(self.recorded_frames, axis=0)
            processed_audio = self._process_audio(raw_recording.flatten())
            sf.write(self.temp_audio_path, processed_audio, self.samplerate)
            self.ui.log_message(
                "[SUCESSO] Áudio processado e salvo.", "lightgreen")
            return str(self.temp_audio_path)
        except Exception as e:
            self.ui.log_message(f"[ERRO] Falha ao processar áudio: {e}", "red")
            return None

    def play_recorded_audio(self):
        if not self.temp_audio_path.exists():
            self.ui.log_message("[ERRO] Nenhum áudio gravado.", "red")
            return
        threading.Thread(target=self._play_audio_thread, daemon=True).start()

    def _play_audio_thread(self):
        try:
            wx.CallAfter(self.ui.set_playback_buttons_state, True)
            wx.CallAfter(self.ui.log_message,
                         "[ÁUDIO] Reproduzindo...", "lightblue")
            data, fs = sf.read(self.temp_audio_path, dtype="float32")
            sd.play(data, fs)
            sd.wait()
            wx.CallAfter(self.ui.log_message,
                         "[ÁUDIO] Reprodução finalizada.", "lightblue")
        except Exception as e:
            wx.CallAfter(self.ui.log_message,
                         f"[ERRO] Falha ao reproduzir: {e}", "red")
        finally:
            if hasattr(self.ui, "set_playback_buttons_state"):
                wx.CallAfter(self.ui.set_playback_buttons_state, False)

    def discard_recorded_audio(self):
        self.recorded_frames = []
        if self.temp_audio_path.exists():
            try:
                os.remove(self.temp_audio_path)
                self.ui.log_message(
                    "[INFO] Gravação temporária descartada.", "orange")
                return True
            except OSError as e:
                self.ui.log_message(
                    f"[ERRO] Falha ao apagar áudio: {e}", "red")
                return False
        return True

    def _open_chat_by_name(self, name):
        try:
            self.ui.log_message(f"[INFO] Procurando por: '{name}'...")
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, CHAT_SEARCH_INPUT)))
            search_box.clear()
            search_box.send_keys(name)
            result_selector = CHAT_SEARCH_RESULT_BY_TITLE.format(name=name)
            target_chat = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, result_selector)))
            self.driver.execute_script("arguments[0].click();", target_chat)
            WebDriverWait(self.driver, 5).until(
                lambda driver: self.get_open_contact_name() == name)
            self.ui.log_message(
                f"[INFO] Conversa '{name}' aberta.", "lightgreen")
            return True
        except TimeoutException:
            self.ui.log_message(
                f"[AVISO] Conversa '{name}' não encontrada.", "orange")
            try:
                self.driver.find_element(
                    By.CSS_SELECTOR, CHAT_SEARCH_INPUT).send_keys(Keys.ESCAPE)
            except:
                pass
            return False
        except Exception as e:
            self.ui.log_message(
                f"[ERRO] Falha ao abrir a conversa '{name}': {e}", "red")
            return False

    def _load_contact_list_from_file(self, file_path):
        if not file_path or not os.path.exists(file_path):
            self.ui.log_message(
                "[ERRO] Arquivo de lista não encontrado.", "red")
            return []
        contacts = []
        try:
            if Path(file_path).suffix.lower() == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    contacts = [self._format_phone_number(
                        line.strip()) for line in f if line.strip()]
            elif Path(file_path).suffix.lower() == ".xlsx":
                sheet = openpyxl.load_workbook(file_path).active
                for row in sheet.iter_rows(min_row=1, values_only=True):
                    if row and row[0]:
                        contacts.append(self._format_phone_number(row[0]))
            self.ui.log_message(
                f"[INFO] {len(contacts)} contatos carregados de '{Path(file_path).name}'.")
            return contacts
        except Exception as e:
            self.ui.log_message(
                f"[ERRO] Falha ao ler o arquivo de lista: {e}", "red")
            return []

    def _attach_file(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return True
        try:
            attach_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ATTACH_CLIP_BUTTON)))
            self.driver.execute_script("arguments[0].click();", attach_button)
            is_image_video = Path(file_path).suffix.lower() in [
                ".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webp"]
            input_selector = ATTACH_IMAGE_INPUT if is_image_video else ATTACH_DOCUMENT_INPUT
            attach_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, input_selector)))
            attach_input.send_keys(os.path.abspath(file_path))
            send_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, SEND_ATTACHMENT_BUTTON)))
            self.driver.execute_script("arguments[0].click();", send_button)
            WebDriverWait(self.driver, 30).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, SEND_ATTACHMENT_BUTTON)))
            self.ui.log_message(
                f"[INFO] Anexo '{Path(file_path).name}' enviado.", "lightgreen")
            return True
        except Exception as e:
            self.ui.log_message(f"[ERRO] Falha ao anexar arquivo: {e}", "red")
            try:
                self.driver.find_element(
                    By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except:
                pass
            return False

    def send_text_message(self, message):
        if not message or not message.strip():
            return True
        try:
            text_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, MAIN_TEXT_BOX))
            )
            # 1. Clica na caixa de texto para garantir o foco
            text_box.click()
            time.sleep(0.5)

            # 2. Digita a mensagem caractere por caractere
            for char in message:
                if char == '\n':
                    # Simula Shift+Enter para quebra de linha
                    text_box.send_keys(Keys.SHIFT, Keys.ENTER)
                else:
                    text_box.send_keys(char)
                # Pausa aleatória minúscula entre as teclas para simular digitação
                time.sleep(random.uniform(0.05, 0.15))

            # 3. Aguarda e clica no botão de enviar
            send_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, SEND_MESSAGE_BUTTON))
            )
            send_button.click()

            self.ui.log_message(
                "[INFO] Mensagem de texto enviada.", "lightgreen")
            return True

        except Exception as e:
            self.ui.log_message(f"[ERRO] Falha ao enviar texto: {e}", "red")
            return False

    def start_campaign(self, campaign_config):
        self.running = True
        self.ui.update_buttons_for_running(True)
        self.ui.log_message("[CAMPANHA] MODO CAMPANHA ATIVADO.", "yellow")
        report_data = []
        start_time = datetime.now()
        source_type = campaign_config.get("source_type")
        message = campaign_config.get("message", "")
        image_pdf_path = campaign_config.get("image_pdf_path")
        audio_path = campaign_config.get("audio_path")
        contacts_to_process = []
        if source_type in [C.SourceType.LIST, C.SourceType.GROUP_LIST]:
            contacts_to_process = self._load_contact_list_from_file(
                campaign_config.get("contact_list_path"))
        elif source_type == C.SourceType.MANUAL_LIST:
            manual_contacts = campaign_config.get("manual_contacts", [])
            contacts_to_process = [(name, self._format_phone_number(
                number)) for name, number in manual_contacts]
        if not contacts_to_process:
            self.ui.log_message("[ERRO] Lista de contatos vazia.", "red")
            self.stop()
            return
        total = len(contacts_to_process)
        success_count = 0
        fail_count = 0
        for i, contact_info in enumerate(contacts_to_process):
            if not self.running:
                report_data.append("\nCampanha interrompida.")
                break
            while self.paused:
                time.sleep(1)
            if not self.is_whatsapp_ready() and not self._handle_disconnection():
                report_data.append("\nCampanha abortada por falha de conexão.")
                break
            identifier, manual_name = (
                contact_info[1], contact_info[0]) if source_type == C.SourceType.MANUAL_LIST else (contact_info, "")
            self.ui.log_message(
                f"--- Processando {i + 1}/{total}: {identifier} ---", "lightblue")
            try:
                chat_opened, contact_name_for_msg = False, ""
                if source_type in [C.SourceType.LIST, C.SourceType.MANUAL_LIST]:
                    # Passa a mensagem aqui
                    if self.send_message_to_contact(identifier, message):
                        chat_opened = True
                        time.sleep(1)
                        contact_name_for_msg = manual_name or self.get_open_contact_name()
                elif source_type == C.SourceType.GROUP_LIST:
                    chat_opened = self._open_chat_by_name(identifier)
                    contact_name_for_msg = identifier

                if not chat_opened:
                    self.ui.log_message(
                        f"[FALHA] Não foi possível abrir conversa com '{identifier}'.", "red")
                    fail_count += 1
                    report_data.append(
                        f"Destinatário: {identifier}\tStatus: FALHA\tMotivo: Contato/Grupo inválido.")
                    continue

                # O envio do texto agora é feito dentro de send_message_to_contact
                # Apenas os anexos são enviados depois
                final_message = message.replace("@Nome", contact_name_for_msg.split(",")[
                                                0]) if "@Nome" in message and contact_name_for_msg else message.replace("@Nome,", "").replace("@Nome", "")

                # A lógica de envio de texto foi movida para send_message_to_contact, então o reenvio aqui foi removido
                # e o resultado é determinado pela abertura da conversa.
                image_success = self._attach_file(image_pdf_path)
                audio_success = self._attach_file(audio_path)

                if image_success and audio_success:
                    self.ui.log_message(
                        f"[SUCESSO] Enviado para {identifier}", "lightgreen")
                    success_count += 1
                    report_data.append(
                        f"Destinatário: {identifier}\tStatus: SUCESSO")
                else:
                    self.ui.log_message(
                        f"[AVISO] Mensagem de texto enviada, mas falha ao enviar anexo para {identifier}.", "orange")
                    # Consideramos sucesso se o texto foi, mas o anexo não. Pode ser ajustado.
                    success_count += 1
                    report_data.append(
                        f"Destinatário: {identifier}\tStatus: SUCESSO PARCIAL (texto enviado, anexo falhou)")

            except Exception as e:
                self.ui.log_message(
                    f"[FALHA] Erro crítico com {identifier}: {e}", "red")
                fail_count += 1
                report_data.append(
                    f"Destinatário: {identifier}\tStatus: FALHA\tMotivo: {e}")
            if i < total - 1 and self.running:
                delay = random.uniform(C.MIN_SEND_DELAY, C.MAX_SEND_DELAY)
                self.ui.log_message(f"Aguardando {delay:.1f}s...", "gray")
                time.sleep(delay)
        self.ui.log_message("[CAMPANHA] CAMPANHA FINALIZADA.", "yellow")
        end_time = datetime.now()
        report_filename = self.reports_dir / \
            f"Relatorio_{start_time.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        try:
            with open(report_filename, "w", encoding="utf-8") as f:
                f.write("=" * 50 + "\n")
                f.write(f"{C.REPORT_TITLE}\n")
                f.write("=" * 50 + "\n\n")
                f.write(
                    f"Início: {start_time.strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Fim: {end_time.strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Duração: {end_time - start_time}\n\n")
                f.write(
                    f"Resumo:\n  - Total: {total}\n  - Sucessos: {success_count}\n  - Falhas: {fail_count}\n\n")
                f.write("=" * 50 + "\n")
                f.write(f"{C.REPORT_DETAILS_HEADER}\n")
                f.write("=" * 50 + "\n\n")
                f.write("\n".join(report_data))
            self.ui.log_message(
                f"[RELATÓRIO] Salvo em: {report_filename}", "purple")
        except Exception as e:
            self.ui.log_message(
                f"[ERRO] Falha ao salvar relatório: {e}", "red")
        self.stop()

    def setup_driver(self):
        try:
            base_path = sys._MEIPASS if getattr(
                sys, "frozen", False) else Path(__file__).parent.resolve()
            drivers_path = Path(base_path) / C.DRIVERS_DIR
            chrome_profile_path = os.path.expandvars(
                r"%LOCALAPPDATA%\Google\Chrome\User Data")
            edge_profile_path = os.path.expandvars(
                r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
            if os.path.exists(edge_profile_path):
                browser, user_data, options, driver_exe, ServiceClass = "Edge", edge_profile_path, webdriver.EdgeOptions(
                ), C.EDGE_DRIVER_EXE, EdgeService
            elif os.path.exists(chrome_profile_path):
                browser, user_data, options, driver_exe, ServiceClass = "Chrome", chrome_profile_path, webdriver.ChromeOptions(
                ), C.CHROME_DRIVER_EXE, ChromeService
            else:
                self.ui.log_message(
                    "[ERRO] Perfil do Chrome ou Edge não encontrado.", "red")
                wx.CallAfter(self.ui.on_connection_failed)
                return False
            driver_path = str(drivers_path / driver_exe)
            if not os.path.exists(driver_path):
                self.ui.log_message(
                    f"[ERRO] Driver não encontrado em: {driver_path}", "red")
                wx.CallAfter(self.ui.on_connection_failed)
                return False
            self.ui.log_message(f"[INFO] Usando {browser} com perfil local.")
            options.add_argument(f"--user-data-dir={user_data}")
            options.add_argument("--profile-directory=Default")
            options.add_argument("--start-maximized")
            options.add_experimental_option(
                "excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            service = ServiceClass(executable_path=driver_path)
            self.driver = webdriver.Edge(service=service, options=options) if browser == "Edge" else webdriver.Chrome(
                service=service, options=options)
            self.ui.log_message(f"[INFO] Abrindo WhatsApp Web no {browser}...")
            self.driver.get("https://web.whatsapp.com")
            self.ui.log_message("[INFO] Aguardando conexão do WhatsApp...")
            WebDriverWait(self.driver, 180).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, MAIN_PANEL)))
            self.ui.enable_buttons()
            return True
        except Exception as e:
            self.ui.log_message(
                f"[ERRO CRÍTICO] Falha ao iniciar navegador: {e}", "red")
            if self.ui:
                wx.CallAfter(self.ui.on_connection_failed)
            return False

    def get_open_contact_name(self):
        try:
            return WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, CHAT_HEADER_TITLE))).text
        except:
            return ""

    def send_message_to_contact(self, phone, message):
        try:
            self.driver.get(f"https://web.whatsapp.com/send?phone={phone}")
            # Espera a caixa de texto aparecer para garantir que a página carregou
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, MAIN_TEXT_BOX)))

            # Se uma mensagem foi fornecida, envia ela aqui
            if message:
                # Remove @Nome para envios diretos
                final_message = message.replace("@Nome", "").strip()
                return self.send_text_message(final_message)

            return True  # Retorna sucesso se abriu a conversa mas não tinha mensagem para enviar
        except (TimeoutException, Exception) as e:
            self.ui.log_message(
                f"[ERRO] Não foi possível carregar a conversa com {phone}: {e}", "red")
            return False

    def stop(self):
        if self.running:
            self.running = False
            if self.paused:
                self.paused = False
                self.ui.update_pause_button(False)
            self.ui.update_buttons_for_running(False)

    def toggle_pause(self):
        self.paused = not self.paused
        self.ui.log_message(
            f"[INFO] Campanha {'pausada' if self.paused else 'retomada'}.", "yellow")
        self.ui.update_pause_button(self.paused)
