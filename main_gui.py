"""
TCC file: main_gui.py
Autor: Victor de Abreu Viana
Descriçao: Interface gráfica em PyQt6 para monitoramento e interação com um medidor DLMS/COSEM.

###########################################################################################

IEC 62056-47 · TCP/WRAPPER · LN · Low Authentication
Validado contra Gurux DLMS Server Example (porta 4063).
"""

import sys
import struct
import datetime
import traceback
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox, QGroupBox, QTabWidget, QLineEdit,
    QFrame, QSizePolicy, QTextEdit, QSplitter, QGridLayout,
    QScrollArea, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QTimer
from engine_dlms import DLMSClient

##########################################################################
# Cores do Software (css)
##########################################################################

C = {
    "bg":        "#F8FAFC",
    "panel":     "#FFFFFF",
    "panel2":    "#F1F5F9",
    "panel3":    "#E2E8F0",
    "border":    "#CBD5E1",
    "border2":   "#94A3B8",
    "accent":    "#1D4ED8",
    "accent_dim":"#DBEAFE",
    "green":     "#15803D",
    "green_dim": "#DCFCE7",
    "red":       "#B91C1C",
    "red_dim":   "#FEE2E2",
    "orange":    "#C2410C",
    "orange_dim":"#FFEDD5",
    "purple":    "#6D28D9",
    "purple_dim":"#EDE9FE",
    "teal":      "#0F766E",
    "teal_dim":  "#CCFBF1",
    "yellow":    "#A16207",
    "yellow_dim":"#FEF9C3",
    "text":      "#0F172A",
    "muted":     "#64748B",
    "dim":       "#94A3B8",
    "hex_addr":  "#7C3AED",
    "hex_wrap":  "#0EA5E9",
    "hex_apdu":  "#F59E0B",
    }

##########################################################################
# Ícones usados no software
##########################################################################

icons = {
    "home": "◈",
    "aba_status": "📊",
    "aba_leituras": "📋",
    "aba_profile": "📈",
    "aba_console": "⚙",
    "seta_direita": "⟶",
    "seta_esquerda": "⟵",
    "sucesso": "✔",
    "falha": "✖",
    "aviso": "⚠",
    "get": "📥",
    "set": "📤",
    "action": "⚡",
    "um": "▶",
    "todos": "⟳",
    "enter": "↵",
    "selecionado": "●",
    "nao_selecionado": "◌"
}

##########################################################################
# Estilos globais do PyQt6
##########################################################################

STYLE = f"""
* {{font-family: 'Inter', 'Segoe UI', sans-serif; font-size: 10pt; color: {C['text']};
}}

QMainWindow, QWidget, QDialog {{ background-color: {C['bg']}; 
}}

QGroupBox {{ background: {C['panel']}; border: 1px solid {C['border']}; 
             border-radius: 6px; margin-top: 14px; padding: 12px 8px 8px 8px; 
             font-size: 8pt; font-weight: bold; color: {C['muted']}; letter-spacing: 1.2px;
}}

QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px; background: {C['panel']};
}}

QTabWidget::pane {{ background: {C['panel']}; border: 1px solid {C['border']}; border-radius: 6px;
    top: -1px;
}}

QTabBar::tab {{ background: {C['panel2']}; color: {C['muted']}; border: 1px solid {C['border']};
                border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px;
                padding: 7px 16px; margin-right: 2px; font-size: 9pt; font-weight: 600;
}}

QTabBar::tab:selected {{ background: {C['panel']}; color: {C['accent']}; border-bottom: 2px solid {C['accent']};
}}

QTableWidget {{ background: {C['panel']}; gridline-color: {C['border']}; border: 1px solid {C['border']};
                border-radius: 4px; alternate-background-color: {C['panel2']}; outline: none;
                selection-background-color: {C['accent_dim']}; selection-color: {C['text']};
}}

QTableWidget::item {{ padding: 4px 8px; 
}}

QHeaderView::section {{ background: {C['panel2']}; color: {C['muted']}; border: none;
                        border-right: 1px solid {C['border']}; border-bottom: 1px solid {C['border']};
                        padding: 6px 8px; font-size: 8pt; font-weight: bold; letter-spacing: 0.8px;
}}

QLineEdit, QComboBox {{ background: {C['panel']}; border: 1px solid {C['border']}; border-radius: 4px;
                        padding: 6px 10px; color: {C['text']};
}}

QLineEdit {{ font-family: 'Consolas', monospace; 
}}

QLineEdit:focus, QComboBox:focus {{ border-color: {C['accent']}; 
}}

QComboBox::drop-down {{ border: none; width: 20px; 
}}

QComboBox QAbstractItemView {{ background: {C['panel']}; border: 1px solid {C['border']};
                               selection-background-color: {C['accent_dim']};
}}

QScrollBar:vertical, QScrollBar:horizontal {{ background: {C['bg']}; border-radius: 4px;
}}

QScrollBar:vertical {{ width: 8px; 
}}

QScrollBar:horizontal {{ height: 8px; 
}}

QScrollBar::handle {{ background: {C['border2']}; border-radius: 4px; 
}}

QScrollBar::handle:hover {{ background: {C['muted']}; 
}}

QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; 
}}

QTextEdit {{ background: {C['panel']}; border: 1px solid {C['border']}; border-radius: 4px;
             padding: 6px; font-family: 'Consolas', monospace; font-size: 9pt; color: {C['text']};
}}

QTreeWidget {{ background: {C['panel']}; border: 1px solid {C['border']}; border-radius: 4px;
               font-family: 'Consolas', monospace; font-size: 9pt; outline: none;
              show-decoration-selected: 1;
}}

QTreeWidget::item {{ padding: 2px 4px; 
}}

QTreeWidget::item:selected {{ background: {C['accent_dim']}; color: {C['text']}; 
}}

QSplitter::handle {{ background: {C['border']}; 
}}

QSplitter::handle:horizontal {{ width: 1px; 
}}

QSplitter::handle:vertical   {{ height: 1px; 
}}
"""

##########################################################################
# Estilos dos botões (GET/SET/ACTION)
##########################################################################

