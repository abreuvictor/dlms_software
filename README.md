# DESENVOLVIMENTO DE SISTEMA DE SOFTWARE AUTOMATIZADO PARA GESTÃO DE MEDIDORES INTELIGENTES

## Trabalho de Conclusão de Curso - Engenharia de Controle e Automação

Instituto Federal de Educação, Ciência e Tecnologia do Ceará (IFCE) - Campus Maracanaú

Autor: Victor de Abreu Viana

---

Cliente DLMS/COSEM em Python para medidores inteligentes, com interface
gráfica em PyQt6.

Arquivos principais:

- `engine_dlms.py` - motor DLMS/COSEM para comunicação com o servidor Gurux
- `main_gui.py` - interface gráfica PyQt6
- `catalogo_dlms.py` - script de inspeção de OBIS

---

## Como executar (Windows)

### 1. Instalar o Python

Baixe o Python 3.10+.

### 2. Instalar servidor Gurux

O projeto se encontra no git:

```powershell
https://github.com/Gurux/Gurux.DLMS.Net
```

**Pré-requisitos:**
 
- [.NET 10 SDK](https://dotnet.microsoft.com/download/dotnet/10.0)
- [.NET Framework 4.8 Developer Pack](https://dotnet.microsoft.com/download/dotnet-framework/net48)
- [nuget.exe](https://dist.nuget.org/win-x86-commandline/latest/nuget.exe)

Provavelmente na execução do servidor Gurux terá de ser necessário restaurar os pacotes NuGet antigos (formato `packages.config`), pois o projeto é antigo e não foi migrado para o formato moderno de pacotes NuGet (`PackageReference`).

```
# Restaurar os pacotes NuGet antigos (formato packages.config)
nuget restore Gurux.DLMS.Server.Example\packages.config -PackagesDirectory packages

# Compilar e executar
cd Gurux.DLMS.Server.Example
dotnet build -c Release
```

O servidor ficará rodando no terminal nas portas 4060, 4061, 4062 e 4063.
Os scripts Python deste projeto usam a porta 4063 (Logical Name + WRAPPER).

### 3. Instalar as dependências Python

Em outra janela:

```powershell
pip install -r requirements.txt
```

### 4. Rodar os scripts

```powershell
python catalogo_dlms.py   # inspeciona o catálogo COSEM
python main_gui.py        # abre a GUI principal
```

A `main_gui.py` conecta em `127.0.0.1:4063` por padrão.

---