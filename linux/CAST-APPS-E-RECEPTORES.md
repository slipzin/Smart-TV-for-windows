# Cast nativo dos aplicativos — destino "TV Sala"

## O que queremos entregar

O usuário abre o aplicativo de streaming no celular, toca no botão **Transmitir/Cast** que já existe dentro desse aplicativo e encontra um dispositivo da casa chamado **TV Sala**. Ao selecioná-lo, o conteúdo passa a tocar na Smart TV OS e o celular continua como controle de reprodução.

**Isto não é espelhamento de tela.** O telefone não envia a imagem inteira da tela para a TV. Ele inicia uma sessão com um receptor compatível. Em uma sessão Cast convencional, o receptor é responsável por carregar/reproduzir o conteúdo e o telefone funciona como Sender/controle: play, pause, busca, seleção de conteúdo e outros comandos permitidos pelo serviço.

O nome amigável padrão do dispositivo será **TV Sala**, mas deve ser editável na configuração da TV (por exemplo, "TV Quarto", "TV Escritório"). A descoberta acontece na rede local, com o celular e a TV conectados a uma rede que permita descoberta entre dispositivos. Redes guest, isolamento de clientes Wi-Fi, VLANs e bloqueios de multicast podem impedir que o alvo apareça.

## Fluxo desejado

1. O computador está ligado e o serviço receiver compatível está ativo.
2. O celular e o Smart TV OS estão na mesma rede local.
3. O usuário abre o próprio aplicativo de streaming no celular.
4. O app mostra seu botão de transmissão e descobre os destinos que ele considera compatíveis.
5. O usuário seleciona **TV Sala**.
6. O sender conecta ao receiver correto e envia a solicitação da sessão (não a tela do telefone).
7. A TV abre o receiver/app de serviço apropriado e reproduz o conteúdo diretamente da internet, sujeito à autenticação, DRM e permissão daquele serviço.
8. O telefone oferece os controles de sessão que o serviço disponibiliza.
9. Quando a sessão termina, o receiver encerra a reprodução e devolve a TV à interface Smart TV OS.

Esse fluxo depende de integração entre o aplicativo Sender e o Receiver. A descoberta do dispositivo na rede, sozinha, não basta. O app sender precisa reconhecer e aceitar aquele receiver e sua implementação.

## A distinção mais importante: Google Cast genérico não significa Netflix compatível

O Google Cast define a arquitetura Sender/Receiver. O Google documenta que o Sender controla a sessão e que os receivers possuem tipos e identificadores de aplicação próprios; o aplicativo sender e o receiver precisam ser compatíveis entre si. Um receiver genérico não passa automaticamente a ser aceito por qualquer aplicativo de streaming.

### Limite específico da Netflix

A documentação oficial da Netflix atualmente lista como aparelhos que aceitam transmissão iniciada pelo aplicativo móvel:

- Chromecast de 3ª geração ou anterior, sem controle remoto físico.
- Google Nest Hub Smart Display.
- Alguns modelos de TV Vizio com Cast.
- Alguns modelos de TV Compal com Cast.

A Netflix também informa que não oferece AirPlay. A lista oficial não inclui um PC Linux com receiver Cast genérico. Portanto, **não podemos garantir que "TV Sala" aparecerá no botão Cast do app Netflix**, mesmo se o Smart TV OS anunciar um receiver Google Cast básico e mesmo que os dois aparelhos estejam no mesmo Wi-Fi.

Essa restrição é definida pelo próprio serviço e pode mudar. Não é algo que se resolva simulando o nome de um Chromecast ou copiando seu protocolo. O projeto não deve se passar por um dispositivo certificado nem contornar restrições do fornecedor.

Para que Netflix aceite um novo tipo de aparelho, será necessário que o serviço reconheça oficialmente a plataforma/receiver e permita essa modalidade de transmissão. Até que haja suporte verificável, a experiência planejada para Netflix será:
- abrir a Netflix diretamente na TV por um cliente/web player que seja realmente compatível com o serviço, se disponível;
- controlar a navegação e a reprodução por controle remoto físico ou pelo **controle companion do Smart TV OS** no celular;
- não mostrar uma promessa falsa de que o botão Cast dentro do app Netflix encontrará "TV Sala".

A segunda opção de controle pelo celular é um recurso próprio do Smart TV OS: pode comandar a Netflix que já está rodando na TV, mas não transforma o app Netflix do celular em um sender autorizado pela Netflix.

## Matriz de compatibilidade por serviço

Cada serviço precisa ter uma validação separada. Não basta testar YouTube ou um app de demonstração do Google Cast e concluir que Netflix, Prime Video, Disney+ ou Max também funcionarão.