def btn_style(bg, fg):
    return f"""
    QPushButton {{ background:{bg}; color:{fg}; border:1px solid {fg}; border-radius:4px;
                   padding:7px 16px; font-weight:600; font-size:9pt;}}
    QPushButton:hover {{ background:{fg}; color:white; }}
    QPushButton:pressed {{ background:{fg}; color:white; }}
    QPushButton:disabled {{ background:{C['panel2']}; color:{C['dim']}; border-color:{C['border']}; }}
    """

##########################################################################
# Catálogo COSEM - usado do catalogo_dlms.py
##########################################################################

OBIS_CATALOG = [
    # OBIS              Class ID  Attr/Method   Label                              Categoria
    ("0.0.42.0.0.255",         1,           2,   "Logical Device Name",            "Sistema"),
    ("1.0.0.2.0.255",          1,           2,   "Firmware Version",               "Sistema"),
    ("0.0.43.1.0.255",         1,           2,   "Invocation Counter",             "Sistema"),
    ("0.0.43.1.8.255",         1,           2,   "Data adicional",                 "Sistema"),
    ("0.0.1.0.0.255",          8,           2,   "Clock - hora atual",             "Tempo"),
    ("0.0.1.0.0.255",          8,           3,   "Clock - time zone",              "Tempo"),
    ("0.0.1.0.0.255",          8,           4,   "Clock - status",                 "Tempo"),
    ("0.0.1.0.0.255",          8,           8,   "Clock - clock base",             "Tempo"),
    ("1.1.21.25.0.255",        3,           2,   "Register - valor",               "Registradores"),
    ("1.1.21.25.0.255",        3,           3,   "Register - scaler/unit",         "Registradores"),
    ("1.0.31.4.0.255",         5,           2,   "Demand Register - valor",        "Registradores"),
    ("1.0.99.1.0.255",         7,           2,   "Load Profile - buffer",          "Perfil"),
    ("1.0.99.1.0.255",         7,           3,   "Load Profile - capture objects", "Perfil"),
    ("1.0.99.1.0.255",         7,           7,   "Load Profile - entries in use",  "Perfil"),
    ("1.0.99.1.0.255",         7,           8,   "Load Profile - profile entries", "Perfil"),
    ("0.0.40.0.0.255",        15,           2,   "Public Association",             "Associações"),
    ("0.0.40.0.2.255",        15,           2,   "Low Association",                "Associações"),
    ("0.0.25.1.0.255",        42,           2,   "TCP/UDP Setup",                  "Comunicação"),
    ("0.0.25.9.0.255",        40,           4,   "Push Setup - destination",       "Comunicação"),
]

def lbl_caps(text, color=None):
    """ 
    Label com estilo de texto em CAPS
    """
    l = QLabel(text.upper())
    c = color or C["muted"]
    l.setStyleSheet(f"font-size:8pt; font-weight:bold; color:{c};"
                    f"letter-spacing:1.2px; background:none; border:none;")
    return l

def hex_dump(data: bytes, wrap_len: int = 8) -> str:
    """
    Função que formata bytes em hex, para exibição no Wire Inspector.
    Separa visualmente o header WRAPPER (8 bytes) do APDU.
    """
    if not data:
        return ""
    out = []
    if len(data) >= 8:  # WRAPPER (primeiros 8 bytes)
        out.append(" ".join(f"{b:02X}" for b in data[:8]))
        out.append(" │ ")
        rest = data[8:]
    else:
        rest = data     # APDU (restante dos bytes agrupadoa)
    for i in range(0, len(rest), 16):
        chunk = rest[i:i+16]
        out.append(" ".join(f"{b:02X}" for b in chunk))
        if i + 16 < len(rest):
            out.append("\n" + " " * 26)
    return "".join(out)

def format_value(val, max_rows=10):
    """ 
    Função para formatar um valor COSEM para exibição
    """
    if isinstance(val, list) and val and isinstance(val[0], tuple):
        rows = []
        for i, t in enumerate(val[:max_rows]):
            rows.append(f"  [{i+1:>3}] " + "  |  ".join(str(x) for x in t))
        if len(val) > max_rows:
            rows.append(f"  ... +{len(val)-max_rows} linhas")
        return f"Array de {len(val)} entradas:\n" + "\n".join(rows)
    if isinstance(val, tuple):
        return "(" + ", ".join(str(x) for x in val) + ")"
    if isinstance(val, list):
        return f"[{len(val)} elementos]"
    return str(val)

##########################################################################
# Decoder de APDU para Wire Inspector (interpretação humana dos bytes)
##########################################################################

APDU_TAGS = {
    0x60: "AARQ - Association Request",
    0x61: "AARE - Association Response",
    0x62: "RLRQ - Release Request",
    0x63: "RLRE - Release Response",
    0xC0: "GET-Request",
    0xC1: "SET-Request",
    0xC3: "ACTION-Request",
    0xC4: "GET-Response",
    0xC5: "SET-Response",
    0xC7: "ACTION-Response",
    0x0E: "Confirmed-Service-Error",
}

def parse_wrapper(data: bytes):
    """
    Função que retorna dict com campos do WRAPPER + apdu
    """
    if len(data) < 8:
        return None
    ver, src, dst, n = struct.unpack(">HHHH", data[:8])
    return {
        "version": ver,
        "src": src,
        "dst": dst,
        "length": n,
        "apdu": data[8:8+n],
    }

