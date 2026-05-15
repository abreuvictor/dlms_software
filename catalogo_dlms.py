"""
TCC file: catalogo_dlms.py
Autor: Victor de Abreu Viana
Descrição: Código para descobrir dinamicamente o catálogo COSEM exposto pelo Gurux Server Example.
"""

import socket
from gurux_dlms import GXDLMSClient, GXReplyData
from gurux_dlms.enums import InterfaceType, Authentication
from gurux_dlms.objects import GXDLMSAssociationLogicalName

HOST = "127.0.0.1"
PORT = 4063

client = GXDLMSClient(
    True, 
    17,
    1,
    Authentication.LOW,
    "Gurux",
    InterfaceType.WRAPPER
)

sock = socket.socket()
sock.settimeout(5)
sock.connect((HOST, PORT))
print(f"--> TCP conectado em {HOST}:{PORT}")

def send_recv(data_list):
    """ 
    Função que envia uma lista de mensagens e aguarda as respostas
    Args:
        data_list (list): Lista de mensagens a serem enviadas.
        
    Returns:
        GXReplyData: Objeto contendo a resposta recebida.
    """
    reply = GXReplyData()
    if not isinstance(data_list, list):
        data_list = [data_list]
    for tx in data_list:
        sock.sendall(bytes(tx))
        while True:
            client.getData(bytearray(sock.recv(4096)), reply)
            if reply.isMoreData():
                rr = client.receiverReady(reply.moreData)
                sock.sendall(bytes(rr))
                continue
            if reply.complete:
                break
    return reply

# Conexão AARQ
reply = send_recv(client.aarqRequest())
client.parseAareResponse(reply.data)
print("--> Associação Low estabelecida\n")
print("Lendo 'object_list' da Association LN...\n")
assoc = GXDLMSAssociationLogicalName()
reply = send_recv(client.read(assoc, 2))

# Atualiza o objeto local com os dados recebidos
client.updateValue(assoc, 2, reply.value)
objs = assoc.objectList

# Printar cada OBIS presente
print(f"{'OBIS':<22} {'CLASS':<6} {'VER':<4} {'TIPO'}")
print("-" * 80)
for obj in objs:
    cls = int(obj.objectType)
    tipo = obj.objectType.name if hasattr(obj.objectType, "name") else str(obj.objectType)
    print(f"{obj.logicalName:<22} {cls:<6} {obj.version:<4} {tipo}")

print(f"\n TOTAL: {len(objs)} objetos\n")

# Atributos
print("="*80)
print("ATRIBUTOS POR OBJETO")
print("="*80)

for obj in objs:
    print(f"\n{obj.logicalName}  ({obj.objectType.name})")
    n = obj.getAttributeCount()
    for i in range(1, n + 1):
        try:
            access = obj.getAccess(i)
            print(f"  attr={i}  access={access}")
        except Exception as e:
            print(f"  attr={i}  erro: {e}")

# Lista Finalizada
release = client.releaseRequest()
if release:
    for tx in release:
        sock.sendall(bytes(tx))
        try: sock.recv(4096)
        except: pass

sock.close()