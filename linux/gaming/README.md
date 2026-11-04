# Jogos no Smart TV OS

O Smart TV OS tem dois perfis independentes. O padrão é **Modo TV**: interface leve para streaming de vídeo e jogos transmitidos de outro computador. O **Modo Console** é opcional e adiciona jogos executados localmente no próprio hardware.

## Modo TV — streaming leve

- Não instala Steam, Wine/Proton, Lutris, GameMode, MangoHud ou emuladores no perfil básico.
- O botão **Jogar via PC** lista clientes de streaming de jogos instalados.
- Pelo KDE Discover/Flathub, o usuário pode instalar:
  - **Moonlight**: Flatpak `com.moonlight_stream.Moonlight`. Na outra máquina, execute Sunshine (AMD/Intel/NVIDIA) ou um host GameStream compatível e faça o pareamento.
  - **Steam Link**: Flatpak `com.valvesoftware.SteamLink`. Na outra máquina, execute Steam e conecte os dois dispositivos pela rede local.
- O cliente da TV decodifica o vídeo e envia os comandos do controle. O computador host continua renderizando o jogo; portanto, isso reduz o trabalho no aparelho da TV, não o trabalho total do PC que roda o jogo.

## Modo Console — jogos locais

Ative **Modo Console (jogos locais)** em Ajustes do Início. O perfil apenas altera a interface; para instalar os componentes, saia do modo TV e execute **Instalar extras de jogos** no desktop (ou use o comando abaixo). A instalação é intencionalmente opt-in.

A biblioteca **Jogos** lê manifestos Steam e descobre launchers e jogos do Linux. Os jogos instalados pela Steam são iniciados localmente com Steam em Big Picture e `-applaunch`; não usam streaming nem um host remoto.


## O que a ISO prepara

- A base TV mantém Mesa/Vulkan para aceleração gráfica, áudio PipeWire, Bluetooth e Discover/Flathub.
- Steam Installer, Lutris, GameMode, MangoHud, Vulkan Tools e a camada Wine/Proton entram somente pela instalação opcional do Modo Console.
- Suporte a controle por navegador/Gamepad API no launcher Smart TV.
- Bluetooth (BlueZ/Blueman) para controles compatíveis.
- Descoberta de launchers e aplicativos de jogos por arquivos .desktop e Flatpak.
- Biblioteca Jogos separada de Todos os Apps, com detecção de entradas da categoria freedesktop Game.
- Leitura dos manifestos das bibliotecas Steam e inicialização dos jogos instalados diretamente por Steam em modo Big Picture (`-applaunch`), sem usar streaming.
- Opções GameMode e MangoHud no menu Ajustes do Início; aplicadas diretamente aos jogos Linux nativos que declaram a categoria Game.

O pacote steam-installer não é incluído no perfil básico. Quando instalado pelo Modo Console, instala o cliente Steam por usuário; não inclui jogos nem contas.

## Instalar extras (opcional)

No desktop do Live/instalado existe Instalar extras de jogos. Também é possível executar:

    sudo /usr/local/bin/smart-tv-install-gaming

Esse instalador, quando confirmado pelo usuário, instala:
- steam-installer (cliente Steam por usuário; as regras udev de controles/Steam Input já vêm na ISO base);
- Wine 64/32 bits e Winetricks;
- DOSBox e ScummVM;
- Gamescope de Debian Trixie Backports;
- Heroic (Epic/GOG/Amazon), Bottles e ProtonUp-Qt pelo Flathub;
- RetroArch, Dolphin, PPSSPP, PCSX2 e RPCS3 pelo Flathub.

A instalação precisa de Internet e baixa runtimes/aplicativos. O script é opcional para que a ISO Live continue leve e não instale centenas de megabytes de jogos/emuladores sem a decisão do usuário.

## Escolha do perfil e latência

- **Modo TV + Moonlight/Steam Link**: jogo roda no PC host; a TV recebe vídeo codificado e envia entradas. É uma boa escolha para uma TV box/PC fraco como cliente, mas depende da rede local, do encoder do host e do decoder do cliente; não elimina a latência do streaming.
- **Modo Console + Steam/Proton**: jogo roda na própria máquina da TV. Não há captura/encode, rede, transporte e decode do vídeo do jogo; costuma ter menos latência de caminho, porém exige CPU, GPU, memória e armazenamento locais e pode aquecer/consumir mais energia.
- Nenhum dos modos garante que todos os títulos funcionem. Escolha o que combina com o hardware e o uso.

