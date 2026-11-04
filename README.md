# Smart TV — transforme seu PC em uma experiência de TV

**Leve a experiência da sala de estar para o computador.** O Smart TV é um projeto que transforma PCs em centrais de entretenimento, com uma interface em tela cheia, navegação pensada para a televisão e suporte a controle de videogame, teclado e mouse.

A proposta reúne filmes, séries, música, aplicativos e jogos em uma experiência simples de usar no sofá — aproveitando os serviços e programas que você já utiliza. O projeto possui duas edições complementares: uma versão portátil para Windows e uma edição de sistema operacional Linux em desenvolvimento.

## Duas maneiras de transformar seu PC

### Smart TV for Windows

Uma central de entretenimento que funciona sobre o Windows, sem substituir o sistema e sem exigir uma instalação tradicional. Basta extrair os arquivos e iniciar o modo TV.

- **Seus aplicativos em um só lugar:** acesse aplicativos instalados no Windows, como Netflix, Prime Video, Disney+, Apple TV, Spotify, Xbox, Battle.net e outros.
- **Feito para o sofá:** navegue pela interface usando controle de Xbox, PlayStation ou outros controles compatíveis, além de teclado e mouse.
- **Jogos sem complicação:** abra a Steam diretamente no modo Big Picture e acesse sua biblioteca.
- **Sua TV, do seu jeito:** personalize temas, planos de fundo, animações, idioma, cidade do clima e comportamento da inicialização.
- **Prático e portátil:** execute pelo próprio computador ou por um pendrive, sem alterar a instalação do Windows.

### Smart TV OS — edição Linux experimental

A evolução do projeto para um sistema independente, baseado em Debian 13, pensado para transformar um PC em uma plataforma dedicada ao entretenimento da sala.

- **Interface de TV em um sistema próprio:** ambiente Linux com KDE Plasma, inicialização Live por pendrive e loja KDE Discover.
- **Do streaming aos jogos:** perfil Modo TV para a experiência de entretenimento e perfil Modo Console para jogos locais compatíveis.
- **Ecossistema aberto:** suporte a aplicativos Linux e Flatpak, com integração gamer planejada em torno de Steam, Proton, Heroic e emuladores.
- **Recursos de transmissão em desenvolvimento:** pesquisa e implementação de recursos como AirPlay, Google Cast, Miracast e controle pelo celular, respeitando as limitações reais de cada tecnologia.

> **Estado do projeto:** a edição Windows e a edição Linux têm escopos diferentes. O Smart TV OS ainda é experimental; compatibilidade de hardware, instalação permanente em dual boot e alguns recursos de transmissão precisam de validação. Consulte o guia Linux antes de instalar e prefira testar a ISO em modo Live.

## O que você encontra na experiência Windows

- **Tela inicial completa:** prateleira de aplicativos, relógio, clima, cotações e destaques de filmes e séries. Os dados de filmes e séries usam uma chave gratuita do TMDB, configurada uma única vez nos ajustes.
- **Navegação por controle:** compatibilidade com controles Xbox, PlayStation e outros. Em aplicativos, o controle Xbox também pode oferecer ponteiro pelo analógico direito; o botão View retorna à tela inicial.
- **Acesso aos jogos:** atalho para abrir a Steam em Big Picture. O Call of Duty instalado pela Steam é reconhecido automaticamente.
- **Personalização visual:** fundos animados e estáticos, imagens, GIFs e vídeos próprios, alternância automática, velocidade das animações, desfoque, escurecimento e temas claro ou escuro.
- **Configurações práticas:** idioma, cidade do clima e opção para iniciar junto com o Windows.
- **Uso consciente de recursos:** a animação do plano de fundo é pausada automaticamente quando outro aplicativo ou jogo está em primeiro plano.

## Comece a usar — Windows

1. Baixe o arquivo `SmartTV-<versão>.zip` em **[Releases](../../releases/latest)** ou use a cópia disponível na pasta [download/](download/).
2. Extraia o conteúdo em uma pasta do computador ou em um pendrive.
3. Execute `INICIAR-TV.bat`.
4. Para sair do modo TV, segure **View + Menu** no controle, use **Ajustes → Sair do modo TV** ou pressione **Alt+F4**.

