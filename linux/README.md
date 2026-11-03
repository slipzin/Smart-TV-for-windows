# Smart TV OS — Linux e dual boot

Esta pasta inicia a migração do Smart TV for Windows para uma edição Linux. A interface `web/` é preservada; `smarttv.py` substitui a camada de integração PowerShell/Win32 por um backend local Linux compatível com a API que a interface já consome.

## O que esta etapa entrega

- Backend HTTP limitado a `127.0.0.1:48765`; não escuta na rede.
- Descoberta de lançadores `.desktop` do Debian, do usuário e de instalações Flatpak.
- Abertura de programas por argv, sem `shell=True`.
- Steam no modo Big Picture; detecção opcional de um jogo Steam pelo manifesto instalado.
- Integração das APIs existentes de apps, configurações, informações do sistema, início automático, wallpapers e saída.
- Wallpapers em `~/Pictures/SmartTV/Fundos`, inclusive vídeo com requisições HTTP Range.
- Launcher Chromium em quiosque, usando a Gamepad API existente na tela.

## Rodar em um Debian já instalado

Base de referência: Debian 13 Trixie amd64. O Debian 13 é a versão estável atual; em 3 de novembro de 2026, a revisão estável publicada é 13.7.

Instale os componentes mínimos:

    sudo apt update
    sudo apt install python3 chromium curl
    ./linux/run.sh

Para instalar a interface e o launcher na conta do usuário atual:

    ./linux/install-user.sh

O instalador por usuário não particiona discos e não modifica o bootloader.

## Construir uma ISO Live experimental

Em uma máquina Debian 13 amd64, instale as ferramentas de build:

    sudo apt update
    sudo apt install live-build debootstrap squashfs-tools xorriso
    sudo linux/build-iso.sh

A saída esperada é `out/SmartTV-OS-live-trixie-amd64.iso`. Ela é uma imagem híbrida para teste em VM e pendrive; a construção ainda precisa ser executada e validada em uma máquina Debian real. O pacote `calamares-settings-debian` fornece uma configuração inicial do instalador genérico. A marca, os módulos, o fluxo de dual boot e as mensagens ainda precisam de validação e personalização antes de uma versão pública.

## Instalação permanente ao lado do Windows

A meta da arquitetura é instalar o Linux numa partição separada, reutilizar a partição EFI sem formatá-la e configurar o GRUB para permitir escolher Windows ou Smart TV OS. O protótipo ISO não executa particionamento destrutivo automaticamente nem substitui o Windows.

1. Faça backup dos dados importantes.
2. No Windows, desative a Inicialização Rápida. Se o BitLocker estiver ativo, guarde a chave de recuperação e suspenda a proteção antes de mexer no boot.
3. No Gerenciamento de Disco do Windows, reduza a partição do Windows e deixe espaço **não alocado** para o Linux.
4. Inicialize o USB no mesmo modo de firmware usado pelo Windows — normalmente UEFI.
5. No Calamares, revise cuidadosamente o particionamento. Se não houver uma opção explícita e correta para instalar ao lado do Windows, use apenas o particionamento manual no espaço não alocado reservado; não formate a partição EFI ou a partição NTFS do Windows.
6. Confirme o destino do carregador de inicialização antes de iniciar a instalação.

Não prossiga se o instalador não identificar com clareza a partição Linux e a ESP. Secure Boot, BitLocker, Intel RST/VMD, placas NVIDIA, Wi-Fi, suspensão e múltiplas GPUs exigem testes em hardware real. Não há garantia de dual boot automático em todo computador.

## Aplicativos e jogos

Programas com lançadores `.desktop` aparecem automaticamente. Steam abre em Big Picture; Kodi, VLC, Plex, Jellyfin, Lutris, Bottles e Moonlight entram no catálogo quando instalados. A compatibilidade de cada jogo depende de Proton, drivers, GPU e sistemas antitrapaça. Apps de streaming que não tenham cliente Linux podem exigir navegador e DRM compatível.

## Testes

    python3 -m unittest discover -s linux -p 'test_*.py'

A ISO não deve ser considerada estável até passar por testes de boot UEFI, dual boot com instalações Windows 10/11, atualização do GRUB, áudio, controle USB/Bluetooth, Wi-Fi, codecs e aceleração gráfica.
