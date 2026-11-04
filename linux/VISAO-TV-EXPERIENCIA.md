# Visão do produto — Smart TV OS como uma TV completa

## Objetivo

Evoluir a imagem Debian 13 para um sistema de entretenimento de sala, iniciado diretamente em uma interface de TV, com navegação por controle, efeitos visuais e sonoros próprios, aplicativos de streaming, recebimento de mídia e controle pelo celular.

A referência de experiência é a geração moderna do tvOS 26: conteúdo em primeiro plano, superfícies translúcidas, profundidade, foco evidente e animações contínuas. A implementação do Smart TV OS deve ter **identidade visual própria**. Não copiar logotipo, ícones, sons, imagens, tipografia proprietária ou telas da Apple; criar materiais, animações, sons e componentes originais inspirados nos princípios de clareza, profundidade e fluidez.

Esta é uma especificação de produto e uma direção de desenvolvimento. Os recursos descritos como planejados ou experimentais ainda não devem ser anunciados como disponíveis até que sejam implementados e testados.

## 1. Experiência de TV desejada

### Interface e identidade visual

- Inicialização direta em uma tela de TV em tela cheia, sem exigir que o usuário conheça o desktop Linux.
- Plano de fundo cinematográfico com imagens e vídeos em alta qualidade, parallax sutil e escurecimento adaptativo para manter os textos legíveis.
- Cartões grandes de aplicativos, pôsteres e conteúdos em destaque, com navegação horizontal por categorias.
- Camadas translúcidas e desfoque de fundo inspirados no conceito de vidro, com contraste e legibilidade garantidos.
- Realce de foco com escala, brilho, contorno e transição suaves ao navegar com controle, teclado ou controle remoto.
- Transições entre início, biblioteca, busca, aplicativos, configurações e telas de reprodução.
- Relógio, rede, volume, estado do controle e notificações em uma central de controle discreta.
- Tela de descanso com arte, relógio e retorno imediato ao pressionar um botão.
- Perfis locais e preferências de idioma, áudio, rede e acessibilidade em uma fase posterior.

### Sons e feedback

- Sons originais e curtos para mover o foco, selecionar, voltar, abrir um aplicativo, iniciar transmissão e receber uma conexão.
- Controle independente de volume dos efeitos, opção de silenciar e prévia dos sons nas configurações.
- Não tocar efeitos repetitivos durante reprodução de vídeo ou música.
- Opções para reduzir animações, desativar sons e preservar acessibilidade.

### Desempenho

- Interface responsiva em hardware modesto, com animações reduzidas automaticamente quando a GPU não suportar os efeitos mais elaborados.
- Decodificação de vídeo acelerada por hardware sempre que o driver permitir.
- Suspender animações e tarefas visuais pesadas quando um aplicativo estiver em primeiro plano.
- Não bloquear o controle remoto enquanto a biblioteca de mídia ou os dispositivos de transmissão são descobertos.

## 2. Transmissão e controle pelo celular: protocolos diferentes

O menu da TV deve reunir os recursos em uma seção única, por exemplo **Conectar celular**, mas cada protocolo deve ser identificado corretamente. O sistema não pode apresentar AirPlay, Google Cast, Miracast, FCast e DLNA como se fossem a mesma tecnologia.

| Tecnologia | Papel no Smart TV OS | Estado e observações |
|---|---|---|
| AirPlay / AirPlay Mirror | Receber espelhamento de iPhone, iPad e Mac, com áudio quando suportado | Início possível com UxPlay do Debian. Não equivale a um receptor completo de Apple TV/AirPlay 2; testar modelos e versões iOS. Conteúdo protegido pode ser bloqueado. |
| Google Cast / Chromecast | Permitir que o próprio app de streaming no celular descubra a TV, inicie a sessão e controle a reprodução sem espelhamento | Criar um receiver real e compatível. A descoberta na rede não garante que cada serviço aceite o receiver; compatibilidade por app é obrigatória. |
| Miracast / Wi-Fi Display | Receber a tela inteira de celulares Android que ofereçam essa opção (por exemplo, Smart View em alguns aparelhos) | Pesquisa experimental. O suporte no Linux depende do adaptador Wi‑Fi, Wi‑Fi Direct/P2P, driver e gerenciamento de rede. Não habilitar como recurso estável sem testes. |
| FCast | Receber streams, arquivos e mídia de aplicativos que implementem o protocolo aberto FCast | Caminho aberto complementar. Não é Google Cast nem garante espelhamento nativo de qualquer celular; confirmar cada aplicativo remetente. |
| DLNA / UPnP | Descobrir e receber mídia local em aparelhos compatíveis | Alternativa para arquivos e players compatíveis; não substitui espelhamento de tela nem apps de streaming protegidos. |