def parse_apdu_summary(apdu: bytes) -> list:
    """
    Função que retorna lista (label, valor) descrevendo a estrutura do APDU
    """
    if not apdu:
        return [("(empty)", "")]
    tag = apdu[0]
    name = APDU_TAGS.get(tag, f"Unknown 0x{tag:02X}")
    out = [("APDU type", f"0x{tag:02X}  {name}")]

    # GET/SET/ACTION request
    if tag in (0xC0, 0xC1, 0xC3) and len(apdu) >= 13:
        kind = apdu[1]
        invoke = apdu[2]
        cls = struct.unpack(">H", apdu[3:5])[0]
        obis = ".".join(str(b) for b in apdu[5:11])
        attr = apdu[11]
        out.append(("Service variant", f"0x{kind:02X}"))
        out.append(("Invoke-id", f"0x{invoke:02X}"))
        out.append(("Class ID", f"{cls}"))
        out.append(("OBIS Code", obis))
        label = "Method ID" if tag == 0xC3 else "Attribute"
        out.append((label, f"{attr}"))
        if tag == 0xC1 and len(apdu) > 13:
            out.append(("Data", apdu[13:].hex()))

    # GET-Response
    elif tag == 0xC4 and len(apdu) >= 4:
        kind = apdu[1]
        invoke = apdu[2]
        result = apdu[3]
        out.append(("Response variant", f"0x{kind:02X}"))
        out.append(("Invoke-id", f"0x{invoke:02X}"))
        if kind == 0x01:
            if result == 0x00:
                out.append(("Result", "data (success)"))
                if len(apdu) > 4:
                    out.append(("Data tag", f"0x{apdu[4]:02X}"))
            else:
                err = apdu[4] if len(apdu) > 4 else 0
                out.append(("Result", f"data-access-error 0x{err:02X}"))
        elif kind == 0x02:
            out.append(("Response variant", "with-data-block"))
            out.append(("Last block", f"0x{apdu[3]:02X}"))

    # SET/ACTION response
    elif tag in (0xC5, 0xC7) and len(apdu) >= 4:
        out.append(("Invoke-id", f"0x{apdu[2]:02X}"))
        out.append(("Result", f"0x{apdu[3]:02X}  ({'success' if apdu[3]==0 else 'error'})"))

    # AARQ/AARE
    elif tag in (0x60, 0x61) and len(apdu) >= 2:
        out.append(("Length", f"{apdu[1]} bytes"))
        if tag == 0x61:
            for i in range(len(apdu) - 4):
                if apdu[i] == 0xA2 and apdu[i+1] == 0x03 and apdu[i+2] == 0x02:
                    rr = apdu[i+4]
                    out.append(("Association-result",
                                f"0x{rr:02X}  ({'accepted' if rr==0 else 'rejected'})"))
                    break

    return out

##########################################################################
# Componentes Visuais da Interface
##########################################################################

class StatusPill(QLabel):
    """
    Função para mostrar status (verde/vermelho/amarelo) para indicar estado da conexão.
        Verde: online
        Vermelho: offline
        Amarelo: conectando
    """
    def __init__(self):
        super().__init__()
        self.set_offline()
    def _set(self, txt, fg, bg):
        self.setText(txt)
        self.setStyleSheet(f"""QLabel {{ background:{bg}; color:{fg}; border:1px solid {fg}; border-radius:10px;
                                         padding:3px 14px; font-size:8pt; font-weight:bold; letter-spacing:1px;
        }}""")
    def set_online(self):    self._set(icons["selecionado"]     + " ONLINE",     C["green"],  C["green_dim"])
    def set_offline(self):   self._set(icons["selecionado"]     + " OFFLINE",    C["red"],    C["red_dim"])
    def set_connecting(self):self._set(icons["nao_selecionado"] + " CONECTANDO", C["yellow"], C["yellow_dim"])


class StatCard(QFrame):
    """
    Card grande com label + valor, para painel Status
    """
    def __init__(self, title: str, accent: str = None):
        super().__init__()
        self._accent = accent or C["accent"]
        self.setStyleSheet(f"""QFrame {{ background:{C['panel']}; border:1px solid {C['border']};
                                         border-radius:6px;
        }}""")
        self.setMinimumHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        accent_bar = QFrame()
        accent_bar.setFixedHeight(3)
        accent_bar.setStyleSheet(f"background:{self._accent}; border:none;")
        lay.addWidget(accent_bar)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet(f"font-size:8pt; font-weight:bold;"
                                     f"color:{C['muted']}; letter-spacing:1.5px;"
                                     f"background:none; border:none;")
        lay.addWidget(self.title_lbl)

        self.val_lbl = QLabel("-")
        self.val_lbl.setStyleSheet(f"font-family:'Consolas',monospace;"
                                   f"font-size:14pt; font-weight:bold;"
                                   f"color:{C['text']}; background:none; border:none;")
        self.val_lbl.setWordWrap(True)
        lay.addWidget(self.val_lbl)
        lay.addStretch()

    def update_value(self, value, color=None):
        """
        Atualiza o valor exibido no card, com formatação e cor
        """
        c = color or C["text"]
        s = str(value)
        if len(s) > 36:
            s = s[:34] + "…"
        self.val_lbl.setText(s)
        self.val_lbl.setStyleSheet(f"font-family:'Consolas',monospace;"
                                   f"font-size:14pt; font-weight:bold;"
                                   f"color:{c}; background:none; border:none;")


class LogConsole(QTextEdit):
    """
    Componente de console de log para exibir mensagens do sistema
    """
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumHeight(110)
        self._log("Sistema iniciado. Aguardando associação.", C["muted"])
    def _log(self, msg, color):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        msg = msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.append(f'<span style="color:{C["dim"]}">{ts}</span> '
                    f'<span style="color:{color}">{msg}</span>')
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
    def info(self, m):    self._log(m, C["text"])
    def ok(self, m):      self._log(f"{icons['sucesso']} {m}", C["green"])
    def err(self, m):     self._log(f"{icons['falha']}   {m}", C["red"])
    def warn(self, m):    self._log(f"{icons['aviso']}   {m}", C["yellow"])
    def get(self, o, v):  self._log(f"GET   {o}   {icons['seta_direita']}   {format_value(v, 2)[:80]}", C["accent"])
    def set_(self, o, v): self._log(f"SET   {o}   {icons['seta_esquerda']}  {v}", C["orange"])
    def act(self, o, v):  self._log(f"ACT   {o}   {icons['seta_direita']}   {v}", C["purple"])


##########################################################################
# WIRE INSPECTOR - exibe TX/RX puro
##########################################################################