**Requisitos:** Windows 10 ou 11 e Microsoft Edge. Instale pela Microsoft Store os aplicativos que deseja acessar; os aplicativos compatíveis instalados são identificados pela interface.

## Smart TV OS — Linux

A edição Linux está sendo construída como uma alternativa independente para quem deseja dedicar um computador à experiência de TV. A ISO Live permite iniciar o sistema por um pendrive e avaliar o ambiente antes de qualquer instalação no disco.

**Atenção:** a ISO é experimental. O instalador Calamares utiliza uma configuração genérica e o processo de instalação permanente ao lado do Windows ainda não foi validado em hardware real. No momento, recomendamos testar pelo pendrive em modo Live e não instalar no disco principal até que o procedimento esteja devidamente validado.

- [Guia de instalação, criação do pendrive, particionamento, loja e transmissão](linux/GUIA-INSTALACAO.md)
- [Como baixar, gerar e publicar a ISO](linux/COMO-PUBLICAR-ISO.md)
- [Visão do produto e experiência Smart TV](linux/VISAO-TV-EXPERIENCIA.md)
- [Jogos no Linux: Steam, Proton, controles, Heroic e emuladores](linux/gaming/README.md)
- [Transmissão entre aplicativos e receptores — destino TV Sala](linux/CAST-APPS-E-RECEPTORES.md)

### Sobre transmissão e dual boot

A ISO experimental inclui UxPlay para espelhamento AirPlay básico, iniciado manualmente e protegido por PIN. Google Cast universal, receptor Miracast, controle remoto próprio pelo celular e transmissão integrada dentro dos aplicativos ainda estão em desenvolvimento ou sem compatibilidade confirmada. O suporte varia conforme o aplicativo, o dispositivo e o protocolo; não há garantia de funcionamento universal.

Para um futuro dual boot, o espaço destinado ao Linux deve ser liberado no Windows como **Não alocado**. O Linux deverá ocupar uma partição própria. Não formate a partição EFI nem as partições existentes do Windows. Uma partição separada para jogos é opcional. Consulte o [guia completo](linux/GUIA-INSTALACAO.md) antes de alterar o disco.

## Biblioteca de prompts e desenvolvimento com IA

O repositório também mantém uma biblioteca organizada de prompts para apoiar a continuidade do projeto com ferramentas de IA. Ela reúne o contexto e as regras gerais, a experiência da interface, a arquitetura Linux/ISO e os critérios de qualidade, testes e publicação.

**[Acessar a biblioteca de prompts](PROMPTS/README.md)**

## Desenvolvimento

### Windows

- Gere a pasta e o ZIP de distribuição:

  `python3 pc/build.py --out out/SmartTV --zip out/SmartTV.zip`

- Para executar a suíte de testes:

  `pc/test.sh [minutos]`

A suíte verifica compatibilidade com Windows PowerShell 5.1, código do controle em C# 5, decisões de navegação, servidor local em ambiente simulado e interface Chromium em diferentes tamanhos de tela, fundos e testes de resistência.

### Linux

Para testar o backend em Debian 13:

```bash
sudo apt install python3 chromium curl
./linux/run.sh
```

Para construir a ISO experimental em Debian 13:

```bash
sudo apt install live-build debootstrap squashfs-tools xorriso
sudo linux/build-iso.sh
```

## Estrutura do projeto

| Pasta | Conteúdo |
|---|---|
| `web/` | Interface principal: HTML, CSS e JavaScript |
| `web/fundos.js` | Planos de fundo da edição Windows |
| `pc/` | Integração com o Windows, servidor local, aplicativos e controles |
| `assets/` | Idiomas, ícones, fontes e configurações iniciais |
| `linux/` | Sistema Linux experimental, backend, ISO e documentação |
| `PROMPTS/` | Biblioteca de prompts e contexto de desenvolvimento |

## Licença

Este projeto é distribuído sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE).
