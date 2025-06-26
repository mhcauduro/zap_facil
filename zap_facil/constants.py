# constants.py
# Este arquivo centraliza as constantes e Enums do projeto.

from enum import Enum, auto

# --- ENUMS ---


class SourceType(Enum):
    """Define os tipos de fontes de contato para uma campanha."""
    MANUAL_LIST = auto()
    LIST = auto()
    GROUP_LIST = auto()


class AudioState(Enum):
    """Define os estados possíveis para o controle de áudio."""
    IDLE = auto()      # Nenhum áudio gravado ou pronto
    RECORDING = auto()  # Gravação em andamento
    READY = auto()     # Gravação finalizada e pronta para uso
    PLAYING = auto()   # Áudio gravado sendo reproduzido


# --- GERAL ---
APP_VERSION = "1.0.0"
COMPANY_NAME = "MHC Softwares"
APP_NAME = "Zap Fácil"

# --- ARQUIVOS E DIRETÓRIOS ---
# Diretórios Principais
DRIVERS_DIR = "drivers"
ICONS_DIR = "icons"

# Diretórios de Dados do App
APP_DATA_DIR_NAME = "Zap Fácil"
REPORTS_SUBDIR_NAME = "Relatórios"

# Nomes de Arquivos
APP_ICON_FILENAME = "app_icon.ico"
CLIENT_LOGO_FILENAME = "logo.png"
MIC_ICON_FILENAME = "mic_icon.png"
PLAY_ICON_FILENAME = "play_icon.png"
TEMP_AUDIO_FILENAME = "zapfacil_gravacao.wav"
CHROME_DRIVER_EXE = "chromedriver.exe"
EDGE_DRIVER_EXE = "msedgedriver.exe"

# Constantes para o config_manager
CONFIG_DIR_COMPANY = "MHC Softwares"
CONFIG_DIR_APP = "Zap Fácil"
CONFIG_FILENAME = "config.ini"
SECURE_FILENAME = "license.key"
MASTER_KEY_FILENAME = "master.key"

# --- CONFIGURAções DO BOT ---
RECONNECT_ATTEMPTS = 20
RECONNECT_WAIT_SECONDS = 15
MIN_SEND_DELAY = 5
MAX_SEND_DELAY = 10
PHONE_COUNTRY_CODE = "55"

# --- CONFIGURAÇÕES DE ÁUDIO ---
AUDIO_SAMPLERATE = 44100
AUDIO_CHANNELS = 1
AUDIO_DTYPE = "float32"

# --- MENSAGENS E TEXTOS PADRÃO ---
DEFAULT_CAMPAIGN_MSG = "Olá @Nome, tudo bem?\n\nEsta é uma mensagem de teste do Zap Fácil!"
DEFAULT_SCHEDULE_MSG = "Olá @Nome, tudo bem?\n\nIdentificamos um débito em aberto no valor de @Valor com vencimento em @Vencimento. Para regularizar, utilize o código de barras: @Codigo"
REPORT_TITLE = f"RELATÓRIO DE CAMPANHA - {APP_NAME.upper()}"
REPORT_DETAILS_HEADER = "DETALHES DO ENVIO"

# --- CONFIGURAÇÕES DA INTERFACE (UI) ---
THEME_COLORS = {
    "background": "#2C3E50",
    "panel": "#34495E",
    "text": "#ECF0F1",
    "primary": "#1ABC9C",
    "accent_red": "#E74C3C",
    "accent_yellow": "#F1C40F",
    "accent_purple": "#9B59B6"
}

# Wildcards para Diálogos de Arquivo
WILDCARD_CONTACTS = "Lista de contatos (*.txt;*.xlsx)|*.txt;*.xlsx"
WILDCARD_MEDIA = "Mídia (*.png;*.jpg;*.jpeg;*.gif;*.pdf)|*.png;*.jpg;*.jpeg;*.gif;*.pdf"
WILDCARD_AUDIO = "Áudio (*.mp3;*.ogg;*.wav;*.m4a)|*.mp3;*.ogg;*.wav;*.m4a"
WILDCARD_SCHEDULE = "Arquivo de cobrança (*.xlsx)|*.xlsx"