class WireInspector(QWidget):
    """ 
    Componente para exibir os bytes TX/RX em formato hex + interpretação do APDU
    """
    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        """ 
        Layout do Wire Inspector
        """
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        root.addWidget(lbl_caps("Wire Inspector - IEC 62056-47", C["accent"]))

        # TX mostra o último request enviado (GET/SET/ACTION/AARQ), em hex + interpretação do APDU
        tx_group = QGroupBox("TX  (último request)")
        tx_lay = QVBoxLayout()
        tx_lay.setContentsMargins(8, 4, 8, 8)
        tx_group.setLayout(tx_lay)

        self.tx_hex = QTextEdit()
        self.tx_hex.setReadOnly(True)
        self.tx_hex.setMaximumHeight(80)
        self.tx_hex.setStyleSheet(f"""QTextEdit {{ background:{C['panel2']}; 
                                                   border:1px solid {C['border']};
                                                   border-radius:4px; padding:6px;
                                                   font-family:'Consolas',monospace; font-size:8.5pt;
        }}""")
        tx_lay.addWidget(self.tx_hex)

        self.tx_tree = QTreeWidget()
        self.tx_tree.setHeaderHidden(True)
        self.tx_tree.setMaximumHeight(140)
        tx_lay.addWidget(self.tx_tree)

        root.addWidget(tx_group)

        # RX mostra a última resposta recebida, em hex + interpretação do APDU
        rx_group = QGroupBox("RX (resposta)")
        rx_lay = QVBoxLayout()
        rx_lay.setContentsMargins(8, 4, 8, 8)
        rx_group.setLayout(rx_lay)

        self.rx_hex = QTextEdit()
        self.rx_hex.setReadOnly(True)
        self.rx_hex.setMaximumHeight(110)
        self.rx_hex.setStyleSheet(f"""QTextEdit {{ background:{C['panel2']}; 
                                                   border:1px solid {C['border']};
                                                   border-radius:4px; padding:6px;
                                                   font-family:'Consolas',monospace; font-size:8.5pt;
        }}""")
        rx_lay.addWidget(self.rx_hex)

        self.rx_tree = QTreeWidget()
        self.rx_tree.setHeaderHidden(True)
        rx_lay.addWidget(self.rx_tree)

        root.addWidget(rx_group, 1)

    def update_from_client(self, client: DLMSClient):
        """
        Atualiza o Wire Inspector com os últimos bytes TX/RX do cliente DLMS
        """
        if not client:
            return
        self._render(client.last_tx, self.tx_hex, self.tx_tree)
        self._render(client.last_rx, self.rx_hex, self.rx_tree)

    def _render(self, data: bytes, hex_widget: QTextEdit, tree: QTreeWidget):
        """ 
        Renderiza os bytes em hex + interpretação dos dados no Wire Inspector
        """
        tree.clear()
        if not data:
            hex_widget.setPlainText("-")
            return
        hex_widget.setPlainText(hex_dump(data))

        windows = parse_wrapper(data)
        if not windows:
            return

        wrap_node = QTreeWidgetItem([f"WRAPPER (8 bytes)"])
        wrap_node.setForeground(0, QColor(C["hex_wrap"]))
        QTreeWidgetItem(wrap_node, [f"version       0x{windows['version']:04X}"                 ])
        QTreeWidgetItem(wrap_node, [f"src (Client)  0x{windows['src']:04X}  ({windows['src']})" ])
        QTreeWidgetItem(wrap_node, [f"dst (Server)  0x{windows['dst']:04X}  ({windows['dst']})" ])
        QTreeWidgetItem(wrap_node, [f"length          {windows['length']} bytes"                ])
        tree.addTopLevelItem(wrap_node)
        wrap_node.setExpanded(True)

        apdu_node = QTreeWidgetItem([f"APDU ({windows['length']} bytes)"])
        apdu_node.setForeground(0, QColor(C["hex_apdu"]))
        for label, value in parse_apdu_summary(windows["apdu"]):
            QTreeWidgetItem(apdu_node, [f"{label:<20s}  {value}"])
        tree.addTopLevelItem(apdu_node)
        apdu_node.setExpanded(True)


##########################################################################
# ABA STATUS - painel de cards com info do medidor
##########################################################################

class StatusTab(QWidget):
    """ 
    Componente para exibir painel de status do medidor
    """
    def __init__(self, log: LogConsole, wire: WireInspector):
        super().__init__()
        self.log = log
        self.wire = wire
        self.client = None
        self._build()

    def _build(self):
        """
        Layout do painel de status
        """
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(lbl_caps("Painel de Status do Medidor"))
        header.addStretch()
        self.btn_refresh = QPushButton(icons["todos"] + " Atualizar Tudo")
        self.btn_refresh.setStyleSheet(btn_style(C["accent_dim"], C["accent"]))
        self.btn_refresh.clicked.connect(self._refresh_all)
        header.addWidget(self.btn_refresh)
        root.addLayout(header)

        # Monta um grid 3 x 2 de áreas 
        grid = QGridLayout()
        grid.setSpacing(10)

        self.card_ldn   = StatCard("Logical Device Name",  C["accent"])
        self.card_fw    = StatCard("Firmware Version",     C["purple"])
        self.card_clock = StatCard("Clock - Hora Atual",   C["green"])
        self.card_inv   = StatCard("Invocation Counter",   C["teal"])
        self.card_reg   = StatCard("Register - Valor",     C["orange"])
        self.card_lp    = StatCard("Load Profile Entries", C["yellow"])

        grid.addWidget(self.card_ldn,   0, 0)
        grid.addWidget(self.card_fw,    0, 1)
        grid.addWidget(self.card_clock, 0, 2)
        grid.addWidget(self.card_inv,   1, 0)
        grid.addWidget(self.card_reg,   1, 1)
        grid.addWidget(self.card_lp,    1, 2)

        root.addLayout(grid)
        root.addStretch()

    def _refresh_all(self):
        """ 
        Lê os valores de todos os cards do painel, usando o cliente DLMS
        """
        if not self.client:
            return
        mapping = [
            (self.card_ldn,   "0.0.42.0.0.255",   1, 2, C["accent"]),
            (self.card_fw,    "1.0.0.2.0.255",    1, 2, C["purple"]),
            (self.card_clock, "0.0.1.0.0.255",    8, 2, C["green"]),
            (self.card_inv,   "0.0.43.1.0.255",   1, 2, C["teal"]),
            (self.card_reg,   "1.1.21.25.0.255",  3, 2, C["orange"]),
            (self.card_lp,    "1.0.99.1.0.255",   7, 7, C["yellow"]),
        ]
        for card, obis, cls, attr, color in mapping:
            try:
                val = self.client.send_get(obis, cls, attr)
                card.update_value(val, color)
                self.log.get(obis, val)
            except Exception as e:
                card.update_value("ERR", C["red"])
                self.log.err(str(e))
        self.wire.update_from_client(self.client)


