# config_manager.py (Versão Padronizada)
import os
import configparser
from pathlib import Path
from cryptography.fernet import Fernet
import constants as C

# --- CAMINHOS E DIRETÓRIOS ---
CONFIG_DIR = Path(os.getenv("APPDATA")) / \
    C.CONFIG_DIR_COMPANY / C.CONFIG_DIR_APP
CONFIG_PATH = CONFIG_DIR / C.CONFIG_FILENAME
SECURE_DATA_PATH = CONFIG_DIR / C.SECURE_FILENAME
MASTER_KEY_PATH = CONFIG_DIR / C.MASTER_KEY_FILENAME


def _ensure_config_dir():
    """Garante que o diretório de configuração exista."""
    os.makedirs(CONFIG_DIR, exist_ok=True)

# --- LÓGICA PARA CONFIG.INI (NÃO SENSÍVEL) ---


def _load_general_config():
    """Carrega o arquivo config.ini e retorna um objeto ConfigParser."""
    _ensure_config_dir()
    config = configparser.ConfigParser()
    if CONFIG_PATH.exists():
        config.read(CONFIG_PATH, encoding="utf-8")
    return config


def _save_general_config(config):
    """Salva o objeto ConfigParser no arquivo config.ini."""
    _ensure_config_dir()
    with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
        config.write(config_file)


def save_setting(section, key, value):
    """Salva uma configuração geral no config.ini."""
    config = _load_general_config()
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, key, str(value))
    _save_general_config(config)


def get_setting(section, key, fallback=None):
    """Pega um valor de uma configuração geral do config.ini."""
    config = _load_general_config()
    return config.get(section, key, fallback=fallback)


def get_section(section_name):
    """Retorna um dicionário com todas as configurações de uma seção do config.ini."""
    config = _load_general_config()
    if config.has_section(section_name):
        return dict(config.items(section_name))
    return {}


# --- LÓGICA PARA LICENSE.KEY (SENSÍVEL) ---

def _get_or_generate_master_key():
    """Carrega a chave de criptografia mestra ou gera uma nova se não existir."""
    _ensure_config_dir()
    if MASTER_KEY_PATH.exists():
        with open(MASTER_KEY_PATH, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(MASTER_KEY_PATH, "wb") as key_file:
            key_file.write(key)
        return key


def save_license_key(license_string: str):
    """
    Criptografa e salva a string da licença no arquivo seguro.
    """
    if not isinstance(license_string, str):
        raise TypeError("A chave de licença deve ser uma string.")

    master_key = _get_or_generate_master_key()
    f = Fernet(master_key)

    encrypted_license = f.encrypt(license_string.encode("utf-8"))

    with open(SECURE_DATA_PATH, "wb") as data_file:
        data_file.write(encrypted_license)
    return True


def get_license_key():
    """
    Descriptografa e retorna a string da licença do arquivo seguro.
    Retorna None se não houver licença ou se o arquivo estiver corrompido.
    """
    if not SECURE_DATA_PATH.exists():
        return None

    master_key = _get_or_generate_master_key()
    f = Fernet(master_key)

    try:
        with open(SECURE_DATA_PATH, "rb") as data_file:
            encrypted_license = data_file.read()

        decrypted_license = f.decrypt(encrypted_license).decode("utf-8")
        return decrypted_license
    except Exception:
        # Erro na descriptografia (chave mestra mudou, arquivo corrompido, etc.)
        return None

# --- FUNÇÕES LEGADAS (Mantidas para compatibilidade) ---


def is_disclaimer_accepted():
    """Verifica especificamente se o disclaimer foi aceito."""
    return get_setting("General", "disclaimer_accepted", "false").lower() == "true"


def save_settings(settings_dict):
    """
    Mescla um dicionário de configurações na seção 'General' do config.ini.
    """
    for key, value in settings_dict.items():
        save_setting("General", key, value)
    return True
