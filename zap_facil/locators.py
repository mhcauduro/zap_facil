# =================================================================================
# ZAP FÁCIL - ARQUIVO CENTRAL DE LOCALIZADORES (SELETORES CSS)
# ---------------------------------------------------------------------------------
# Este arquivo contém todos os seletores CSS usados pelo Selenium para encontrar
# os elementos na página do WhatsApp Web. Manter este arquivo atualizado é
# essencial para a estabilidade do bot.
# =================================================================================


# --- CONEXÃO E TELA PRINCIPAL ---
# Seletores usados para verificar se o WhatsApp carregou corretamente.

# Painel lateral esquerdo que indica que a interface principal foi carregada.
# Usar um seletor de ID (#) é a forma mais rápida e estável.
MAIN_PANEL = "#pane-side"

# O elemento <canvas> onde o QR Code de conexão é renderizado.
# Usamos o aria-label para identificá-lo de forma única.
QR_CODE_CANVAS = "canvas[aria-label='Scan me!']"


# --- BUSCA E ABERTURA DE CONVERSAS ---
# Seletores para encontrar a barra de busca e os resultados.

# Campo de input para pesquisar conversas. O data-testid é um atributo
# estável fornecido pelo próprio WhatsApp para testes.
CHAT_SEARCH_INPUT = "div[data-testid='chat-list-search']"

# Título da conversa atualmente aberta no painel principal.
# ATENÇÃO: Este seletor pode mudar. Se a captura de nome falhar, verificar aqui.
CHAT_HEADER_TITLE = "header span[data-testid='conversation-info-header-chat-title']"

# Template para encontrar um resultado da busca pelo seu título.
# O '{}' será substituído dinamicamente pelo nome do contato/grupo.
CHAT_SEARCH_RESULT_BY_TITLE = "span[title='{}']"


# --- COMPOSIÇÃO E ENVIO DE MENSAGENS ---
# Seletores para a caixa de texto e botões de envio.

# A caixa de texto principal onde as mensagens são digitadas.
# CORRIGIDO: Voltamos ao seletor original que é mais genérico e robusto.
MAIN_TEXT_BOX = "#main div[role='textbox'][contenteditable='true']"

# O botão de enviar a mensagem de texto (avião de papel).
# Usa o 'aria-label', que é confiável para a sua versão do WhatsApp.
SEND_MESSAGE_BUTTON = 'button[aria-label="Enviar"]'


# --- ANEXOS ---
# Seletores para o menu de anexos e seus botões.

# O botão de clipe de papel para abrir o menu de anexos.
ATTACH_CLIP_BUTTON = "span[data-testid='clip']"

# O botão de enviar um anexo (depois de já ter sido escolhido).
SEND_ATTACHMENT_BUTTON = "span[data-testid='send']"

# Os campos <input> (que ficam escondidos) para cada tipo de anexo.
ATTACH_IMAGE_INPUT = "input[accept='image/*,video/mp4,video/3gpp,video/quicktime']"
ATTACH_DOCUMENT_INPUT = "input[accept='*']"