##########################################################################
# ABA LEITURAS - tabela com objetos COSEM para leitura manual
##########################################################################
class ReadingsTab(QWidget):
    """
    Componente para exibir tabela de OBIS e permitir leitura manual 
    """
    def __init__(self, log: LogConsole, wire: WireInspector):
        super().__init__()
        self.log = log
        self.wire = wire
        self.client = None
        self._build()

    def _build(self):
        """ 
        Layout da tabela de leituras, com combo de filtro por categoria e botões de ação 
        """
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        ctl = QHBoxLayout()
        ctl.addWidget(lbl_caps("Filtrar:"))
        self.combo_cat = QComboBox()
        cats = ["Todos"] + sorted(set(c[4] for c in OBIS_CATALOG))
        self.combo_cat.addItems(cats)
        self.combo_cat.currentTextChanged.connect(self._populate_table)
        ctl.addWidget(self.combo_cat, 1)

        self.btn_sel = QPushButton(icons['um'] + " Ler Selecionado")
        self.btn_sel.setStyleSheet(btn_style(C["accent_dim"], C["accent"]))
        self.btn_sel.clicked.connect(self._read_selected)
        ctl.addWidget(self.btn_sel)

        self.btn_all = QPushButton(icons['todos'] + " Ler Todos")
        self.btn_all.setStyleSheet(btn_style(C["panel3"], C["muted"]))
        self.btn_all.clicked.connect(self._read_all)
        ctl.addWidget(self.btn_all)
        root.addLayout(ctl)

        self.table = QTableWidget(0, 5)
        # Cabeçalhos das colunas
        self.table.setHorizontalHeaderLabels(["OBIS", "ATTR", "DESCRIÇÃO", "CATEGORIA", "VALOR"]) 
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self._populate_table("Todos")
        root.addWidget(self.table, 1)

    def _populate_table(self, cat="Todos"):
        """
        Preenche a tabela de leituras com os objetos do catálogo, filtrando por categoria 
        """
        rows = OBIS_CATALOG if cat == "Todos" else [r for r in OBIS_CATALOG if r[4] == cat]
        self.table.setRowCount(0)
        for obis, cls, attr, label, categoria in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            obis_item = QTableWidgetItem(obis)
            obis_item.setFont(QFont("Consolas", 8))
            obis_item.setForeground(QColor(C["accent"]))
            self.table.setItem(r, 0, obis_item)
            self.table.setItem(r, 1, QTableWidgetItem(str(attr)))
            self.table.setItem(r, 2, QTableWidgetItem(label))
            cat_item = QTableWidgetItem(categoria)
            cat_item.setForeground(QColor(C["muted"]))
            self.table.setItem(r, 3, cat_item)
            v = QTableWidgetItem("-")
            v.setForeground(QColor(C["dim"]))
            v.setFont(QFont("Consolas", 9))
            self.table.setItem(r, 4, v)

    def _read_one(self, row, obis, cls, attr):
        """ 
        Lê um obis específico e atualiza a tabela com o valor lido
        """
        try:
            if obis == "1.0.99.1.0.255" and attr == 2:
                entries = self.client.send_get(obis, cls, 7)
                if isinstance(entries, int) and entries > 0:
                    n = min(10, entries)
                    val = self.client.send_get(obis, cls, 2,
                                               selective=(entries-n+1, entries))
                else:
                    val = self.client.send_get(obis, cls, attr)
            else:
                val = self.client.send_get(obis, cls, attr)
            txt = format_value(val, 3).replace("\n", icons["enter"])[:160]
            self.table.item(row, 4).setText(txt)
            self.table.item(row, 4).setForeground(QColor(C["green"]))
            self.log.get(obis, val)
        except Exception as e:
            self.table.item(row, 4).setText(f"ERR: {e}")
            self.table.item(row, 4).setForeground(QColor(C["red"]))
            self.log.err(str(e))

    def _read_selected(self):
        """ 
        Lê o objeto COSEM da linha selecionada na tabela
        """
        if not self.client: return
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.information(self, "Aviso", "Selecione uma linha.")
            return
        obis = self.table.item(r, 0).text()
        attr = int(self.table.item(r, 1).text())
        entry = next((e for e in OBIS_CATALOG if e[0] == obis and e[2] == attr), None)
        if entry:
            self._read_one(r, entry[0], entry[1], entry[2])
            self.wire.update_from_client(self.client)

    def _read_all(self):
        """
        Lê todos os objetos COSEM listados na tabela
        """
        if not self.client: return
        for r in range(self.table.rowCount()):
            obis = self.table.item(r, 0).text()
            attr = int(self.table.item(r, 1).text())
            entry = next((e for e in OBIS_CATALOG if e[0] == obis and e[2] == attr), None)
            if entry:
                self._read_one(r, entry[0], entry[1], entry[2])
        self.wire.update_from_client(self.client)


