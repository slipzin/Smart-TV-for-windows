# Receptor Google Cast — TV Sala

Esta integração usa o projeto open source [VibeCast](https://github.com/emilsvennesson/vibecast), fixado na versão v0.2.0 e compilado durante a geração da ISO.

## O que a integração prepara

- Protocolo Google Cast V2 e descoberta mDNS pelo VibeCast.
- Nome de player/receptor configurado como **TV Sala**.
- Player web local (Shaka Player) para receber e reproduzir as sessões que forem compatíveis com o navegador.
- Script de inicialização que verifica a presença e a estrutura do arquivo privado de autenticação.
- Serviço desligado por padrão: o usuário escolhe quando abrir o atalho **Iniciar Google Cast — TV Sala**.

## Estado e requisito de autenticação

O VibeCast exige material de autenticação de dispositivo Google Cast válido, incluindo certificado/cadeia e resposta de autenticação assinada. Esse material não está incluído no código-fonte nem nos releases upstream. Sem credenciais válidas, aplicativos remetentes podem rejeitar o dispositivo.

A ISO **não inclui**, inventa, copia nem publica esse material. O usuário deve possuir um arquivo de autenticação que esteja autorizado a usar e guardá-lo somente no computador, fora do repositório.

Caminho esperado:

    ~/.config/smart-tv/cast/certs.json

Restringir o arquivo à conta local (permissão 600). Nunca faça commit desse arquivo nem envie seu conteúdo em issues, chats ou capturas de tela.

O script faz validação estrutural do JSON antes de abrir o servidor. A validação estrutural não confirma se os certificados são válidos, se não expiraram ou se serão aceitos pelos servidores Google.

## Inicializar

1. Disponha o arquivo autorizado em `~/.config/smart-tv/cast/certs.json`.
2. Na área de trabalho KDE, abra **Iniciar Google Cast — TV Sala**.
3. O receptor e o player local serão iniciados. O player se registra no VibeCast com o nome TV Sala.
4. Aplicativos remetentes compatíveis poderão descobrir o dispositivo na mesma rede, caso a autenticação Cast seja válida.
5. Feche a janela do player para encerrar o receptor.

Logs locais:

- `~/.config/smart-tv/cast/vibecast.log`
- `~/.config/smart-tv/cast/player-http.log`
- `~/.config/smart-tv/cast/player-browser.log`

## Compatibilidade

O VibeCast upstream lista YouTube, Prime Video, SVT Play, TV4 Play, Viaplay e DAZN. A disponibilidade real depende de autenticação, player, DRM, navegador, codecs e política de cada serviço. O player web é indicado pelo upstream principalmente para desenvolvimento/teste. A integração Kodi requer Kodi 21.3+, enquanto Debian 13 Trixie fornece Kodi 21.2; por isso, esta ISO não declara suporte ao player Kodi do VibeCast.

Netflix e Disney+ não estão listados como providers suportados pelo VibeCast v0.2.0. Não anunciar compatibilidade com esses apps até existir implementação e teste legítimos.

## Origem e licença

VibeCast v0.2.0, licença MIT. A ISO compila o código upstream e aplica duas alterações locais:
- nome anunciado do player: `TV Sala`;
- remove o sufixo de identificação técnica `[vibecast]` do nome público.

Código upstream: https://github.com/emilsvennesson/vibecast/tree/v0.2.0

A licença MIT upstream é copiada junto aos arquivos instalados em /usr/share/doc/smarttv-vibecast/.
