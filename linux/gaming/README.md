# Perfis de jogos no Smart TV OS

O Smart TV OS oferece dois perfis separados:

- **Modo TV (padrão):** use jogos na nuvem a partir do próprio computador da TV. Xbox Cloud Gaming, GeForce NOW (incluindo títulos Steam habilitados por Steam Cloud Play) e Boosteroid abrem em janelas Chromium de tela cheia. Não é necessário manter um segundo PC ligado.
- **Modo Console (opcional):** instala Steam e os componentes locais de jogos quando o usuário roda o instalador gamer. A biblioteca Steam é instalada e executada no próprio computador; não há streaming de jogo pela rede.

## Modo TV

A ISO base inclui somente desktop, Chromium, áudio, Bluetooth/controles, aceleração Mesa/Vulkan, Discover/Flatpak, Kodi e VLC. Ela não instala Steam, Wine/Proton, Lutris, GameMode, MangoHud ou emuladores.

Os atalhos de Xbox Cloud Gaming, GeForce NOW e Boosteroid ficam disponíveis no botão **Jogos na nuvem**. Cada provedor usa um perfil persistente e separado de Chromium em `~/.local/share/smart-tv/cloud-profiles/`.

Veja [Jogos na nuvem e compatibilidade dos provedores](../cloud-gaming/README.md) para os requisitos, Steam Cloud Play e limitações específicas de Debian 13.

## Modo Console

Em Ajustes do Início, selecione **Modo Console (jogos locais)**. Depois, no desktop, execute **Instalar extras de jogos** ou:

    sudo /usr/local/bin/smart-tv-install-gaming

O instalador usa somente os manifestos instalados em `/usr/share/smarttv-gaming/`:
- `console-apt-packages.txt`: Steam Installer, bibliotecas gráficas i386, GameMode, MangoHud, Lutris, Wine 32/64 bits, Winetricks, DOSBox e ScummVM;
- `console-flatpaks.txt`: Heroic, Bottles, ProtonUp-Qt, RetroArch, Dolphin, PPSSPP, PCSX2 e RPCS3;
- `console-backports-packages.txt`: Gamescope, de Debian Trixie Backports.

A ISO base não inclui esses pacotes de Console. O instalador exige Debian 13 Trixie amd64, adiciona i386 e habilita Backports somente no momento da instalação opcional. Antes de instalar, ele pede confirmação.

Para validar sem root, sem rede e sem modificar o sistema:

    SMARTTV_GAMING_MANIFEST_DIR=linux/profiles bash linux/gaming/install-extras.sh --print-plan

## Biblioteca e desempenho locais

O backend lê manifestos das bibliotecas Steam e exibe os jogos instalados no painel **Jogos**. Um jogo é aberto pela própria Steam em Big Picture. Para jogos Steam/Proton, as opções de inicialização podem receber `gamemoderun %command%` ou `MANGOHUD=1 %command%`. O GameMode/MangoHud da UI aplica-se diretamente aos jogos Linux nativos reconhecidos pelo desktop.

Mantenha a biblioteca Steam em ext4 ou outro armazenamento Linux adequado; não recomendamos partilhar a mesma biblioteca/proton prefixes com o Windows numa partição NTFS.

## Validação automatizada

A suíte `linux/test.sh` verifica:
- separação entre a lista APT do Modo TV e as listas Console;
- execução `--print-plan` comparada aos três manifestos reais;
- perfis persistentes e API;
- detecção de clientes de nuvem e jogos Steam;
- inicialização dos atalhos cloud sem rede e com diretórios de sessão isolados;
- sintaxe Python, JavaScript e shell.

Esses testes verificam composição e orquestração, não substituem o teste real de decodificação de vídeo, login, controles e latência em hardware físico.

## Limites

Nem todo título funciona com Proton/Wine, e anti-cheat/DRM podem impedir jogos locais. Emuladores não incluem ROMs, BIOS ou firmware. O GeForce NOW nativo para Linux exige Ubuntu 24.04 oficialmente; no Debian 13 o atalho usa o navegador e precisa de validação física. Boosteroid oferece app Linux próprio em beta e pacote DEB para Debian 11+; a ISO não instala esse cliente de terceiros por padrão.