##########################################################################
# ABA PROFILE - gráfico de Load Profile
##########################################################################
class ProfileTab(QWidget):
    """
    Componente para exibir gráfico do Load Profile (memória de massa)
    """
    def __init__(self, log: LogConsole, wire: WireInspector):
        super().__init__()
        self.log = log
        self.wire = wire
        self.client = None
        self._build()

    def _build(self):
        """ 
        Layout da aba de Load Profile, com gráfico e controles para selecionar range de entradas a exibir
        """
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        ctl = QHBoxLayout()
        ctl.addWidget(lbl_caps("Load Profile · 1.0.99.1.0.255 · Selective Access"))
        ctl.addStretch()

        ctl.addWidget(lbl_caps("Últimas:"))
        self.combo_n = QComboBox()
        # Opções de quantas últimas entradas do Load Profile exibir no gráfico (10, 50, 100, 500)
        self.combo_n.addItems(["10", "50", "100", "500"])
        self.combo_n.setMaximumWidth(80)
        ctl.addWidget(self.combo_n)

        self.btn_load = QPushButton(icons["todos"] + " Carregar Perfil")
        self.btn_load.setStyleSheet(btn_style(C["green_dim"], C["green"]))
        self.btn_load.clicked.connect(self._load)
        ctl.addWidget(self.btn_load)
        root.addLayout(ctl)

        #### Info ####
        info = QFrame()
        info.setStyleSheet(f"background:{C['panel']}; border:1px solid {C['border']};"
                           f"border-radius:4px;")
        il = QHBoxLayout(info)
        il.setContentsMargins(14, 8, 14, 8)
        self.lbl_total = QLabel("Total no buffer: -")
        self.lbl_range = QLabel("Range exibido: -")
        self.lbl_first = QLabel("Primeira: -")
        self.lbl_last  = QLabel("Última: -")
        for lbl in (self.lbl_total, self.lbl_range, self.lbl_first, self.lbl_last):
            lbl.setStyleSheet(f"font-family:'Consolas',monospace; font-size:9pt;"
                              f"color:{C['text']}; background:none; border:none;")
            il.addWidget(lbl)
            il.addSpacing(20)
        il.addStretch()
        root.addWidget(info)

        #### Gráfico ####
        pg.setConfigOption("background", C["panel"])
        pg.setConfigOption("foreground", C["text"])
        pg.setConfigOptions(antialias=True)
        date_axis = pg.DateAxisItem(orientation="bottom")
        self.plot = pg.PlotWidget(axisItems={"bottom": date_axis})
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.getAxis("left").setLabel("Valor do Registrador", color=C["muted"])
        self.plot.getAxis("bottom").setLabel("Tempo", color=C["muted"])
        self.plot.setStyleSheet(f"border:1px solid {C['border']}; border-radius:4px;")
        self.curve = self.plot.plot(
            pen=pg.mkPen(C["accent"], width=2),
            symbol="o", symbolSize=4,
            symbolBrush=C["accent"], symbolPen=None,
        )
        root.addWidget(self.plot, 1)

    def _load(self):
        """ 
        Carrega os dados do Load Profile e plota no gráfico
        """
        if not self.client: return
        n_target = int(self.combo_n.currentText())
        try:
            entries = self.client.send_get("1.0.99.1.0.255", 7, 7)
            if not isinstance(entries, int) or entries == 0:
                QMessageBox.information(self, "Buffer vazio", \
                    "Profile Generic não tem entradas capturadas.")
                return
            self.lbl_total.setText(f"Total no buffer: {entries}")
            n = min(n_target, entries)
            from_e = entries - n + 1
            to_e = entries
            self.lbl_range.setText(f"Range exibido: {from_e}-{to_e}  ({n} entradas)")
            data = self.client.send_get("1.0.99.1.0.255", 7, 2, selective=(from_e, to_e))
            if isinstance(data, list) and data and isinstance(data[0], tuple):
                xs, ys = [], []
                for i, t in enumerate(data):
                    ts_raw = t[0] if len(t) >= 1 else None
                    if isinstance(ts_raw, datetime.datetime):
                        x = ts_raw.timestamp()
                    elif isinstance(ts_raw, str):
                        try:
                            x = datetime.datetime.strptime(
                                ts_raw, "%Y-%m-%d %H:%M:%S").timestamp()
                        except ValueError:
                            x = float(from_e + i)
                    else:
                        x = float(from_e + i)
                    xs.append(x)
                    if len(t) >= 2 and isinstance(t[1], (int, float)):
                        ys.append(t[1])
                    else:
                        ys.append(0)
                self.curve.setData(xs, ys)
                self.lbl_first.setText(f"Primeira: {data[0]}")
                self.lbl_last.setText(f"Última: {data[-1]}")
                self.log.ok(f"Load Profile: {n} entradas plotadas")
            else:
                self.log.warn(f"Resposta inesperada: {data!r}")
            self.wire.update_from_client(self.client)
        except Exception as e:
            self.log.err(str(e))


##########################################################################
# ABA CONSOLE
##########################################################################