| Serviço / origem | Como deverá funcionar | Critério para declarar compatível |
|---|---|---|
| Netflix no celular | Selecionar "TV Sala" dentro do app Netflix somente se a Netflix aceitar oficialmente este tipo de receiver | A documentação atual limita a lista a certos dispositivos; Linux receiver genérico não está confirmado |
| Prime Video | Cast nativo se o app móvel e o receiver forem oficialmente compatíveis; caso contrário abrir o serviço na TV e usar controle companion | Testar Android e iOS, início de sessão, DRM, qualidade, legenda e controles |
| Disney+ | Cast nativo se o app e receiver aceitarem a combinação; alternativa é abrir o serviço na TV | Testar por plataforma/conta, DRM e sessão |
| Max | Cast nativo se o app e receiver aceitarem a combinação; alternativa é abrir o serviço na TV | Testar por plataforma/conta, DRM e sessão |
| YouTube | Integrar receiver compatível com o sender oficial e testar descoberta e fila | Testar Android/iOS, pareamento, anúncios, fila e controles |
| Spotify / música | Receiver compatível com o protocolo oferecido pelo app; alternativa local/web quando disponível | Testar seleção de destino, áudio em segundo plano e controle |
| FCast | Receber mídia de apps que implementam FCast | Identificar claramente como FCast, sem apresentá-lo como Google Cast |
| AirPlay | Receber AirPlay Mirror/audio compatível com UxPlay | Não confundir com Netflix Cast; a Netflix não oferece AirPlay |
| Miracast / Smart View | Espelhamento integral quando o hardware e o driver suportarem | Recurso separado; não é Cast nativo de um serviço e pode sofrer bloqueio DRM |

Os serviços podem alterar suas políticas, receptores suportados, apps e planos. A matriz deve apontar para a documentação atual de cada fornecedor e ser atualizada antes de cada release.

## Implementação selecionada para Linux: VibeCast

O branch experimental do Smart TV OS agora compila o [VibeCast v0.2.0](https://github.com/emilsvennesson/vibecast/tree/v0.2.0), um projeto comunitário de código aberto que implementa Cast V2, autenticação de dispositivo e descoberta mDNS. O player local é ajustado para anunciar o nome **TV Sala**.

Isso é uma implementação de compatibilidade de protocolo de terceiros, **não um Chromecast físico, Android TV nem um produto certificado/aprovado pelo Google**. A implementação ainda exige material de autenticação de dispositivo válido de um Cast real; não há credenciais incluídas na ISO ou no repositório. Sem esse material, apps remetentes rejeitam o receiver.

O VibeCast v0.2.0 lista providers para YouTube, Prime Video, SVT Play, TV4 Play, Viaplay e DAZN. O README upstream descreve o player Browser como ferramenta de desenvolvimento/teste e exige Kodi 21.3+ para o player Kodi; Debian 13 Trixie fornece Kodi 21.2, então esta imagem usa o player web local como primeiro caminho de teste. DRM, codecs e reprodução de cada serviço ainda devem ser validados no hardware.

Não há suporte Netflix listado nessa versão do VibeCast. A restrição de compatibilidade da Netflix permanece independente do Cast V2 genérico.

Consulte [linux/cast/README.md](cast/README.md) para o estado da integração e as exigências de autenticação. Nunca coloque o arquivo privado de certificados no repositório.

## Arquitetura do Smart TV OS

Desenvolver um **Cast Manager** separado do launcher:

- **Friendly name:** nome anunciado e configurável, padrão "TV Sala".
- **Discovery:** anunciar somente serviços e protocolos realmente implementados; descoberta local sem atravessar redes.
- **Receiver registry:** identificar que receiver e app ID estão ativos; não imitar IDs de produtos de terceiros.
- **Service adapter:** integração independente para cada plataforma e protocolo.
- **Playback coordinator:** estado da sessão, conteúdo, volume, posição, legendas, erros e retorno ao launcher.
- **Native app launcher:** abrir o app local do serviço quando existir integração autorizada, ou o cliente web compatível.
- **Companion remote:** oferecer QR code/PIN para controle próprio do Smart TV OS quando o app do serviço não aceitar Cast.
- **Privacy/security:** PIN para pareamento do controle companion, autorização explícita, revogação e sessões limitadas à rede local.

O receiver não deve pedir nem armazenar senha do serviço no celular. Quando o fluxo exigir autenticação, ela ocorre no app ou web player da TV conforme a política do serviço.

## Critérios de aceite antes de anunciar a função

Para cada serviço, registrar:

- nome e versão do app Sender;
- Android/iOS e versão do sistema;
- plano/país quando isso alterar a disponibilidade;
- modelo do computador, GPU e driver;
- tipo de conexão Wi-Fi/Ethernet e roteador;
- protocolo e implementação do Receiver;
- se "TV Sala" apareceu no botão do app;
- se iniciou a sessão sem espelhamento;
- se o vídeo foi buscado e decodificado na TV;
- DRM, resolução, áudio, legendas e sincronização;
- controles testados no celular (play, pause, seek, legendas, desconectar);
- reconexão, standby e encerramento.

**Regra do projeto:** só exibir um serviço como "Transmitir para TV Sala" quando o app Sender real desse serviço tiver sido testado com o receiver publicado. Uma implementação aberta de Cast ou uma descoberta mDNS bem-sucedida, sozinhas, não são prova de compatibilidade com Netflix.

## Referências oficiais

- [Netflix — como transmitir ou espelhar do celular](https://help.netflix.com/pt/node/49)
- [Netflix — aparelhos compatíveis com transmissão](https://help.netflix.com/pt/node/100131)
- [Netflix — "Nenhum aparelho encontrado"](https://help.netflix.com/pt/node/133390)
- [Google Cast — visão geral de Sender e Receiver](https://developers.google.com/cast/docs/overview)
- [Google Cast — descoberta e solução de problemas](https://developers.google.com/cast/docs/discovery)
