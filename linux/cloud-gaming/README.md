# Jogos na nuvem no Modo TV

O Modo TV foi pensado para um único computador conectado à TV. Ele não exige outro PC de jogos ligado na rede: os provedores abaixo executam o jogo em servidores remotos e enviam vídeo/áudio para o Smart TV OS. O computador local faz principalmente decodificação de vídeo, áudio e leitura do controle.

## Atalhos incluídos na ISO

- **Xbox Cloud Gaming** — abre [xbox.com/play](https://www.xbox.com/pt-BR/play) no Chromium, em janela de aplicativo e tela cheia. O catálogo depende da região, da conta e do plano; a página oficial informa que alguns jogos gratuitos podem ser acessados com conta Microsoft, enquanto a maior parte do catálogo Game Pass exige assinatura compatível.
- **GeForce NOW** — abre [play.geforcenow.com](https://play.geforcenow.com/). No Brasil o serviço é atendido pelo parceiro ABYA. É o caminho mais próximo para jogar parte da biblioteca Steam na nuvem.
- **Boosteroid** — abre [cloud.boosteroid.com](https://cloud.boosteroid.com/). O provedor informa disponibilidade no Brasil e oferece também aplicativo Linux em pacote DEB para Debian 11 ou mais recente. A ISO não baixa nem instala esse cliente de terceiros por padrão; o usuário pode obtê-lo no site oficial quando preferir o cliente nativo.

Cada provedor recebe um perfil de Chromium separado em:

    ~/.local/share/smart-tv/cloud-profiles/

Assim, os logins do Xbox, GeForce NOW e Boosteroid não se misturam entre si nem com a sessão da interface Smart TV. O perfil preserva cookies e autenticação entre reinicializações.

## Steam Cloud, Steam Cloud Play e Steam Link não são a mesma coisa

- **Steam Cloud** sincroniza arquivos de salvamento/configuração entre dispositivos. Não executa nem transmite jogos.
- **Steam Cloud Play** é a integração de jogos Steam com serviços de nuvem, incluindo GeForce NOW. O publicador precisa habilitar cada jogo; por isso, não é possível transmitir automaticamente qualquer título da biblioteca Steam.
- **GeForce NOW** executa na nuvem os títulos compatíveis e conecta a conta Steam do usuário.
- **Steam Link / Steam Remote Play** transmite um jogo executado em outro computador que esteja rodando Steam. Não é a escolha principal para o Smart TV OS quando o próprio computador local está ocupado com a TV.

Os atalhos Moonlight e Steam Link continuam sendo opções secundárias: instale-os pelo Discover somente se houver outro PC na rede (por exemplo, com Sunshine ou Steam) servindo os jogos.

## Limitações e validação

- Os atalhos abrem os sites oficiais; não incluem assinatura, conta, licença ou compra de jogos.
- A latência final depende da rota até o datacenter, jitter, perda de pacotes, Wi-Fi e decodificador. Ethernet é preferível; em Wi-Fi use 5 GHz ou melhor. Streaming sempre tem alguma latência de rede.
- O Xbox indica, para seu Cloud Gaming no navegador, um navegador compatível como Edge/Chrome/Safari e conexão mínima de 10 Mbps, recomendando 20 Mbps em alguns dispositivos. O Chromium desta ISO deve ser validado com controle real, aceleração de vídeo e login no serviço.
- A aplicação nativa atual do GeForce NOW para Linux tem Ubuntu 24.04 como requisito oficial. Como esta ISO é Debian 13 Trixie, não instalamos o binário nativo da NVIDIA nem afirmamos suporte oficial a Debian; o atalho usa o portal web e precisa de teste físico.
- O cliente Linux do Boosteroid é fornecido pelo próprio provedor e está em beta segundo seu suporte. A ISO não instala pacotes externos nem mantém repositório de terceiros.
- O suporte ao controle depende do serviço, do jogo e do navegador/cliente. Testar Xbox, DualSense e controles genéricos por USB e Bluetooth continua necessário.
- A ISO base inclui VA-API, drivers Mesa para AMD/Intel antigos e atuais, e `vainfo` para diagnóstico. O driver aplicável depende da geração da GPU. O perfil TV também inclui Vulkan para o caminho de aceleração de vídeo suportado.
- Para o melhor resultado, o computador precisa suportar decodificação de vídeo por hardware (H.264 e, quando disponível, H.265/AV1). Sem isso, a CPU pode ficar bastante ocupada mesmo quando o jogo roda na nuvem. Use `vainfo` no desktop para conferir os perfis de decodificação disponíveis. Drivers proprietários NVIDIA podem exigir instalação adicional específica do modelo; a ISO não força um único driver NVIDIA em todas as máquinas.

## Outra máquina na rede (opcional)

Se o usuário tiver um PC gamer separado, poderá instalar:
- Moonlight na TV + Sunshine no computador host.
- Steam Link na TV + Steam executando o jogo no computador host.

Essas opções não são o fluxo padrão, pois exigem um segundo computador disponível para renderizar o jogo.
