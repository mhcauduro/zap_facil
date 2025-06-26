# zap_facil.pyw (Versão Final Refatorada)
import wx
import sys
from ui import ZapFacilUI
from functions import WhatsAppBot
from disclaimer_ui import DisclaimerDialog
# MODIFICADO: Importa a função mais específica 'save_setting'
from config_manager import is_disclaimer_accepted, save_setting


def main():
    """Função principal que controla a inicialização do aplicativo."""
    app = wx.App(False)

    if not is_disclaimer_accepted():
        dialog = DisclaimerDialog(None)
        result = dialog.ShowModal()
        dialog.Destroy()

        if result == wx.ID_OK:
            # Usuário aceitou, salva a configuração e continua
            # MODIFICADO: Usa a função mais clara e específica
            save_setting('General', 'disclaimer_accepted', 'True')
        else:
            # Usuário clicou em Sair ou fechou a janela
            sys.exit(0)

    # Prossiga para a aplicação principal somente se o disclaimer foi aceito
    frame = ZapFacilUI(
        None, title="Zap Fácil - Automação Inteligente para WhatsApp")

    bot_instance = WhatsAppBot(frame)

    # --- CORREÇÃO CRÍTICA APLICADA ---
    # Em vez de atribuir 'frame.bot' diretamente, usamos o método 'set_bot'.
    # Isso garante que a UI inicie corretamente os serviços de background
    # (agendador e conexão do WhatsApp).
    frame.set_bot(bot_instance)

    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
