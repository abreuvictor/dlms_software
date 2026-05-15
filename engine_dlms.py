"""
TCC file: engine_dlms.py — Motor de Comunicação DLMS/COSEM
Autor: Victor de Abreu Viana
Descriçao: Implementação de um motor de comunicação DLMS/COSEM em Python,
    capaz de se conectar a um servidor DLMS usando o transporte WRAPPER, 
    realizar associação AARQ com autenticação Low, e executar operações GET, SET e ACTION. 
    
###########################################################################################

Validado usando o Gurux DLMS Server Example (porta 4063, LN+WRAPPER, Low Auth).

Funções Importantes:
  - AARQ Low Authentication (usando senha "Gurux", ClientSAP=17)
  - GET, SET, ACTION
  - "Selective access" (Profile Generic, entry-descriptor)
  - Codec BER-TLV recursivo (array, structure aninhados)
  - Thread-safe via threading.Lock
"""

import socket
import struct
import datetime
import threading

class DLMSClient:
    _invoke_seq = 0x01

    def __init__(self, host="127.0.0.1", port=4063):
        self.host = host
        self.port = port
        self.sock = None
        self._lock = threading.Lock()
        self.last_tx = b""       
        self.last_rx = b""       

    def _next_invoke(self) -> int:
        """ 
        Gera o próximo número de invoke para as requisições DLMS, 
        garantindo que seja entre 1 e 255.
        
        Returns:
            - O próximo número de invoke a ser usado em uma requisição DLMS.
        """
        invoke = DLMSClient._invoke_seq
        DLMSClient._invoke_seq = (DLMSClient._invoke_seq % 255) + 1
        return invoke

    ##########################################################################
    # Função para Conexão / Desconexão
    ##########################################################################
    
    def connect(self):
        """
        Função que estabelece conexão TCP e envia AARQ Low com a senha 'Gurux' (ClientSAP=17)
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10.0)
        self.sock.connect((self.host, self.port))
        aarq_apdu = bytes.fromhex(
            "6033"
            "A109" "0607" "60857405080101"
            "8A02" "0780"
            "8B07" "60857405080201"
            "AC07" "80054775727578"
            "BE10" "040E"
            "01000000065F1F0400401E5DFFFF"
            )
        self._send_wrapper(aarq_apdu)
        self._recv_frame()

    def disconnect(self):
        """
        Função que finaliza a conexão TCP com o server
        """
        if self.sock:
            try:
                self._send_wrapper(bytes([0x62, 0x00]))
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    ##########################################################################
    # Função para o transporte WRAPPER
    ##########################################################################
    
    def _send_wrapper(self, apdu: bytes, src: int = 0x0011, dst: int = 0x0001):
        """ 
        Função que envia um APDU através do transporte WRAPPER com o header correto 
            (Source SAP, Destination SAP, Length) e guarda o último APDU enviado.
        
        Args:
            - apdu: bytes do APDU a ser enviado
            - src: Source SAP (padrão 0x0011 para o cliente)
            - dst: Destination SAP (padrão 0x0001 para o servidor)
        """
        header = struct.pack(">HHHH", 0x0001, src, dst, len(apdu))
        packt = header + apdu
        self.last_tx = packt
        self.sock.sendall(packt)

    def _recv_exact(self, n: int) -> bytes:
        """ 
        Função que recebe exatamente n bytes do socket
        
        Args:
            - n: número de bytes a serem recebidos
            
        Returns:
            - Os bytes recebidos
        """
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Conexão encerrada pelo servidor")
            buf += chunk
        return buf

    def _recv_frame(self) -> bytes:
        """ 
        Função que recebe um frame completo do transporte WRAPPER
            
        Returns:
            - O frame completo recebido
        """
        hdr = self._recv_exact(8)
        _, _, _, n = struct.unpack(">HHHH", hdr)
        frame = hdr + self._recv_exact(n)
        self.last_rx = frame         
        return frame

    ##########################################################################
    # Função DLMS - GET
    ##########################################################################
    
    def send_get(self, obis_str: str, class_id: int = 1, attr_id: int = 2,
             selective: tuple = None):
        """ 
        Função que envia uma requisição GET para o servidor DLMS
        
        Args:
            - obis_str: string com o OBIS code;
            - class_id: ID da classe DLMS;
            - attr_id: ID do atributo;
            - selective: tupla (inicio, fim).

        Returns:
            - O valor retornado pela requisição GET
        """
        with self._lock:
            obis_b = bytes(int(x) for x in obis_str.split("."))
            invoke = self._next_invoke()

            if selective is None:
                access = bytes([0x00])
            else:
                from_entry, to_entry = selective
                access = bytes([0x01, 0x02, 0x02, 0x04, 0x06, *struct.pack(">I", from_entry),
                    0x06, *struct.pack(">I", to_entry), 0x12, 0x00, 0x01, 0x12, 0x00, 0x00])

            apdu = (bytes([0xC0, 0x01, invoke]) + struct.pack(">H", class_id)
                    + obis_b + bytes([attr_id]) + access)
            self._send_wrapper(apdu)

            # Responsável por receber o primeiro frame
            resp = self._recv_frame()
            if len(resp) < 12:
                return "Erro!"
            if resp[8] != 0xC4:
                return f"Erro: tag inesperado 0x{resp[8]:02X}"

            variant = resp[9]

            ###### GetResponseNormal (com a resposta inteira) ######
            if variant == 0x01:
                if resp[11] != 0x00:
                    err = resp[12] if len(resp) > 12 else 0
                    return f"Rejeitado (DataAccessResult=0x{err:02X})"
                return self._decode_value(resp[12:])

            ###### GetResponseWithDataBlock: (com a resposta bloco a bloco) ######
            if variant == 0x02:
                return self._read_blocks(resp, invoke, class_id, obis_b, attr_id)

            return f"Erro: variant 0x{variant:02X} não suportado"

    def _read_blocks(self, first_resp: bytes, invoke: int,
                    class_id: int, obis_b: bytes, attr_id: int):
        """
        Função responsável por estruturar as respostas fragmentadas \
            (função GetResponseWithDataBlock)
            
        Args:
            - first_resp: bytes do primeiro frame recebido;
            - invoke: número de invoke usado na requisição;
            - class_id, obis_b, attr_id: parâmetros da requisição original.
                
        Returns:
            - Valor decodificado;
            - Mensagem de erro.
        """
        accumulated = bytearray()
        resp = first_resp

        while True:
            apdu = resp[8:]
            if len(apdu) < 9 or apdu[0] != 0xC4 or apdu[1] != 0x02:
                return f"Erro: bloco mal formado"
            last_block = apdu[3]                                  
            # 0 = possui mais blocos
            # 1 = último bloco
            block_num  = struct.unpack(">I", apdu[4:8])[0]
            # data_len pode ser 1 byte (curto) 
            # começar com 0x81/0x82 (longo)
            idx = 8
            n = apdu[idx]
            if n == 0x81:
                n = apdu[idx + 1]
                idx += 2
            elif n == 0x82:
                n = struct.unpack(">H", apdu[idx + 1:idx + 3])[0]
                idx += 3
            else:
                idx += 1
            accumulated += apdu[idx:idx + n]
            if last_block == 0x01:
                break

            # Solicita o próximo bloco: GetRequestNext
            next_apdu = (bytes([0xC0, 0x02, invoke])
                        + struct.pack(">I", block_num))
            self._send_wrapper(next_apdu)
            resp = self._recv_frame()

        return self._decode_value(bytes(accumulated))

    ##########################################################################
    # Função DLMS - SET
    ##########################################################################
    
    def send_set(self, obis_str: str, class_id: int, attr_id: int, value) -> str:
        """ 
        Função responsável por enviar um comando SET para o servidor DLMS, com o valor codificado em BER-TLV
        
        Args:
            - obis_str: string no formato "X.X.X.X.X.X";
            - class_id: ID da classe do objeto;
            - attr_id: ID do atributo a ser escrito;
            - value: valor a ser escrito, podeno ser um int, float, string ou bytes.
            
        Returns:
            - "Sucesso" se a escrita for bem-sucedida;
            - "Erro: <descrição>" em caso de falha, com detalhes do motivo
        """
        with self._lock:
            obis_b = bytes(int(x) for x in obis_str.split("."))
            data_enc = self._encode(value)
            invoke = self._next_invoke()
            apdu = (bytes([0xC1, 0x01, invoke])
                    + struct.pack(">H", class_id)
                    + obis_b
                    + bytes([attr_id, 0x00])
                    + data_enc)
            self._send_wrapper(apdu)

            resp = self._recv_frame()
            if len(resp) < 12:
                return "Erro: pacote truncado"
            if resp[8] != 0xC5:
                return f"Erro: tag inesperado 0x{resp[8]:02X}"
            result = resp[11]
            if result == 0x00:
                return "Sucesso"
            return f"Erro ao escrever (DataAccessResult=0x{result:02X})"

    ##########################################################################
    # Função DLMS - ACTION
    ##########################################################################
    
    def send_action(self, obis_str: str, class_id: int, method_id: int,
                    enum_param: int = None) -> str:
        """ 
        Função responsável por enviar um comando ACTION para o servidor DLMS
        
        Args:
            - obis_str: string no formato "X.X.X.X.X.X";
            - class_id: ID da classe;
            - method_id: ID do método;
            - enum_param: parâmetro opcional.
            
        Returns:
            - "Método executado com sucesso" se a execução for bem-sucedida;
            - "Falha na execução (ActionResult=0x{result:02X})" em caso de falha.
        """
        with self._lock:
            obis_b = bytes(int(x) for x in obis_str.split("."))
            invoke = self._next_invoke()
            if enum_param is not None:
                param_bytes = bytes([0x01, 0x16, enum_param & 0xFF])
            else:
                param_bytes = bytes([0x00])
            apdu = (bytes([0xC3, 0x01, invoke]) + struct.pack(">H", class_id)
                    + obis_b + bytes([method_id]) + param_bytes)
            self._send_wrapper(apdu)

            resp = self._recv_frame()
            if len(resp) < 12:
                return "Erro!"
            if resp[8] != 0xC7:
                return f"Erro: tag inesperado 0x{resp[8]:02X}"
            result = resp[11]
            if result == 0x00:
                return "Método executado com sucesso"
            return f"Falha na execução (ActionResult=0x{result:02X})"

    ##########################################################################
    # Codec COSEM — Decoder
    ##########################################################################
    
    @staticmethod
    def _decode(data: bytes, offset: int = 0):
        """ 
        Função que decodifica os dados conforme o formato BER-TLV 
        
        Args:
            - data: bytes para decodificar;
            - offset: posição inicial para decodificação (padrão 0).
        
        Returns:
            - O valor decodificado;
            - O novo offset.
        """
        if offset >= len(data):
            return None, offset
        tag = data[offset]
        offset += 1
        try:
            if tag == 0x00:
                return None, offset
            elif tag == 0x01:
                count = data[offset]; offset += 1
                items = []
                for _ in range(count):
                    val, offset = DLMSClient._decode(data, offset)
                    items.append(val)
                return items, offset
            elif tag == 0x02:
                count = data[offset]; offset += 1
                items = []
                for _ in range(count):
                    val, offset = DLMSClient._decode(data, offset)
                    items.append(val)
                return tuple(items), offset
            elif tag == 0x03:
                return bool(data[offset]), offset + 1
            elif tag == 0x04:
                n_bits = data[offset]; offset += 1
                n_bytes = (n_bits + 7) // 8
                raw = data[offset:offset+n_bytes]
                return f"bits[{n_bits}]=0x{raw.hex()}", offset + n_bytes
            elif tag == 0x05:
                v = struct.unpack(">i", data[offset:offset+4])[0]
                return v, offset + 4
            elif tag == 0x06:
                v = struct.unpack(">I", data[offset:offset+4])[0]
                return v, offset + 4
            elif tag == 0x09:
                n = data[offset]; offset += 1
                raw = data[offset:offset+n]; offset += n
                if n == 12:
                    return DLMSClient._decode_datetime(raw), offset
                try:
                    return raw.decode("ascii"), offset
                except UnicodeDecodeError:
                    return raw.hex(), offset
            elif tag == 0x0A:
                n = data[offset]; offset += 1
                return data[offset:offset+n].decode("ascii", errors="replace"), offset + n
            elif tag == 0x0F:
                v = struct.unpack(">b", bytes([data[offset]]))[0]
                return v, offset + 1
            elif tag == 0x10:
                v = struct.unpack(">h", data[offset:offset+2])[0]
                return v, offset + 2
            elif tag == 0x11:
                return data[offset], offset + 1
            elif tag == 0x12:
                v = struct.unpack(">H", data[offset:offset+2])[0]
                return v, offset + 2
            elif tag == 0x16:
                return data[offset], offset + 1
            elif tag == 0x17:
                v = struct.unpack(">f", data[offset:offset+4])[0]
                return round(v, 6), offset + 4
            elif tag == 0x18:
                v = struct.unpack(">d", data[offset:offset+8])[0]
                return round(v, 9), offset + 8
            elif tag == 0x19:
                return DLMSClient._decode_datetime(data[offset:offset+12]), offset + 12
            elif tag == 0x1A:
                v = struct.unpack(">f", data[offset:offset+4])[0]
                return round(v, 6), offset + 4
            elif tag == 0x1B:
                v = struct.unpack(">d", data[offset:offset+8])[0]
                return round(v, 9), offset + 8
            else:
                return f"<tag=0x{tag:02X}>", offset
        except Exception as e:
            return f"<erro tag=0x{tag:02X}: {e}>", offset

    @staticmethod
    def _decode_value(data: bytes):
        """ 
        Decodifica um valor único conforme o formato BER-TLV
        
        Args:
            - data: bytes do valor a ser decodificado
            
        Returns:
            - Valor decodificado ou uma mensagem de erro
        """
        val, _ = DLMSClient._decode(data, 0)
        return val

    @staticmethod
    def _fmt(value, verif, lenght):
        if value != verif:
            return f"{value:0{lenght}d}"
        else:
            return "?" * lenght
        
    @staticmethod
    def _decode_datetime(raw: bytes) -> str:
        """ 
        Decodifica um valor de data e hora conforme o formato BER-TLV
        
        Args:
            - raw: bytes do valor de data e hora a ser decodificado
            
        Returns:
            - Data e hora decodificados ou uma mensagem de erro
        """
        if len(raw) < 12:
            return f"datetime inválido ({raw.hex()})"
        try:
            yr, mo, dy, dow, h, mi, s, cs = struct.unpack(">HBBBBBBB", raw[:9])
            
            yr_s = DLMSClient._fmt(yr, 0xFFFF, 4)
            mo_s = DLMSClient._fmt(mo, 0xFF, 2)
            dy_s = DLMSClient._fmt(dy, 0xFF, 2)
            h_s  = DLMSClient._fmt(h,  0xFF, 2)
            mi_s = DLMSClient._fmt(mi, 0xFF, 2)
            s_s  = DLMSClient._fmt(s,  0xFF, 2)
                
            return f"{yr_s}-{mo_s}-{dy_s} {h_s}:{mi_s}:{s_s}"
        except Exception:
            return raw.hex()
        

    # -----------------------------------------------------------------------
    # Encoder (para função DLMS SET)
    # -----------------------------------------------------------------------
    @staticmethod
    def _encode(value) -> bytes:
        """
        Função responsável por codificar valor Python para BER-TLV.
        
        Args:
            - value: valor a ser codificado
            
        Returns:
            - Bytes codificados
        """
        ###### IF para bytes ######
        if isinstance(value, (bytes, bytearray)):
            return bytes(value)

        s = str(value).strip()

        ###### IF para date-time YYYY-MM-DD HH:MM:SS ######
        if (len(s) == 19 and s[4] == "-" and s[7] == "-"
                and s[10] == " " and s[13] == ":" and s[16] == ":"):
            try:
                dt = datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
                dow = dt.isoweekday()  
                # dias da semana começando pela segunda
                # 1 = segunda até 7 = domingo (seguindo formato DLMW/COSEM)
                payload = struct.pack(">HBBBBBBBHB",
                    dt.year, dt.month, dt.day, dow, dt.hour, dt.minute, dt.second,
                    0,         # centésimos de segundo
                    0x8000,    # deviation = not specified (seguindo DLMS)
                    0xFF)      # clock_status = not specified (seguindo DLMS)
                return bytes([0x09, 12]) + payload
            except ValueError:
                pass

        ###### IF para inteiro ######
        try:
            v = int(s)
            if 0 <= v <= 0xFF:
                return bytes([0x11, v])
            if 0 <= v <= 0xFFFF:
                return bytes([0x12]) + struct.pack(">H", v)
            if 0 <= v <= 0xFFFFFFFF:
                return bytes([0x06]) + struct.pack(">I", v)
            return bytes([0x05]) + struct.pack(">i", v)
        except ValueError:
            pass

        ###### IF para float32 ######
        try:
            v = float(s)
            return bytes([0x1A]) + struct.pack(">f", v)
        except ValueError:
            pass

        ###### IF para ASCII ######
        b = s.encode("ascii", errors="replace")
        return bytes([0x0A, len(b)]) + b