## Desempenho

- GameMode fica ativado por padrão no Modo Console para jogos Linux nativos reconhecidos como categoria Game; o usuário pode desligá-lo em Ajustes do Início. Jogos Steam/Proton podem usar `gamemoderun %command%` nas opções de inicialização do próprio jogo.
- MangoHud fica desativado por padrão no Modo Console e pode ser ativado no mesmo menu. A variável é aplicada a jogos nativos compatíveis com OpenGL/Vulkan. Para Steam/Proton, use `MANGOHUD=1 %command%` nas opções de inicialização do jogo.
- Steam/Proton, Heroic e Lutris gerenciam seus próprios jogos e podem exigir configuração de GameMode/MangoHud dentro do respectivo launcher. O Smart TV OS não injeta variáveis em processos intermediários de Steam/Proton para evitar uma otimização enganosa que termina antes do jogo.
- Gamescope é instalado como ferramenta opcional; não é forçado em todos os jogos porque resolução, compositor, driver e GPU variam por máquina.

## Limitações importantes

- Ter um launcher instalado não garante que todo jogo rode no Linux.
- Jogos com anti-cheat, DRM, launchers proprietários ou dependências específicas podem não funcionar com Wine/Proton.
- Para GPUs Intel/AMD, o caminho normal usa Mesa/Vulkan incluído na imagem. Quem usa driver proprietário NVIDIA pode precisar instalar o driver correspondente e as bibliotecas i386 `nvidia-driver-libs:i386` e `nvidia-vulkan-icd:i386`; isso depende do modelo e da versão do driver.
- RPCS3, PCSX2, Dolphin e outros emuladores dependem muito de CPU, GPU e configuração; nenhum desempenho é garantido.
- Emuladores não incluem ROMs, imagens de jogos, BIOS ou firmware. Use somente arquivos que você tem direito de usar.
- A instalação de steam-devices cria regras udev que ampliam o acesso de usuários locais a dispositivos de entrada; use em uma máquina doméstica confiável e leia /usr/share/doc/steam-devices/README.Debian.
- Controle Bluetooth depende do adaptador, firmware e emparelhamento do dispositivo.
- A compatibilidade real de controles, Vulkan, aceleração de vídeo, suspend/resume e desempenho ainda exige testes em hardware físico.

## Fontes e identificadores

- Steam no Debian: https://wiki.debian.org/Steam/
- Moonlight (cliente): https://flathub.org/apps/com.moonlight_stream.Moonlight
- Steam Link (cliente): https://flathub.org/apps/com.valvesoftware.SteamLink
- Sunshine (host para Moonlight): https://flathub.org/apps/dev.lizardbyte.app.Sunshine
- Heroic: https://flathub.org/apps/com.heroicgameslauncher.hgl
- Bottles: https://flathub.org/apps/com.usebottles.bottles
- ProtonUp-Qt: https://flathub.org/apps/net.davidotek.pupgui2
- RetroArch: https://flathub.org/apps/org.libretro.RetroArch
- Dolphin: https://flathub.org/apps/org.DolphinEmu.dolphin-emu
- PPSSPP: https://flathub.org/apps/org.ppsspp.PPSSPP
- PCSX2: https://flathub.org/apps/net.pcsx2.PCSX2
- RPCS3: https://flathub.org/apps/net.rpcs3.RPCS3

## Instalação local e dual boot

Os jogos são baixados e executados no próprio PC. Não há servidor remoto, codificação de vídeo ou rede entre o controle e o jogo nesse modo; só existe a latência normal do próprio computador/monitor/controle. Downloads precisam de Internet, e alguns títulos exigem conexão permanente mesmo depois de instalados. A Steam informa que jogos instalados podem funcionar offline, exceto os que exigem rede ou autenticação online.

A Steam do Debian instala o cliente e os jogos no diretório pessoal do usuário. Reserve espaço generoso na partição Linux (ext4) ou use um SSD/partição Linux dedicada para a biblioteca. Evite compartilhar a mesma biblioteca Steam numa partição NTFS do Windows: instalações e prefixos de compatibilidade Proton não são um bom alvo para uma biblioteca compartilhada entre os dois sistemas.

A interface Big Picture da Steam é a experiência de TV/controle disponível no cliente desktop. Ela não transforma esta distribuição no SteamOS oficial, não traz o selo Steam Deck Verified e não fornece automaticamente a suspensão/retomada e a gestão de energia específicas do Deck.