class ConsoleTab(QWidget):
    """
    Componente para enviar GET/SET/ACTION manualmente, com campos de entrada e log de resultados
    """
    def __init__(self, log: LogConsole, wire: WireInspector):
        """ 
        Inicializa a aba Console, recebendo o log e wire inspector
        para exibir resultados e tráfego
        """
        super().__init__()
        self.log = log
        self.wire = wire
        self.client = None
        self._build()

    def _build(self):
        """ 
        Layout da aba Console
        """
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        root.addWidget(lbl_caps("Console DLMS - GET / SET / ACTION"))

        #### Campos de entrada para OBIS, Classe, Atributo/Método e Valor (SET) ####
        f = QFrame()
        f.setStyleSheet(f"background:{C['panel']}; border:1px solid {C['border']};"
                        f"border-radius:4px;")
        fg = QGridLayout(f)
        fg.setContentsMargins(14, 12, 14, 12)
        fg.setSpacing(8)
        fg.setColumnStretch(1, 2)
        fg.setColumnStretch(3, 2)

        def fl(t):
            """ Label estilizada para os campos de entrada"""
            l = QLabel(t.upper())
            l.setStyleSheet(f"font-size:8pt; font-weight:bold; color:{C['muted']};"
                            f"background:none; border:none;")
            l.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return l

        fg.addWidget(fl("OBIS"),     0, 0)
        self.inp_obis = QLineEdit("0.0.42.0.0.255")
        fg.addWidget(self.inp_obis, 0, 1)

        fg.addWidget(fl("Class"),    0, 2)
        self.inp_cls = QLineEdit("1")
        self.inp_cls.setMaximumWidth(60)
        fg.addWidget(self.inp_cls, 0, 3)

        fg.addWidget(fl("Attr/Method"), 1, 0)
        self.inp_attr = QLineEdit("2")
        self.inp_attr.setMaximumWidth(60)
        fg.addWidget(self.inp_attr, 1, 1)

        fg.addWidget(fl("Valor (SET)"), 1, 2)
        self.inp_val = QLineEdit()
        self.inp_val.setPlaceholderText("vazio para GET/ACTION")
        fg.addWidget(self.inp_val, 1, 3)
        root.addWidget(f)

        #### Atalhos ####
        sg = QGroupBox("ATALHOS DO CATÁLOGO")
        sg_lay = QVBoxLayout()
        sg.setLayout(sg_lay)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(150)
        qw = QWidget()
        qg = QGridLayout(qw)
        qg.setSpacing(4)
        cat_color = {
            "Sistema": C["purple"], 
            "Tempo": C["accent"],
            "Registradores": C["teal"], 
            "Perfil": C["green"],
            "Associações": C["orange"], 
            "Comunicação": C["yellow"],
        }
        for i, (obis, cls, attr, label, cat) in enumerate(OBIS_CATALOG):
            color = cat_color.get(cat, C["muted"])
            btn = QPushButton(f"{obis}  attr={attr}\n{label}")
            btn.setStyleSheet(f"""
                QPushButton {{ background:{C['panel2']}; color:{C['muted']};
                               border:1px solid {C['border']}; border-radius:3px;
                               padding:4px 6px; font-size:7.5pt; text-align:left;
                }}
                QPushButton:hover {{ background:{C['panel3']}; color:{color}; border-color:{color};
                }}""")
            btn.setFixedHeight(40)
            btn.clicked.connect(lambda _, o=obis, c=cls, a=attr: self._fill(o, c, a))
            qg.addWidget(btn, i // 4, i % 4)
        scroll.setWidget(qw)
        sg_lay.addWidget(scroll)
        root.addWidget(sg)

        #### Botões de ação ####
        br = QHBoxLayout()
        self.btn_get = QPushButton(icons['get'] + "  GET - Leitura")
        self.btn_get.setStyleSheet(btn_style(C["accent_dim"], C["accent"]))
        self.btn_get.clicked.connect(self._do_get)
        self.btn_set = QPushButton(icons['set'] + "  SET - Escrita")
        self.btn_set.setStyleSheet(btn_style(C["orange_dim"], C["orange"]))
        self.btn_set.clicked.connect(self._do_set)
        self.btn_action = QPushButton(icons['action'] + "  ACTION - Execução")
        self.btn_action.setStyleSheet(btn_style(C["purple_dim"], C["purple"]))
        self.btn_action.clicked.connect(self._do_action)
        br.addWidget(self.btn_get)
        br.addWidget(self.btn_set)
        br.addWidget(self.btn_action)
        br.addStretch()
        root.addLayout(br)

        #### Resultado ####
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        self.result.setMinimumHeight(140)
        self._reset_result()
        root.addWidget(self.result, 1)

    def _reset_result(self):
        """ 
        Reseta a área de resultado para o estado inicial, aguardando uma requisição
        """
        self.result.setPlainText("Aguardando requisição...")
        self.result.setStyleSheet(f"""QTextEdit {{ background:{C['panel2']}; 
                                                   border:1px solid {C['border']};
                                                   border-radius:4px; padding:14px;
                                                   font-family:'Consolas',monospace; font-size:11pt;
                                                   color:{C['muted']};
        }}""")

    def _show(self, txt, color):
        """ 
        Exibe o resultado de uma requisição GET/SET/ACTION formatado
        """
        self.result.setPlainText(str(txt))
        self.result.setStyleSheet(f"""QTextEdit {{ background:{C['panel2']}; border:1px solid {color};
                                                   border-radius:4px; padding:14px;
                                                   font-family:'Consolas',monospace; font-size:11pt;
                                                   color:{color};
        }}""")

    def _fill(self, obis, cls, attr):
        """ 
        Preenche os campos de entrada com os valores do OBIS, Classe e Atributo/Método
        """
        self.inp_obis.setText(obis)
        self.inp_cls.setText(str(cls))
        self.inp_attr.setText(str(attr))

    def _parse(self):
        """ 
        Parsear os campos de entrada para OBIS, Classe e Atributo/Método
        """
        try:
            return self.inp_obis.text().strip(), int(self.inp_cls.text()), int(self.inp_attr.text())
        except ValueError:
            QMessageBox.warning(self, "Aviso", "Class/Attr precisam ser inteiros.")
            return None, None, None

    def _do_get(self):
        """ 
        Realiza um GET usando os valores dos campos de OBIS,                        \
            Classe e Atributo, e exibe o resultado formatado.
            Para o objeto de Load Profile (1.0.99.1.0.255) com atributo 2 (buffer),     \
                o software primeiro consulta o número de entradas (attr 7)              \
                e depois lê apenas as últimas 10 entradas usando acesso seletivo
        """
        obis, cls, attr = self._parse()
        if not obis or not self.client: return
        try:
            if obis == "1.0.99.1.0.255" and attr == 2:
                entries = self.client.send_get(obis, cls, 7)
                if isinstance(entries, int) and entries > 0:
                    n = min(10, entries)
                    val = self.client.send_get(obis, cls, 2,
                                               selective=(entries-n+1, entries))
                else:
                    val = self.client.send_get(obis, cls, attr)
            else:
                val = self.client.send_get(obis, cls, attr)
            self._show(format_value(val), C["accent"])
            self.log.get(obis, val)
        except Exception as e:
            self._show(f"ERRO: {e}", C["red"])
            self.log.err(str(e))
        self.wire.update_from_client(self.client)

    def _do_set(self):
        """
        O valor do SET é enviado como string, e o software tenta adivinhar o formato correto (int, str, etc)
            baseado no catálogo de OBIS. Se o formato for complexo ou não for possível adivinhar, o valor é enviado como string
        """
        obis, cls, attr = self._parse()
        val = self.inp_val.text().strip()
        if not obis or not val or not self.client:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos e o valor.")
            return
        try:
            res = self.client.send_set(obis, cls, attr, val)
            self._show(res, C["orange"])
            self.log.set_(obis, val)
        except Exception as e:
            self._show(f"ERRO: {e}", C["red"])
            self.log.err(str(e))
        self.wire.update_from_client(self.client)

    def _do_action(self):
        """
        O campo de valor é ignorado no ACTION, pois o software tenta adivinhar o formato correto (int, str, etc)
            baseado no catálogo de OBIS. Se o formato for complexo ou não for possível adivinhar, o valor é enviado como string
        """
        obis, cls, method = self._parse()
        if not obis or not self.client: return
        try:
            res = self.client.send_action(obis, cls, method)
            self._show(res, C["purple"])
            self.log.act(obis, res)
        except Exception as e:
            self._show(f"ERRO: {e}", C["red"])
            self.log.err(str(e))
        self.wire.update_from_client(self.client)


##########################################################################
# JANELA PRINCIPAL - Quando inicialize o software
##########################################################################
class MainWindow(QMainWindow):
    """
    Janela principal da aplicação, contendo o header, painel de abas e wire inspector
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DLMS / COSEM Station · IEC 62056-47 · Low Auth")
        self.setMinimumSize(1400, 820)
        self.client = None
        self._tabs_list = []
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        #### HEADER ####
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"background:{C['panel']};"
                             f"border-bottom:2px solid {C['accent']};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 0, 18, 0)
        hl.setSpacing(14)

        logo = QLabel(icons["home"] + " DLMS / COSEM STATION")
        logo.setStyleSheet(f"font-size:13pt; font-weight:bold; color:{C['accent']};"
                           f"letter-spacing:3px; background:none; border:none;")
        hl.addWidget(logo)

        sub = QLabel("IEC 62056-47 · TCP / WRAPPER · LN · Low Auth")
        sub.setStyleSheet(f"font-size:8pt; color:{C['muted']};"
                          f"background:none; border:none;")
        hl.addWidget(sub)

        hl.addStretch()

        for lbl, attr, windows, default in [
            ("HOST",  "inp_host", 130, "127.0.0.1"),
            ("PORT",  "inp_port",  60, "4063"),
        ]:
            l = QLabel(lbl)
            l.setStyleSheet(f"font-size:8pt; font-weight:bold; color:{C['muted']};"
                            f"background:none; border:none;")
            hl.addWidget(l)
            inp = QLineEdit(default)
            inp.setFixedWidth(windows)
            setattr(self, attr, inp)
            hl.addWidget(inp)

        self.btn_conn = QPushButton(icons['seta_direita'] + "  AARQ Low")
        self.btn_conn.setStyleSheet(btn_style(C["green_dim"], C["green"]))
        self.btn_conn.clicked.connect(self._connect)
        hl.addWidget(self.btn_conn)

        self.btn_disc = QPushButton(icons['seta_esquerda'] + "  RLRQ")
        self.btn_disc.setStyleSheet(btn_style(C["red_dim"], C["red"]))
        self.btn_disc.clicked.connect(self._disconnect)
        self.btn_disc.setEnabled(False)
        hl.addWidget(self.btn_disc)

        self.status_pill = StatusPill()
        hl.addWidget(self.status_pill)

        root.addWidget(header)

        # Corpo da aplicação (direito: wire inspector, esquerdo: abas)
        body = QSplitter(Qt.Orientation.Horizontal)
        body.setHandleWidth(2)

        #### Painel esquerdo (abas) ####
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(10, 10, 5, 10)
        ll.setSpacing(8)

        self.log_console = LogConsole()
        self.wire = WireInspector()
        self.tab_status  = StatusTab(self.log_console, self.wire)
        self.tab_read    = ReadingsTab(self.log_console, self.wire)
        self.tab_profile = ProfileTab(self.log_console, self.wire)
        self.tab_console = ConsoleTab(self.log_console, self.wire)
        self._tabs_list = [self.tab_status, self.tab_read, self.tab_profile, self.tab_console]

        self.tabs = QTabWidget()
        self.tabs.setEnabled(False)
        # Adiciona as abas com ícones e títulos
        self.tabs.addTab(self.tab_status,  f"{icons['aba_status']}  Status")
        self.tabs.addTab(self.tab_read,    f"{icons['aba_leituras']}  Leituras")
        self.tabs.addTab(self.tab_profile, f"{icons['aba_profile']}  Profile")
        self.tabs.addTab(self.tab_console, f"{icons['aba_console']}   Console")
        ll.addWidget(self.tabs, 1)

        log_g = QGroupBox("LOG DE OPERAÇÕES")
        lg = QVBoxLayout(); lg.setContentsMargins(6, 2, 6, 6)
        lg.addWidget(self.log_console)
        log_g.setLayout(lg)
        ll.addWidget(log_g)

        body.addWidget(left)

        #### Painel direito (wire inspector) ####
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(5, 10, 10, 10)
        rl.addWidget(self.wire)
        body.addWidget(right)

        body.setSizes([900, 500])
        root.addWidget(body, 1)

        #### Variáveis de controle ####
        self._t_start = None
        self._uptime_timer = QTimer()
        self._uptime_timer.timeout.connect(self._tick_uptime)

    def _connect(self):
        """ 
        Função que estabelece associação DLMS com os dados da interface e atualiza o status da aplicação 
        """
        host = self.inp_host.text().strip()
        try:
            port = int(self.inp_port.text())
        except ValueError:
            QMessageBox.warning(self, "Aviso", "Porta inválida.")
            return

        self.status_pill.set_connecting()
        self.btn_conn.setEnabled(False)
        self.log_console.info(f"Conectando a {host}:{port} (Low Auth)...")
        QApplication.processEvents()

        try:
            self.client = DLMSClient(host, port)
            self.client.connect()
            for t in self._tabs_list:
                t.client = self.client
            self.status_pill.set_online()
            self.tabs.setEnabled(True)
            self.btn_disc.setEnabled(True)
            self.inp_host.setEnabled(False)
            self.inp_port.setEnabled(False)
            self._t_start = datetime.datetime.now()
            self._uptime_timer.start(1000)
            self.log_console.ok(f"AARQ Low aceito por {host}:{port}")
            self.wire.update_from_client(self.client)
        except Exception as e:
            self.status_pill.set_offline()
            self.btn_conn.setEnabled(True)
            self.log_console.err(f"Falha: {e}")
            QMessageBox.critical(self, "Erro de Conexão",
                f"Não foi possível estabelecer associação DLMS.\n\n{e}\n\n" \
                "Verifique o servidor e a porta.")

    def _disconnect(self):
        """
        Função que envia RLRQ para encerrar a associação e atualiza o status da aplicação 
        """
        try: self.client.disconnect()
        except Exception: pass
        self.status_pill.set_offline()
        self.tabs.setEnabled(False)
        self.btn_conn.setEnabled(True)
        self.btn_disc.setEnabled(False)
        self.inp_host.setEnabled(True)
        self.inp_port.setEnabled(True)
        self._uptime_timer.stop()
        self.log_console.warn("RLRQ enviado, associação liberada.")

    def _tick_uptime(self):
        """
        Função que atualiza o título da janela com o tempo de sessão desde a conexão 
        """
        if self._t_start:
            d = datetime.datetime.now() - self._t_start
            h, r = divmod(int(d.total_seconds()), 3600)
            m, s = divmod(r, 60)
            self.setWindowTitle(
                f"DLMS / COSEM Station · Sessão {h:02d}:{m:02d}:{s:02d}")


def excepthook(et, ev, etb):
    """ 
    Função para capturar exceções não tratadas e exibir um diálogo de erro
    """
    tb = "".join(traceback.format_exception(et, ev, etb))
    print("\n--- ERRO ---\n", tb)
    try: QMessageBox.critical(None, "Erro Crítico", tb)
    except Exception: pass

if __name__ == "__main__":
    sys.excepthook = excepthook
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    windows = MainWindow()
    windows.show()
    sys.exit(app.exec())