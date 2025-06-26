import wx


class DisclaimerDialog(wx.Dialog):
    def __init__(self, parent):
        super(DisclaimerDialog, self).__init__(
            parent, title="Aviso Importante - MHC Softwares")

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        disclaimer_text = (
            "Bem-vindo ao Zap Fácil!\n\n"
            "Este software foi desenvolvido para otimizar sua comunicação e produtividade, "
            "automatizando tarefas repetitivas no WhatsApp Web.\n\n"
            "É fundamental que você saiba que a automação de contas de usuário na plataforma "
            "do WhatsApp é contra os Termos de Serviço da Meta. O uso desta ferramenta para "
            "fins de envio de spam, mensagens em massa não solicitadas ou qualquer outra "
            "atividade que viole as políticas do WhatsApp pode resultar no bloqueio temporário "
            "ou permanente do seu número de telefone.\n\n"
            "A MHC Softwares não se responsabiliza por qualquer uso indevido da ferramenta ou "
            "por quaisquer consequências decorrentes, incluindo o bloqueio de contas.\n\n"
            "Use com moderação e responsabilidade."
        )

        st_text = wx.StaticText(self, label=disclaimer_text)
        st_text.Wrap(480)  # Quebra de linha automática
        main_sizer.Add(st_text, 0, wx.ALL, 15)

        line = wx.StaticLine(self)
        main_sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        self.cb_agree = wx.CheckBox(
            self, label="Eu li, entendo e aceito os riscos e termos de uso.")
        main_sizer.Add(self.cb_agree, 0, wx.ALL, 15)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_accept = wx.Button(self, wx.ID_OK, label="Continuar")
        self.btn_accept.Disable()  # Começa desabilitado
        btn_exit = wx.Button(self, wx.ID_CANCEL, label="Sair")

        btn_sizer.Add(btn_exit, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.btn_accept, 0)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 15)

        self.SetSizerAndFit(main_sizer)

        # Binds
        self.cb_agree.Bind(wx.EVT_CHECKBOX, self.OnCheckbox)

    def OnCheckbox(self, event):
        self.btn_accept.Enable(event.IsChecked())
