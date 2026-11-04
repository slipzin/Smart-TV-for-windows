# Jogos no Smart TV OS

## O que a ISO prepara

- Steam Installer Debian (o cliente final é baixado e configurado por usuário na primeira abertura).
- Lutris, GameMode, MangoHud, Mesa Vulkan, Vulkan Tools.
- Suporte a controle por navegador/Gamepad API no launcher Smart TV.
- Bluetooth (BlueZ/Blueman) para controles compatíveis.
- Descoberta de launchers e aplicativos de jogos por arquivos .desktop e Flatpak.
- Biblioteca Jogos separada de Todos os Apps, com detecção de entradas da categoria freedesktop Game.
- Detecção de jogos instalados nas bibliotecas Steam, com abertura por URI steam://rungameid/...
- Opções GameMode e MangoHud no menu Ajustes do Início; aplicadas diretamente aos jogos Linux nativos que declaram a categoria Game.

O pacote steam-installer é o instalador do cliente, não uma cópia pré-instalada de Steam nem inclui jogos. Ao abrir Steam pela primeira vez, o instalador baixa o cliente para a conta local.

## Instalar extras (opcional)

No desktop do Live/instalado existe Instalar extras de jogos. Também é possível executar:

    sudo /usr/local/bin/smart-tv-install-gaming

Esse instalador, quando confirmado pelo usuário, instala:
- steam-devices (regras udev para gamepads, Steam Input e dispositivos compatíveis);
- Wine 64/32 bits e Winetricks;
- DOSBox e ScummVM;
- Gamescope de Debian Trixie Backports;
- Heroic (Epic/GOG/Amazon), Bottles e ProtonUp-Qt pelo Flathub;
- RetroArch, Dolphin, PPSSPP, PCSX2 e RPCS3 pelo Flathub.

A instalação Flatpak precisa de Internet e baixa os runtimes e aplicativos. O script é opcional para que a ISO Live não baixe centenas de megabytes de emuladores sem a decisão do usuário.

## Desempenho

- GameMode fica ativado por padrão para jogos Linux nativos reconhecidos como categoria Game; o usuário pode desligá-lo em Ajustes do Início.
- MangoHud fica desativado por padrão e pode ser ativado no mesmo menu. A variável é aplicada a jogos nativos compatíveis com OpenGL/Vulkan.
- Steam/Proton, Heroic e Lutris gerenciam seus próprios jogos e podem exigir configuração de GameMode/MangoHud dentro do respectivo launcher. O Smart TV OS não injeta variáveis em processos intermediários de Steam/Proton para evitar uma otimização enganosa que termina antes do jogo.
- Gamescope é instalado como ferramenta opcional; não é forçado em todos os jogos porque resolução, compositor, driver e GPU variam por máquina.

## Limitações importantes

- Ter um launcher instalado não garante que todo jogo rode no Linux.
- Jogos com anti-cheat, DRM, launchers proprietários ou dependências específicas podem não funcionar com Wine/Proton.
- RPCS3, PCSX2, Dolphin e outros emuladores dependem muito de CPU, GPU e configuração; nenhum desempenho é garantido.
- Emuladores não incluem ROMs, imagens de jogos, BIOS ou firmware. Use somente arquivos que você tem direito de usar.
- A instalação de steam-devices cria regras udev que ampliam o acesso de usuários locais a dispositivos de entrada; use em uma máquina doméstica confiável e leia /usr/share/doc/steam-devices/README.Debian.
- Controle Bluetooth depende do adaptador, firmware e emparelhamento do dispositivo.
- A compatibilidade real de controles, Vulkan, aceleração de vídeo, suspend/resume e desempenho ainda exige testes em hardware físico.

## Fontes e identificadores

- Steam no Debian: https://wiki.debian.org/Steam/
- Heroic: https://flathub.org/apps/com.heroicgameslauncher.hgl
- Bottles: https://flathub.org/apps/com.usebottles.bottles
- ProtonUp-Qt: https://flathub.org/apps/net.davidotek.pupgui2
- RetroArch: https://flathub.org/apps/org.libretro.RetroArch
- Dolphin: https://flathub.org/apps/org.DolphinEmu.dolphin-emu
- PPSSPP: https://flathub.org/apps/org.ppsspp.PPSSPP
- PCSX2: https://flathub.org/apps/net.pcsx2.PCSX2
- RPCS3: https://flathub.org/apps/net.rpcs3.RPCS3