### Cast nativo dentro dos aplicativos — requisito "TV Sala"

O comportamento desejado para os serviços é o Cast iniciado dentro do próprio aplicativo móvel, como em uma Smart TV: o usuário abre Netflix/Prime Video/Disney+/outro app, toca em Transmitir, seleciona **TV Sala**, e a reprodução acontece no receiver/app da TV. O celular permanece como controle da sessão. Não é espelhamento da tela.

O documento [Cast nativo dos aplicativos — destino TV Sala](CAST-APPS-E-RECEPTORES.md) descreve o fluxo, a arquitetura e a matriz de validação por serviço.

**Atenção especial à Netflix:** sua documentação atual restringe o Cast do app móvel a Chromecast de 3ª geração ou anterior sem controle remoto, Nest Hub e alguns modelos Vizio/Compal. Um PC Linux com receiver Cast genérico não está nessa lista. Portanto, não prometer que Netflix mostrará TV Sala até haver aceitação oficial e teste real. Para esse serviço, o plano alternativo é executar Netflix diretamente na TV e oferecer um controle companion próprio do Smart TV OS no celular. Isso não é o mesmo que selecionar a TV dentro do app Netflix.

### AirPlay: primeira integração

O Debian 13 fornece o pacote uxplay, que permite receber AirPlay Mirror e áudio AirPlay em um computador Linux. A imagem experimental deve disponibilizar um atalho **Receber AirPlay**, que inicia o serviço sob demanda e solicita PIN de conexão.

Limitações que precisam permanecer explícitas:

- UxPlay não implementa o protocolo de vídeo AirPlay 2 completo.
- Espelhar a interface do telefone não significa que aplicativos protegidos aceitarão a imagem.
- O serviço deve permanecer desligado até que o usuário o inicie.
- A conexão deve ser restrita à rede local, com PIN e indicação visual da sessão ativa.
- Um botão **Desconectar** deve encerrar a sessão e liberar a tela.

### Android: abordagem em camadas

A meta é aceitar conteúdo Android de mais de uma maneira:

1. **Google Cast de aplicativos:** integração de receiver para apps que suportam Google Cast, validada aplicativo por aplicativo.
2. **Miracast / Smart View:** espelhamento de tela inteira quando o celular, chipset Wi‑Fi e driver Linux forem compatíveis.
3. **FCast:** mídia de aplicativos remetentes compatíveis com o protocolo aberto.
4. **DLNA:** envio de fotos, música e vídeos locais, quando o aplicativo do celular oferecer essa opção.

Não confundir o GNOME Network Displays com um receptor para o celular: sua função principal é transmitir a tela do computador para outra tela. MiracleCast tem código para o lado receptor Miracast, mas requer controle de Wi‑Fi Direct e pode interferir no NetworkManager; deve permanecer em avaliação isolada até existir um desenho de rede seguro.

### Controle pelo celular

Desenvolver um controle remoto web/PWA, acessível pela rede local sem instalar aplicativo obrigatório:

- O usuário abre **Conectar celular** na TV.
- A TV mostra QR code e código curto temporário.
- O telefone entra em uma página local e confirma o pareamento.
- A interface do telefone oferece direcional, OK, voltar, início, reprodução/pausa, volume, teclado para busca e controle da sessão de transmissão.
- O celular pode controlar a TV sem espelhar a própria tela.
- Pareamentos podem ser revogados na TV.

Requisitos obrigatórios de segurança:

