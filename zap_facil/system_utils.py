import sys
import os
import winreg

# Nome que aparecerá no Gerenciador de Tarefas > Inicializar
APP_NAME = "Zap Facil - MHC Softwares"

# O caminho para o nosso .exe quando estiver compilado
PATH_TO_EXE = sys.executable

# A chave do registro do Windows onde as configurações de inicialização do usuário ficam
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_run_key():
    """Abre a chave do registro 'Run' com permissão de escrita."""
    return winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_ALL_ACCESS)


def add_to_startup():
    """Adiciona o programa à inicialização do Windows."""
    try:
        key = _get_run_key()
        # Cria um novo valor no registro: nome do app = caminho para o .exe
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, PATH_TO_EXE)
        winreg.CloseKey(key)
        print(f"'{APP_NAME}' adicionado à inicialização.")
        return True
    except Exception as e:
        print(f"Falha ao adicionar à inicialização: {e}")
        return False


def remove_from_startup():
    """Remove o programa da inicialização do Windows."""
    try:
        key = _get_run_key()
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        print(f"'{APP_NAME}' removido da inicialização.")
        return True
    except FileNotFoundError:
        # O valor não existia, o que não é um erro.
        print(f"'{APP_NAME}' já não estava na inicialização.")
        return True
    except Exception as e:
        print(f"Falha ao remover da inicialização: {e}")
        return False


def is_in_startup():
    """Verifica se o programa já está configurado para iniciar com o sistema."""
    try:
        key = _get_run_key()
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False
