# Smart TV OS — Linux

Esta pasta contém a edição Linux experimental do Smart TV for Windows. A interface web é preservada; o backend em Python integra o launcher com aplicativos Linux nativos e Flatpak.

## O que esta etapa entrega

- Backend HTTP limitado a 127.0.0.1:48765.
- Descoberta de lançadores de aplicativos do Debian, do usuário e de instalações Flatpak.
- Abertura segura de aplicativos sem shell.
- Integração opcional com Steam Big Picture quando a Steam estiver instalada.
- Interface Smart TV em tela cheia usando Chromium e suporte à Gamepad API.
- Base de ISO Live Debian 13 Trixie amd64 com KDE Plasma.
- Loja KDE Discover e backend Flatpak incluídos na lista de pacotes da imagem.

## Guia para baixar, testar e instalar

**Leia antes de criar o pendrive ou mexer nas partições do Windows:**

➡️ **[Guia completo da ISO, pendrive, particionamento e dual boot](GUIA-INSTALACAO.md)**

O guia explica a diferença entre a ISO no pendrive e o espaço que deve ser reservado no HD/SSD, como conferir o BitLocker, liberar espaço no Windows, testar o modo Live e o que deve ser preservado no particionamento.

> **Estado experimental:** o Calamares incluído na ISO usa configuração genérica. O fluxo de instalação permanente e dual boot ainda precisa de validação em hardware real. A recomendação atual é testar pelo pendrive e não instalar no disco principal com Windows até essa validação.

## Rodar em um Debian já instalado

Na base Debian 13 amd64:

    sudo apt update
    sudo apt install python3 chromium curl
    ./linux/run.sh

Para instalar a interface e o launcher somente na conta do usuário atual:

    ./linux/install-user.sh

Esse instalador por usuário não particiona discos e não altera o bootloader.

## Construir a ISO

Em Debian 13 amd64, instale as ferramentas:

    sudo apt update
    sudo apt install live-build debootstrap squashfs-tools xorriso
    sudo linux/build-iso.sh

A imagem esperada é out/SmartTV-OS-live-trixie-amd64.iso.

## Testes do backend

    python3 -m unittest discover -s linux -p 'test_*.py'

A ISO só deve ser considerada estável depois de testes de boot UEFI, dual boot com Windows 10/11, atualização do GRUB, áudio, controle USB/Bluetooth, Wi-Fi, codecs e aceleração gráfica.