- Pareamento iniciado fisicamente na TV e PIN temporário, com expiração.
- Nenhum controle remoto aberto por padrão na rede.
- Sessões autenticadas, limite de tentativas, revogação e indicação de aparelhos conectados.
- Não expor o backend interno do launcher diretamente à rede.
- Não receber comandos de teclado arbitrários sem validação.
- Não enviar senha de streaming nem credenciais dos serviços ao telefone.
- Tráfego limitado à rede privada/local; documentar o comportamento em redes Wi‑Fi isoladas ou guest network.

## 3. Streaming: prioridade para reprodução no próprio sistema

A biblioteca deve reunir atalhos ou aplicativos suportados para os serviços que o usuário utiliza, por exemplo:

- Netflix
- Prime Video
- Disney+
- Max
- Apple TV
- YouTube
- Spotify e outros serviços de música

A disponibilidade varia por país, serviço, versão e DRM. O projeto deve usar, nesta ordem:

1. Aplicativo Linux oficial, quando o fornecedor disponibilizar.
2. Aplicativo web/PWA ou navegador compatível com o DRM e codecs requeridos.
3. Google Cast oficial/compatível para o serviço, quando houver receiver suportado.
4. Reprodução local ou DLNA para arquivos sem proteção, quando adequado.

**Não prometer que todo aplicativo de streaming pode ser espelhado pelo celular.** Alguns serviços desativam AirPlay, bloqueiam espelhamento, exigem um receiver certificado ou entregam o vídeo diretamente ao aparelho receptor com DRM. A Netflix, por exemplo, informa que não oferece suporte a AirPlay e que o espelhamento sem fio pode não funcionar em determinados dispositivos. Nesses serviços, a opção correta é abrir o serviço no próprio Smart TV OS ou usar um destino Cast explicitamente compatível.

Cada serviço deve ter uma matriz de validação separada: abrir/login, vídeo, áudio, resolução, legendas, controle pelo celular, retomada de sessão, DRM e comportamento após atualização.

## 4. Arquitetura recomendada

Separar a experiência em serviços para que uma falha de transmissão não derrube o launcher:

- **TV Shell:** interface principal, navegação por foco, efeitos, sons, configurações e central de controle.
- **App Catalog:** descoberta de aplicativos Linux, Flatpak e atalhos web.
- **Media Center:** fila de reprodução, player local, biblioteca e metadados.
- **Cast Manager:** estado, descoberta, PIN, sessões ativas e encerramento de AirPlay, Google Cast, Miracast, FCast e DLNA.
- **Mobile Remote:** web/PWA isolada, pareamento e comandos autorizados.
- **System Services:** NetworkManager, Avahi/mDNS, Bluetooth, áudio, gamepads e aceleração gráfica.

Todos os receptores devem ter estados claros: desligado, procurando, aguardando conexão, conectado, reproduzindo, erro e desconectado. A tela deve informar o protocolo realmente usado.

## 5. Plano de implementação e critérios de aceite

### Fase A — base visual e AirPlay básico

- [ ] Criar identidade visual própria inspirada em superfícies translúcidas, sem copiar assets Apple.
- [ ] Implementar feedback sonoro original e controles para reduzir animação/som.
- [ ] Integrar UxPlay ao menu e à imagem Debian, iniciando sob demanda com PIN.
- [ ] Exibir estado de AirPlay na TV e permitir encerrar sessão.
- [ ] Testar iPhone/iPad e macOS em versões distintas, com áudio, vídeo, latência e reconexão.

**Aceite:** o dispositivo é descoberto na mesma rede; o usuário insere o PIN; espelhamento compatível é exibido com áudio quando suportado; a sessão pode ser encerrada; nenhum receiver fica aberto sem consentimento.

### Fase B — catálogo de mídia e controle pelo celular

- [ ] Integrar FCast Receiver como aplicativo opcional pela loja Flatpak, após validação.
- [ ] Implementar pareamento QR/PIN do controle remoto.
- [ ] Adicionar controle de navegação e reprodução do celular.
- [ ] Implementar descoberta mDNS sem expor o backend interno.
- [ ] Testar em Android e iPhone na mesma rede, inclusive com isolamento de clientes.

**Aceite:** o telefone emparelha por código temporário, controla navegação/volume/reprodução autorizados e pode ser removido pela TV.

### Fase C — Cast nativo dentro dos apps (TV Sala), Android e Google Cast

