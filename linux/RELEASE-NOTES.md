# Smart TV OS — versão experimental

Esta é uma versão experimental do Smart TV OS baseada no Debian 13 (Trixie), arquitetura amd64.

## O que está incluído

- KDE Plasma e interface Smart TV em tela cheia.
- KDE Discover, repositórios Debian e integração com Flathub.
- Chromium, Kodi e VLC.
- Modo TV leve como perfil padrão.
- Modo Console opcional, instalado separadamente.
- Recursos iniciais de recepção AirPlay/Cast conforme as limitações documentadas no guia.

## Avisos importantes

- A imagem foi compilada e validada pelo workflow automatizado; isso não substitui testes em hardware físico.
- O modo recomendado é iniciar pelo pendrive em modo Live.
- A instalação permanente e o dual boot com Windows ainda não foram validados em máquinas reais. Não instale no disco principal com Windows e dados importantes.
- Compatibilidade de Wi-Fi, Bluetooth, áudio, GPU, DRM, serviços de streaming e jogos varia por equipamento e provedor.
- UxPlay oferece espelhamento AirPlay básico, não AirPlay 2 completo. Google Cast/FCast e Miracast têm limitações descritas na documentação.

## Arquivos

- `SmartTV-OS-live-trixie-amd64.iso`: imagem inicializável.
- `SmartTV-OS-live-trixie-amd64.iso.sha256`: checksum SHA-256 da ISO.

Confira o checksum antes de gravar o pendrive e siga o [guia de instalação](linux/GUIA-INSTALACAO.md).
