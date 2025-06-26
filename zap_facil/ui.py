# ui.py
import wx
import wx.adv
import threading
import sys
import os
from pathlib import Path

# --- Módulos do Projeto ---
import system_utils
import config_manager
import constants as C

# --- Funções Auxiliares ---

def resource_path(relative_path):
    """ Retorna o caminho absoluto para um recurso, lidando com o modo de execução (normal ou 'pyinstaller'). """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def get_icon_path(filename):
    """ 
    Busca um ícone na pasta 'icons' de forma segura.
    Retorna o caminho completo se o arquivo existir, senão retorna None.
    """
    if not filename:
        return None
    icon_path = resource_path(os.path.join(C.ICONS_DIR, filename))
    if os.path.exists(icon_path):
        return icon_path
    return None

# --- Classes de Diálogo (ScheduleDialog, ReportsDialog) ---

class ScheduleDialog(wx.Dialog):
    def __init__(self, parent, bot):
        super(ScheduleDialog, self).__init__(
            parent, title="Agendamento de Cobranças", size=(600, 550))
        self.bot = bot
        self.SetBackgroundColour(C.THEME_COLORS["panel"])
        self.SetForegroundColour(C.THEME_COLORS["text"])
        self.InitUI()
        self.BindEvents()
        self._load_schedule_settings()

    def InitUI(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(10, 10)
        self.schedule_enable_check = wx.CheckBox(
            panel, label="Ativar envio automático de cobranças")
        gbs.Add(self.schedule_enable_check, pos=(0, 0),
                span=(1, 4), flag=wx.BOTTOM, border=10)
        gbs.Add(wx.StaticText(panel, label="Horário do Envio:"),
                pos=(1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        self.schedule_time_picker = wx.adv.TimePickerCtrl(
            panel, style=wx.adv.TP_DEFAULT)
        gbs.Add(self.schedule_time_picker, pos=(1, 1),
                flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=20)
        days_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.day_checks = {'mon': wx.CheckBox(panel, label="Seg"), 'tue': wx.CheckBox(panel, label="Ter"), 'wed': wx.CheckBox(panel, label="Qua"), 'thu': wx.CheckBox(
            panel, label="Qui"), 'fri': wx.CheckBox(panel, label="Sex"), 'sat': wx.CheckBox(panel, label="Sáb"), 'sun': wx.CheckBox(panel, label="Dom")}
        for day in self.day_checks.values():
            days_sizer.Add(day, 0, wx.RIGHT, 5)
        gbs.Add(days_sizer, pos=(1, 2), span=(
            1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        gbs.Add(wx.StaticText(panel, label="Arquivo de Cobrança:"), pos=(
            2, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.TOP, border=5)
        self.schedule_file_path = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.schedule_browse_btn = wx.Button(panel, label="Carregar...")
        gbs.Add(self.schedule_file_path, pos=(
            3, 0), span=(1, 3), flag=wx.EXPAND)
        gbs.Add(self.schedule_browse_btn, pos=(3, 3))
        gbs.Add(wx.StaticText(panel, label="Mensagem de Cobrança (use tags como @Nome):"),
                pos=(4, 0), span=(1, 4), flag=wx.TOP, border=5)
        self.schedule_msg = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.schedule_msg.SetValue(C.DEFAULT_SCHEDULE_MSG)
        gbs.Add(self.schedule_msg, pos=(5, 0), span=(1, 4), flag=wx.EXPAND)
        gbs.AddGrowableRow(5)
        gbs.AddGrowableCol(2)
        panel.SetSizer(gbs)
        main_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 15)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.save_btn = wx.Button(self, label="Salvar Agendamento")
        self.cancel_btn = wx.Button(self, label="Cancelar")
        button_sizer.AddStretchSpacer()
        button_sizer.Add(self.cancel_btn, 0, wx.RIGHT, 5)
        button_sizer.Add(self.save_btn, 0, wx.LEFT, 5)
        main_sizer.Add(button_sizer, 0, wx.EXPAND |
                       wx.BOTTOM | wx.RIGHT | wx.LEFT, 15)
        self.SetSizer(main_sizer)
        self.OnToggleScheduleControls(None)

    def BindEvents(self):
        self.schedule_enable_check.Bind(
            wx.EVT_CHECKBOX, self.OnToggleScheduleControls)
        self.schedule_browse_btn.Bind(wx.EVT_BUTTON, self.OnBrowseScheduleFile)
        self.save_btn.Bind(wx.EVT_BUTTON, self.OnSaveSchedule)
        self.cancel_btn.Bind(
            wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_CANCEL))

    def _load_schedule_settings(self):
        settings = self.bot.load_schedule_settings()
        self.schedule_enable_check.SetValue(
            settings.get('enabled', 'false').lower() == 'true')
        try:
            hour, minute = map(int, settings.get('time', '09:00').split(':'))
            self.schedule_time_picker.SetValue(
                wx.DateTime().Set(hour=hour, minute=minute, second=0))
        except:
            pass
        days_of_week = settings.get(
            'days_of_week', 'mon,tue,wed,thu,fri').split(',')
        for code, chk in self.day_checks.items():
            chk.SetValue(code in days_of_week)
        self.schedule_file_path.SetValue(settings.get('filepath', ''))
        self.schedule_msg.SetValue(settings.get(
            'message', C.DEFAULT_SCHEDULE_MSG))
        self.OnToggleScheduleControls(None)

    def OnToggleScheduleControls(self, event):
        is_enabled = self.schedule_enable_check.GetValue()
        for ctrl in [self.schedule_time_picker, self.schedule_file_path, self.schedule_browse_btn, self.schedule_msg, *self.day_checks.values()]:
            ctrl.Enable(is_enabled)

    def OnBrowseScheduleFile(self, event):
        with wx.FileDialog(self, "Escolha o arquivo de cobrança", wildcard=C.WILDCARD_SCHEDULE, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fd:
            if fd.ShowModal() == wx.ID_OK:
                self.schedule_file_path.SetValue(fd.GetPath())

    def OnSaveSchedule(self, event):
        if self.schedule_enable_check.GetValue():
            if not self.schedule_file_path.GetValue():
                wx.MessageBox("Para ativar, selecione um arquivo.",
                              "Erro", wx.OK | wx.ICON_ERROR)
                return
            if not any(c.IsChecked() for c in self.day_checks.values()):
                wx.MessageBox("Para ativar, selecione um dia.",
                              "Erro", wx.OK | wx.ICON_ERROR)
                return
        dt = self.schedule_time_picker.GetValue()
        settings = {'enabled': self.schedule_enable_check.GetValue(), 'time': f"{dt.GetHour():02d}:{dt.GetMinute():02d}", 'days_of_week': ",".join(
            [code for code, chk in self.day_checks.items() if chk.IsChecked()]), 'filepath': self.schedule_file_path.GetValue(), 'message': self.schedule_msg.GetValue(), 'attachment': ''}
        self.bot.save_schedule_settings(settings)
        self.GetParent().log_message(
            "[AGENDADOR] Configurações salvas!", C.THEME_COLORS["accent_purple"])
        self.EndModal(wx.ID_OK)


class ReportsDialog(wx.Dialog):
    def __init__(self, parent, bot):
        super(ReportsDialog, self).__init__(
            parent, title="Relatórios de Campanha", size=(800, 600))
        self.bot = bot
        self.SetBackgroundColour(C.THEME_COLORS["panel"])
        self.SetForegroundColour(C.THEME_COLORS["text"])
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        left_panel = wx.Panel(self)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.report_list = wx.ListBox(left_panel)
        left_sizer.Add(wx.StaticText(
            left_panel, label="Relatórios Gerados:"), 0, wx.ALL, 5)
        left_sizer.Add(self.report_list, 1, wx.EXPAND | wx.ALL, 5)
        left_panel.SetSizer(left_sizer)
        right_panel = wx.Panel(self)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.report_content = wx.TextCtrl(
            right_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.report_content.SetBackgroundColour(C.THEME_COLORS["background"])
        self.report_content.SetForegroundColour(C.THEME_COLORS["text"])
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.delete_btn = wx.Button(right_panel, label="Excluir")
        self.close_btn = wx.Button(right_panel, label="Fechar")
        button_sizer.Add(self.delete_btn, 0, wx.ALL, 5)
        button_sizer.AddStretchSpacer()
        button_sizer.Add(self.close_btn, 0, wx.ALL, 5)
        right_sizer.Add(wx.StaticText(
            right_panel, label="Conteúdo do Relatório:"), 0, wx.ALL, 5)
        right_sizer.Add(self.report_content, 1, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)
        right_panel.SetSizer(right_sizer)
        main_sizer.Add(left_panel, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(right_panel, 2, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(main_sizer)
        self.BindEvents()
        self.RefreshReportList()

    def BindEvents(self):
        self.report_list.Bind(wx.EVT_LISTBOX, self.OnReportSelected)
        self.delete_btn.Bind(wx.EVT_BUTTON, self.OnDeleteReport)
        self.close_btn.Bind(wx.EVT_BUTTON, lambda e: self.Close())

    def RefreshReportList(self):
        self.report_list.Clear()
        reports = self.bot.get_reports()
        if reports:
            self.report_list.InsertItems(reports, 0)
        self.report_content.Clear()
        self.delete_btn.Disable()

    def OnReportSelected(self, e):
        sel = self.report_list.GetStringSelection()
        if sel:
            self.report_content.SetValue(self.bot.get_report_content(sel))
            self.delete_btn.Enable()

    def OnDeleteReport(self, e):
        sel = self.report_list.GetStringSelection()
        if not sel:
            return
        if wx.MessageDialog(self, f"Excluir o relatório '{sel}'?", "Confirmar", wx.YES_NO | wx.ICON_WARNING).ShowModal() == wx.ID_YES:
            if self.bot.delete_report(sel):
                wx.MessageBox("Relatório excluído.", "Sucesso",
                              wx.OK | wx.ICON_INFORMATION)
                self.RefreshReportList()

# --- Classe do Ícone da Barra de Tarefas ---


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        super(TaskBarIcon, self).__init__()
        self.frame = frame
        icon_path = get_icon_path(C.APP_ICON_FILENAME)
        if icon_path:
            self.SetIcon(wx.Icon(icon_path, wx.BITMAP_TYPE_ICO),
                         f"{C.APP_NAME} - {C.COMPANY_NAME}")
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.OnLeftDClick)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(wx.ID_OPEN, "Restaurar")
        menu.AppendSeparator()
        menu.Append(wx.ID_EXIT, "Sair")
        self.Bind(wx.EVT_MENU, self.frame.OnRestore, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.frame.OnExitApp, id=wx.ID_EXIT)
        return menu

    def OnLeftDClick(self, e): self.frame.OnRestore(e)

# --- Classe Principal da UI ---


class ZapFacilUI(wx.Frame):
    def __init__(self, parent, title):
        super(ZapFacilUI, self).__init__(parent, title=title, size=(720, 850))
        self.bot = None
        self._setup_theme()
        self.taskBarIcon = TaskBarIcon(self)
        self.InitUI()
        self._create_menu_bar()
        self.statusBar = self.CreateStatusBar(2)
        self.statusBar.SetStatusWidths([-1, 180])
        self.statusBar.SetStatusText("Aguardando inicialização...", 0)
        self.statusBar.SetStatusText(f"{C.COMPANY_NAME} v{C.APP_VERSION}", 1)
        self.Centre()
        self.SetMinSize(self.GetSize())
        icon_path = get_icon_path(C.APP_ICON_FILENAME)
        if icon_path:
            self.SetIcon(wx.Icon(icon_path, wx.BITMAP_TYPE_ICO))
        self.BindEvents()
        # MODIFICADO: A inicialização dos serviços agora é feita no método set_bot

    def _setup_theme(self):
        self.colors = C.THEME_COLORS
        self.fonts = {"title": wx.Font(16, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD), "label": wx.Font(
            10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD), "main": wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)}

    def InitUI(self):
        panel = wx.Panel(self)
        panel.SetBackgroundColour(self.colors["background"])
        panel.SetFont(self.fonts["main"])
        panel.SetForegroundColour(self.colors["text"])
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        header_sizer = self._create_header(panel)
        self.notebook = self._create_notebook(panel)
        log_sizer = self._create_log_panel(panel)
        control_sizer = self._create_control_panel(panel)
        main_sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 15)
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        main_sizer.Add(log_sizer, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(control_sizer, 0, wx.EXPAND |
                       wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        panel.SetSizer(main_sizer)

    def _create_header(self, parent):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        logo_path = get_icon_path(C.CLIENT_LOGO_FILENAME)
        if logo_path:
            try:
                logo_img = wx.Image(logo_path, wx.BITMAP_TYPE_ANY).Scale(
                    120, 32, wx.IMAGE_QUALITY_HIGH)
                logo_widget = wx.StaticBitmap(
                    parent, wx.ID_ANY, wx.Bitmap(logo_img))
                sizer.Add(logo_widget, 0, wx.RIGHT |
                          wx.ALIGN_CENTER_VERTICAL, 10)
            except wx.WXAssertionError:
                logo_placeholder = wx.Panel(parent, size=(120, 32))
                logo_placeholder.SetBackgroundColour(self.colors["primary"])
                sizer.Add(logo_placeholder, 0, wx.RIGHT |
                          wx.ALIGN_CENTER_VERTICAL, 10)
        else:
            logo_placeholder = wx.Panel(parent, size=(120, 32))
            logo_placeholder.SetBackgroundColour(self.colors["primary"])
            sizer.Add(logo_placeholder, 0, wx.RIGHT |
                      wx.ALIGN_CENTER_VERTICAL, 10)
        title = wx.StaticText(parent, label=C.APP_NAME)
        title.SetFont(self.fonts["title"])
        title.SetForegroundColour(self.colors["primary"])
        self.activity_indicator = wx.ActivityIndicator(parent)
        sizer.Add(title, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.AddStretchSpacer()
        sizer.Add(self.activity_indicator, 0,
                  wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        return sizer

    def _create_content_panel(self, parent):
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(self.colors["panel"])
        sizer = wx.BoxSizer(wx.VERTICAL)
        msg_box = wx.StaticBox(panel, label="Mensagem")
        msg_box.SetForegroundColour(self.colors["primary"])
        msg_sizer = wx.StaticBoxSizer(msg_box, wx.VERTICAL)
        self.campaign_msg = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.campaign_msg.SetValue(C.DEFAULT_CAMPAIGN_MSG)
        msg_sizer.Add(self.campaign_msg, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(msg_sizer, 1, wx.EXPAND | wx.ALL, 10)
        attach_box = wx.StaticBox(panel, label="Anexos")
        attach_box.SetForegroundColour(self.colors["primary"])
        attach_sizer = wx.StaticBoxSizer(attach_box, wx.VERTICAL)
        gbs = wx.GridBagSizer(5, 5)
        self.image_path = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.browse_image_btn = wx.Button(panel, label="Imagem/PDF...")
        gbs.Add(self.image_path, pos=(0, 0),
                flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        gbs.Add(self.browse_image_btn, pos=(0, 1))
        self.audio_path = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.browse_audio_btn = wx.Button(panel, label="Áudio...")
        gbs.Add(self.audio_path, pos=(1, 0), flag=wx.EXPAND |
                wx.ALIGN_CENTER_VERTICAL | wx.TOP, border=5)
        gbs.Add(self.browse_audio_btn, pos=(1, 1), flag=wx.TOP, border=5)
        gbs.Add(wx.StaticLine(panel), pos=(2, 0), span=(1, 2),
                flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=10)
        gbs.Add(wx.StaticText(panel, label="Gravar Áudio na Hora:"),
                pos=(3, 0), span=(1, 2))
        self.record_btn = self._create_button(
            parent=panel, label="Gravar", art_id=wx.ART_TIP, color=self.colors["accent_red"], icon_filename=C.MIC_ICON_FILENAME)
        self.play_btn = self._create_button(
            parent=panel, label="Reproduzir", art_id=wx.ART_GO_FORWARD, icon_filename=C.PLAY_ICON_FILENAME)
        self.discard_btn = self._create_button(
            parent=panel, label="Descartar", art_id=wx.ART_DELETE)
        self.attach_audio_btn = self._create_button(
            parent=panel, label="Anexar", art_id=wx.ART_GO_UP)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.record_btn, 1, wx.EXPAND | wx.RIGHT, 5)
        btn_sizer.Add(self.play_btn, 1, wx.EXPAND | wx.RIGHT, 5)
        btn_sizer.Add(self.discard_btn, 1, wx.EXPAND | wx.RIGHT, 5)
        btn_sizer.Add(self.attach_audio_btn, 1, wx.EXPAND)
        gbs.Add(btn_sizer, pos=(4, 0), span=(1, 2), flag=wx.EXPAND)
        gbs.AddGrowableCol(0)
        attach_sizer.Add(gbs, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(attach_sizer, 0, wx.EXPAND |
                  wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        panel.SetSizer(sizer)
        return panel

    def _create_button(self, parent, label, art_id, color=None, icon_filename=None):
        button = wx.Button(parent, label=label)
        icon_path = get_icon_path(icon_filename)
        bmp = None
        if icon_path:
            try:
                bmp = wx.Bitmap(icon_path, wx.BITMAP_TYPE_ANY)
            except:
                bmp = None
        if bmp:
            button.SetBitmap(bmp)
        else:
            button.SetBitmap(wx.ArtProvider.GetBitmap(
                art_id, wx.ART_BUTTON, (16, 16)))
        if color:
            button.SetBackgroundColour(color)
            button.SetForegroundColour("#FFFFFF")
        return button

    def initiate_automatic_connection(self):
        if not self.bot:
            self.on_connection_failed()
            return
        self.log_message(f"[INFO] Conectando ao WhatsApp...",
                         self.colors["accent_yellow"])
        self._set_status_text("Conectando...")
        self.activity_indicator.Start()
        threading.Thread(target=self.bot.setup_driver, daemon=True).start()

    def _create_menu_bar(self):
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        menu_restore = file_menu.Append(wx.ID_ANY, "&Restaurar\tCtrl+R")
        file_menu.AppendSeparator()
        menu_exit = file_menu.Append(wx.ID_EXIT, "Sai&r\tAlt+F4")
        schedule_menu = wx.Menu()
        menu_schedule_collection = schedule_menu.Append(
            wx.ID_ANY, "&Agendar Cobranças...")
        reports_menu = wx.Menu()
        menu_view_reports = reports_menu.Append(
            wx.ID_ANY, "&Visualizar Relatórios...")
        settings_menu = wx.Menu()
        self.menu_startup = settings_menu.AppendCheckItem(
            wx.ID_ANY, "Iniciar com o Sistema")
        self.menu_startup.Check(config_manager.get_setting(
            'General', 'start_on_boot', 'false').lower() == 'true')
        menu_bar.Append(file_menu, "&Arquivo")
        menu_bar.Append(schedule_menu, "&Agendamentos")
        menu_bar.Append(reports_menu, "&Relatórios")
        menu_bar.Append(settings_menu, "&Configurações")
        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, self.OnRestore, menu_restore)
        self.Bind(wx.EVT_MENU, self.OnExitApp, menu_exit)
        self.Bind(wx.EVT_MENU, self.OnToggleStartup, self.menu_startup)
        self.Bind(wx.EVT_MENU, self.OnViewReports, menu_view_reports)
        self.Bind(wx.EVT_MENU, self.OnShowScheduleDialog,
                  menu_schedule_collection)

    def _create_notebook(self, parent):
        notebook = wx.Notebook(parent)
        notebook.SetBackgroundColour(self.colors["panel"])
        notebook.AddPage(self._create_recipients_panel(
            notebook), "1. Destinatários")
        notebook.AddPage(self._create_content_panel(
            notebook), "2. Mensagem e Anexos")
        return notebook

    def _create_recipients_panel(self, parent):
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(self.colors["panel"])
        sizer = wx.BoxSizer(wx.VERTICAL)
        source_box = wx.StaticBox(panel, label="Fonte dos Contatos")
        source_box.SetForegroundColour(self.colors["primary"])
        source_sizer = wx.StaticBoxSizer(source_box, wx.VERTICAL)
        self.rb_manual = wx.RadioButton(
            panel, label="Adicionar Contatos Manualmente", style=wx.RB_GROUP)
        self.rb_list_numbers = wx.RadioButton(
            panel, label="Usar Lista de Números (.txt/.xlsx)")
        self.rb_list_groups = wx.RadioButton(
            panel, label="Usar Lista de Grupos (.txt/.xlsx)")
        source_sizer.Add(self.rb_manual, 0, wx.BOTTOM, 5)
        source_sizer.Add(self.rb_list_numbers, 0, wx.BOTTOM, 5)
        source_sizer.Add(self.rb_list_groups, 0, wx.BOTTOM, 5)
        sizer.Add(source_sizer, 0, wx.EXPAND | wx.ALL, 10)
        self.manual_panel = self._create_manual_add_panel(panel)
        sizer.Add(self.manual_panel, 1, wx.EXPAND |
                  wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.list_panel = self._create_list_load_panel(panel)
        sizer.Add(self.list_panel, 0, wx.EXPAND |
                  wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        panel.SetSizer(sizer)
        return panel

    def _create_manual_add_panel(self, parent):
        panel = wx.Panel(parent)
        box = wx.StaticBox(panel, label="Contatos Manuais")
        box.SetForegroundColour(self.colors["primary"])
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        input_sizer = wx.GridBagSizer(5, 5)
        input_sizer.Add(wx.StaticText(panel, label="Nome:"),
                        pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        self.manual_name = wx.TextCtrl(panel)
        self.manual_name.SetHint("Ex: João Silva")
        input_sizer.Add(self.manual_name, pos=(0, 1), flag=wx.EXPAND)
        input_sizer.Add(wx.StaticText(panel, label=f"Número ({C.PHONE_COUNTRY_CODE}DDD...):"), pos=(
            1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        self.manual_number = wx.TextCtrl(panel)
        self.manual_number.SetHint("Ex: 5511987654321")
        input_sizer.Add(self.manual_number, pos=(1, 1), flag=wx.EXPAND)
        self.add_contact_btn = wx.Button(panel, label="Adicionar Contato")
        input_sizer.Add(self.add_contact_btn, pos=(2, 1), flag=wx.ALIGN_RIGHT)
        input_sizer.AddGrowableCol(1)
        sizer.Add(input_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.manual_contact_list = wx.ListCtrl(
            panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.manual_contact_list.InsertColumn(0, "Nome", width=250)
        self.manual_contact_list.InsertColumn(1, "Número", width=200)
        sizer.Add(self.manual_contact_list, 1, wx.EXPAND | wx.ALL, 5)
        self.remove_contact_btn = wx.Button(panel, label="Remover Selecionado")
        sizer.Add(self.remove_contact_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        panel.SetSizer(sizer)
        return panel

    def _create_list_load_panel(self, parent):
        panel = wx.Panel(parent)
        box = wx.StaticBox(panel, label="Carregar de Arquivo")
        box.SetForegroundColour(self.colors["primary"])
        sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        self.contact_list_path = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.browse_contacts_btn = wx.Button(panel, label="Carregar Lista...")
        sizer.Add(self.contact_list_path, 1, wx.EXPAND | wx.RIGHT, 5)
        sizer.Add(self.browse_contacts_btn, 0)
        panel.SetSizer(sizer)
        return panel

    def _create_log_panel(self, parent):
        box = wx.StaticBox(parent, label="Histórico de Eventos")
        box.SetForegroundColour(self.colors["primary"])
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.log = wx.TextCtrl(
            parent, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.log.SetBackgroundColour(self.colors["panel"])
        self.log.SetForegroundColour(self.colors["text"])
        sizer.Add(self.log, 1, wx.EXPAND | wx.ALL, 5)
        return sizer

    def _create_control_panel(self, parent):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_campaign_btn = self._create_button(
            parent, "INICIAR CAMPANHA", wx.ART_GO_FORWARD)
        self.parar_btn = self._create_button(
            parent, "Parar", wx.ART_CROSS_MARK)
        self.pausar_btn = self._create_button(parent, "Pausar", wx.ART_PASTE)
        self.minimize_btn = self._create_button(
            parent, "Minimizar", wx.ART_GO_DOWN)
        sizer.Add(self.start_campaign_btn, 2, wx.EXPAND | wx.ALL, 5)
        sizer.AddStretchSpacer(1)
        sizer.Add(self.parar_btn, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.pausar_btn, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.minimize_btn, 0, wx.ALL, 5)
        return sizer

    def BindEvents(self):
        self.minimize_btn.Bind(wx.EVT_BUTTON, self.OnMinimizeToTray)
        self.browse_contacts_btn.Bind(wx.EVT_BUTTON, self.OnBrowseContacts)
        self.browse_image_btn.Bind(wx.EVT_BUTTON, self.OnBrowseImage)
        self.browse_audio_btn.Bind(wx.EVT_BUTTON, self.OnBrowseAudio)
        self.rb_manual.Bind(wx.EVT_RADIOBUTTON, self.OnSourceTypeChange)
        self.rb_list_numbers.Bind(wx.EVT_RADIOBUTTON, self.OnSourceTypeChange)
        self.rb_list_groups.Bind(wx.EVT_RADIOBUTTON, self.OnSourceTypeChange)
        self.add_contact_btn.Bind(wx.EVT_BUTTON, self.OnAddManualContact)
        self.remove_contact_btn.Bind(wx.EVT_BUTTON, self.OnRemoveManualContact)
        self.record_btn.Bind(wx.EVT_BUTTON, self.OnRecordToggle)
        self.play_btn.Bind(wx.EVT_BUTTON, self.OnPlayAudio)
        self.discard_btn.Bind(wx.EVT_BUTTON, self.OnDiscardAudio)
        self.attach_audio_btn.Bind(wx.EVT_BUTTON, self.OnAttachRecordedAudio)
        self.start_campaign_btn.Bind(wx.EVT_BUTTON, self.OnStartCampaign)
        self.parar_btn.Bind(wx.EVT_BUTTON, self.OnParar)
        self.pausar_btn.Bind(wx.EVT_BUTTON, self.OnPausar)
        self.Bind(wx.EVT_CLOSE, self.OnMinimizeToTray)
        self.start_campaign_btn.Enable(False)
        self.parar_btn.Enable(False)
        self.pausar_btn.Enable(False)
        self.update_audio_controls(C.AudioState.IDLE)
        self.OnSourceTypeChange(None)

    # --- NOVO: Método para injetar o bot e iniciar os serviços ---
    def set_bot(self, bot_instance):
        """Define a instância do bot para a UI e inicia os serviços de background."""
        self.bot = bot_instance

        # Agora iniciamos os serviços que dependem do bot
        if self.bot:
            # Inicia o agendador em segundo plano (Otimização de performance)
            threading.Thread(
                target=self.bot.initialize_scheduler, daemon=True).start()

            # Inicia a conexão com o WhatsApp
            wx.CallAfter(self.initiate_automatic_connection)

    def OnShowScheduleDialog(self, e):
        if not self.bot:
            return
        with ScheduleDialog(self, self.bot) as dialog:
            dialog.ShowModal()

    def OnViewReports(self, e):
        if not self.bot:
            return
        with ReportsDialog(self, self.bot) as dialog:
            dialog.ShowModal()

    def OnToggleStartup(self, e):
        is_checked = self.menu_startup.IsChecked()
        if is_checked and system_utils.add_to_startup():
            self.log_message("[INFO] Adicionado à inicialização.")
        elif not is_checked and system_utils.remove_from_startup():
            self.log_message("[INFO] Removido da inicialização.")
        else:
            self.log_message("[ERRO] Falha. Tente como admin.",
                             self.colors["accent_red"])
            self.menu_startup.Check(not is_checked)
            return
        config_manager.save_setting(
            'General', 'start_on_boot', str(is_checked))

    def OnSourceTypeChange(self, e): self.manual_panel.Show(self.rb_manual.GetValue(
    )); self.list_panel.Show(not self.rb_manual.GetValue()); self.Layout()

    def OnAddManualContact(self, e):
        name = self.manual_name.GetValue().strip()
        number = self.manual_number.GetValue().strip()
        if not name or not number:
            wx.MessageBox("Nome e Número são obrigatórios.",
                          "Erro", wx.OK | wx.ICON_ERROR)
            return
        index = self.manual_contact_list.InsertItem(
            self.manual_contact_list.GetItemCount(), name)
        self.manual_contact_list.SetItem(index, 1, number)
        self.manual_name.Clear()
        self.manual_number.Clear()
        self.manual_name.SetFocus()

    def OnRemoveManualContact(self, e):
        idx = self.manual_contact_list.GetFirstSelected()
        if idx != -1:
            self.manual_contact_list.DeleteItem(idx)
        else:
            wx.MessageBox("Selecione um contato para remover.",
                          "Aviso", wx.OK | wx.ICON_WARNING)

    def OnStartCampaign(self, e):
        if not (self.bot and self.bot.driver):
            return
        cfg = {'message': self.campaign_msg.GetValue(
        ), 'image_pdf_path': self.image_path.GetValue(), 'audio_path': self.audio_path.GetValue()}
        if self.rb_manual.GetValue():
            cfg['source_type'] = C.SourceType.MANUAL_LIST
            if self.manual_contact_list.GetItemCount() == 0:
                wx.MessageBox("Adicione contatos manuais.",
                              "Erro", wx.OK | wx.ICON_ERROR)
                return
            cfg['manual_contacts'] = [(self.manual_contact_list.GetItem(i, 0).GetText(), self.manual_contact_list.GetItem(
                i, 1).GetText()) for i in range(self.manual_contact_list.GetItemCount())]
        else:
            if not self.contact_list_path.GetValue():
                wx.MessageBox("Selecione um arquivo de lista.",
                              "Erro", wx.OK | wx.ICON_ERROR)
                return
            cfg['source_type'] = C.SourceType.LIST if self.rb_list_numbers.GetValue(
            ) else C.SourceType.GROUP_LIST
            cfg['contact_list_path'] = self.contact_list_path.GetValue()
        if not any(cfg.values()):
            wx.MessageBox("A campanha está vazia.",
                          "Aviso", wx.OK | wx.ICON_WARNING)
            return
        threading.Thread(target=self.bot.start_campaign,
                         args=(cfg,), daemon=True).start()

    def update_buttons_for_running(self, running): wx.CallAfter(
        self._do_update_buttons_for_running, running)

    def _do_update_buttons_for_running(self, running):
        self._set_status_text(
            "Campanha em execução..." if running else "Ocioso")
        self.start_campaign_btn.Enable(not running)
        self.notebook.Enable(not running)
        self.parar_btn.Enable(running)
        self.pausar_btn.Enable(running)
        for i in range(self.GetMenuBar().GetMenuCount()):
            self.GetMenuBar().EnableTop(i, not running)

    def update_pause_button(self, paused): wx.CallAfter(
        self._do_update_pause_button, paused)

    def _do_update_pause_button(self, paused):
        self.pausar_btn.SetLabel("Continuar" if paused else "Pausar")
        self._set_status_text("Pausado" if paused else "Em execução...")
        self.pausar_btn.SetBitmap(wx.ArtProvider.GetBitmap(
            wx.ART_GO_FORWARD if paused else wx.ART_PASTE, wx.ART_BUTTON, (16, 16)))

    def log_message(self, message, color=None): wx.CallAfter(
        self._do_log_message, message, color or self.colors["text"])

    def _do_log_message(self, message, color): self.log.SetDefaultStyle(
        wx.TextAttr(color)); self.log.AppendText(f"{message}\n")

    def OnBrowseContacts(self, e):
        with wx.FileDialog(self, "Escolha a lista", wildcard=C.WILDCARD_CONTACTS, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fd:
            if fd.ShowModal() == wx.ID_OK:
                self.contact_list_path.SetValue(fd.GetPath())

    def OnBrowseImage(self, e):
        with wx.FileDialog(self, "Escolha Imagem/PDF", wildcard=C.WILDCARD_MEDIA, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fd:
            if fd.ShowModal() == wx.ID_OK:
                self.image_path.SetValue(fd.GetPath())

    def OnBrowseAudio(self, e):
        with wx.FileDialog(self, "Escolha um áudio", wildcard=C.WILDCARD_AUDIO, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fd:
            if fd.ShowModal() == wx.ID_OK:
                self.audio_path.SetValue(fd.GetPath())

    def OnRecordToggle(self, e):
        if not self.bot:
            return
        if self.bot.is_recording:
            self.update_audio_controls(
                C.AudioState.READY if self.bot.stop_recording() else C.AudioState.IDLE)
        else:
            self.bot.start_recording()
            self.update_audio_controls(C.AudioState.RECORDING)

    def OnPlayAudio(self, e):
        if self.bot:
            self.bot.play_recorded_audio()

    def OnDiscardAudio(self, e):
        if self.bot and self.bot.discard_recorded_audio():
            if self.audio_path.GetValue() == str(self.bot.temp_audio_path):
                self.audio_path.Clear()
            self.update_audio_controls(C.AudioState.IDLE)

    def OnAttachRecordedAudio(self, e):
        if not self.bot:
            return
        if self.bot.temp_audio_path.exists():
            self.audio_path.SetValue(str(self.bot.temp_audio_path))
            self.log_message("[INFO] Áudio gravado anexado.", "lightgreen")
        else:
            self.log_message("[ERRO] Nenhum áudio gravado.", "red")

    def on_recording_error(self): self.update_audio_controls(C.AudioState.IDLE)

    def set_playback_buttons_state(self, is_playing): self.update_audio_controls(
        C.AudioState.PLAYING if is_playing else C.AudioState.READY)

    def update_audio_controls(self, state: C.AudioState): wx.CallAfter(
        self._do_update_audio_controls, state)

    def _do_update_audio_controls(self, state: C.AudioState):
        self.record_btn.SetLabel(
            "Parar" if state == C.AudioState.RECORDING else "Gravar")
        self.record_btn.Enable(state != C.AudioState.PLAYING)
        self.play_btn.Enable(state == C.AudioState.READY)
        self.discard_btn.Enable(
            state in [C.AudioState.READY, C.AudioState.PLAYING, C.AudioState.RECORDING])
        self.attach_audio_btn.Enable(state == C.AudioState.READY)
        self.record_btn.SetBackgroundColour(
            self.colors["primary"] if state == C.AudioState.RECORDING else self.colors["accent_red"])

    def OnParar(self, e):
        if self.bot:
            self.log_message("[INFO] Parando...", "yellow")
            self.bot.stop()

    def OnPausar(self, e):
        if self.bot:
            self.bot.toggle_pause()

    def OnMinimizeToTray(self, e):
        self.Hide()
        self.log_message("[INFO] Zap Fácil minimizado.", "yellow")
        if hasattr(e, 'CanVeto') and e.CanVeto():
            e.Veto()

    def OnRestore(self, e=None): self.Show(); self.Restore(); self.Raise()

    def OnExitApp(self, e):
        self.taskBarIcon.RemoveIcon()
        self.taskBarIcon.Destroy()
        if self.bot:
            self.log_message("[INFO] Encerrando...")
            threading.Thread(target=self.bot.shutdown, daemon=True).start()
        else:
            self.Destroy()

    def on_bot_shutdown(self): self.Destroy()
    def _set_status_text(self, text, field=0): wx.CallAfter(
        self.statusBar.SetStatusText, text, field)

    def enable_buttons(self): wx.CallAfter(self._do_enable_buttons)

    def _do_enable_buttons(self):
        self.activity_indicator.Stop()
        self._set_status_text("Conectado")
        self.start_campaign_btn.Enable(True)
        self.log_message(
            "[INFO] WhatsApp conectado. Pronto para operar.", self.colors["primary"])
        self.Raise()

    def on_connection_failed(self): wx.CallAfter(self._do_on_connection_failed)

    def _do_on_connection_failed(self):
        self.activity_indicator.Stop()
        self._set_status_text("Falha na conexão")
        self.log_message(
            "[ERRO] Falha ao conectar ao WhatsApp.", self.colors["accent_red"])