- [ ] Avaliar e testar um receiver Miracast sink real em hardware suportado.
- [ ] Validar compatibilidade Wi‑Fi Direct/P2P sem derrubar a conexão normal da TV.
- [x] Integrar VibeCast v0.2.0 como receptor Cast V2, com descoberta mDNS e player local TV Sala.
- [ ] Configurar material válido de autenticação Cast e validar descoberta/conexão com apps sender reais.
- [ ] Validar receiver IDs, DRM e compatibilidade por serviço.
- [ ] Implementar nome amigável configurável, padrão TV Sala, e fluxo Sender → Receiver sem espelhamento.
- [ ] Validar cada aplicativo móvel separadamente; não inferir suporte Netflix a partir de testes com outros apps.
- [ ] Para serviços que não aceitam receiver genérico, abrir o cliente do serviço na TV e disponibilizar controle companion autorizado.
- [ ] Testar os aplicativos Android mais importantes um por um.
- [ ] Não chamar FCast ou DLNA de Google Cast.

**Aceite:** registrar uma lista de combinações testadas de modelo do telefone, versão Android, adaptador Wi‑Fi, protocolo e aplicativo. Só declarar suporte para as combinações aprovadas.

### Fase D — streaming

- [ ] Catálogo com serviços oficiais/web quando disponíveis.
- [ ] Testes separados de DRM, resolução, áudio e legendas.
- [ ] Implementar Cast por serviço apenas quando o emissor e receiver forem compatíveis.
- [ ] Manter alternativa de reprodução diretamente no sistema.
- [ ] Documentar serviços incompatíveis com espelhamento.

**Aceite:** nenhuma tela de serviço é anunciada como compatível antes do teste real; limitações de DRM ficam visíveis.

### Fase E — acabamento e estabilidade

- [ ] Controle de gamepad e navegação por teclado em todas as telas.
- [ ] Perfis, screensaver, retomada e atualizações com recuperação.
- [ ] Testes de boot UEFI, drivers, áudio, HDMI, Wi‑Fi e Bluetooth.
- [ ] Testes contínuos de memória, fluidez e temperaturas.
- [ ] Instalação dual boot validada sem apagar partições Windows ou EFI.

## 6. Estado real desta ISO

No momento desta especificação, a edição Linux é experimental:

- Debian 13 Trixie amd64 e KDE Plasma.
- Launcher Smart TV e backend Linux.
- KDE Discover e suporte Flatpak na composição em construção.
- Kodi, VLC, Lutris, GameMode e MangoHud na lista de pacotes da imagem.
- UxPlay em integração inicial para AirPlay Mirror básico (não AirPlay 2 completo).
- Cast nativo dentro dos aplicativos (destino TV Sala), receiver Google Cast completo, Miracast sink integrado, controle remoto móvel próprio e experiência visual final ainda não concluídos.
- A Netflix atualmente restringe o Cast móvel a uma lista limitada de dispositivos; um receiver Linux genérico não tem compatibilidade confirmada.
- Steam não vem pré-instalada.
- O Calamares usa configuração genérica; o fluxo de dual boot ainda não está validado em hardware real.

## 7. Referências técnicas

- [Apple — tvOS 26 e Liquid Glass](https://www.apple.com/br/newsroom/2025/06/apple-tv-brings-a-beautiful-redesign-and-enhanced-home-entertainment-experience/)
- [Debian — pacote UxPlay](https://packages.debian.org/trixie/uxplay)
- [UxPlay — projeto upstream](https://github.com/FDH2/UxPlay)
- [FCast — protocolo aberto](https://docs.fcast.org/)
- [FCast — receiver](https://docs.fcast.org/receiver/)
- [Google Cast — arquitetura sender/receiver](https://developers.google.com/cast/docs/overview)
- [Documento do projeto: Cast nativo e TV Sala](CAST-APPS-E-RECEPTORES.md)
- [Google Cast — registro de receiver](https://developers.google.com/cast/docs/registration)
- [MiracleCast — implementação Miracast sink](https://github.com/albfan/miraclecast)
- [Netflix — transmissão e espelhamento](https://help.netflix.com/pt/node/49)

---

A visão é ambiciosa, mas o critério do projeto é simples: **uma função só será apresentada como compatível quando estiver implementada e testada no hardware e nos aplicativos indicados**.
