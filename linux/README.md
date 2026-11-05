# Smart TV OS — Linux

Esta pasta contém a edição Linux experimental do Smart TV for Windows. A interface web é preservada; o backend em Python integra o launcher com aplicativos Linux nativos e Flatpak.

## O que esta etapa entrega

- Backend HTTP limitado a 127.0.0.1:48765.
- Descoberta de lançadores de aplicativos do Debian, do usuário e de instalações Flatpak.
- Abertura segura de aplicativos sem shell.
- Modo TV leve por padrão, com áudio PipeWire, Bluetooth, aceleração Mesa/Vulkan e KDE Discover/Flathub; atalhos de Xbox Cloud Gaming, GeForce NOW/Steam Cloud Play e Boosteroid executam jogos em nuvem no próprio computador conectado à TV.
- A ISO desta branch é exclusivamente Modo TV: não instala Steam, Lutris, Wine/Proton nem emuladores. Os atalhos de Xbox Cloud Gaming, GeForce NOW/Steam Cloud Play e Boosteroid continuam disponíveis. A edição Console será distribuída separadamente.
- Biblioteca Jogos no Modo Console, com descoberta de títulos Steam e execução local em Big Picture, sem streaming. Steam Link/Moonlight ficam como alternativas secundárias que exigem outro PC na rede.
- Interface Smart TV em tela cheia usando Chromium e suporte à Gamepad API; o botão de jogos muda entre **Jogos na nuvem** (Modo TV) e **Jogos locais** (Modo Console).
- Base de ISO Live Debian 13 Trixie amd64 com KDE Plasma.
- Loja KDE Discover, backend Flatpak e catálogo Flathub configurado na imagem.
- UxPlay e Avahi para recepção AirPlay Mirror básica, iniciada manualmente pelo atalho Receber AirPlay e protegida por PIN.
- VibeCast v0.2.0 compilado para o receptor Google Cast, com player web local anunciado como **TV Sala**; o serviço é iniciado manualmente e requer material privado válido de autenticação Cast que não acompanha a ISO.

## Guia para baixar, testar e instalar

**Leia antes de criar o pendrive ou mexer nas partições do Windows:**

➡️ **[Guia completo da ISO, pendrive, particionamento, loja e AirPlay](GUIA-INSTALACAO.md)**  
➡️ **[Visão do produto: interface premium, streaming, AirPlay, Android Cast e controle por celular](VISAO-TV-EXPERIENCIA.md)**  
➡️ **[Integração gamer: Steam, Heroic, Lutris, Proton, Wine, controles e emuladores](gaming/README.md)**
➡️ **[Jogos na nuvem: Xbox Cloud Gaming, GeForce NOW/Steam Cloud Play e Boosteroid](cloud-gaming/README.md)**  
➡️ **[Cast nativo nos apps: destino TV Sala e compatibilidade por serviço](CAST-APPS-E-RECEPTORES.md)**

O guia explica a diferença entre a ISO no pendrive e o espaço que deve ser reservado no HD/SSD, como conferir o BitLocker, liberar espaço no Windows, testar o modo Live e o que deve ser preservado no particionamento. A ISO desta branch mantém o Modo TV e oferece atalhos de serviços de jogos na nuvem. Componentes de jogos locais não fazem parte desta imagem.

 > **Estado experimental e segurança:** o Calamares incluído nesta imagem ainda usa configuração genérica do Debian; não existe ainda um assistente Smart TV OS personalizado com detecção validada de Windows/EFI, revisão de partições e proteção comprovada contra formatação. Portanto, não execute a instalação no disco que contém o Windows. O boot Live e os testes automatizados não validam instalação permanente nem dual boot. AirPlay Mirror é básico (não AirPlay 2 completo). Compatibilidade por aplicativo do Cast TV Sala ainda precisa ser testada; o receptor está integrado, mas não funciona sem arquivo privado válido de autenticação Cast. Google Cast universal, recepção Miracast, controle remoto próprio por celular e interface visual final continuam em desenvolvimento. A Netflix atualmente restringe o Cast do app móvel a uma lista limitada de aparelhos; receiver Linux genérico não tem compatibilidade confirmada. A recomendação atual é testar pelo pendrive e não instalar no disco principal com Windows até a validação.

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

A camada gamer também depende da GPU/driver, das bibliotecas 32-bit, dos launchers e dos requisitos de cada jogo. Anti-cheat e DRM podem bloquear títulos no Wine/Proton. Emuladores não incluem ROMs, BIOS ou firmware.

A ISO só deve ser considerada estável depois de testes de boot UEFI, dual boot com Windows 10/11, atualização do GRUB, áudio, controle USB/Bluetooth, Wi-Fi, codecs e aceleração gráfica.
