# Smart TV for Windows + Smart TV OS (Linux)

Transforme o computador numa smart TV. Uma tela inicial em tela cheia, no estilo das TVs mais modernas, comandada pelo
**controle de video game**, pelo teclado ou pelo mouse. Ela abre os **aplicativos instalados no Windows** (Netflix,
Prime Video, Disney+, Apple TV, Spotify, Xbox, Battle.net, Steam no modo Big Picture e outros), sem nada pelo
navegador. Não instala nada e não muda o Windows: roda direto de um pendrive.

## Projeto e prompts de desenvolvimento

Este repositório reúne duas edições relacionadas: **Smart TV for Windows**, um launcher portátil para aplicativos já instalados no Windows, e **Smart TV OS**, uma edição Linux experimental baseada em Debian 13 para transformar um PC em uma central de entretenimento de sala. A documentação registra o estado real de cada recurso, os limites de compatibilidade e os passos de teste.

**[Biblioteca de prompts para continuar o desenvolvimento com IA](PROMPTS/README.md)** — contexto geral, experiência da interface, arquitetura Linux/ISO e critérios de qualidade e publicação.

## Destaques

- **Tela inicial de TV**: prateleira de apps, relógio, clima, cotações e destaques de filmes e séries (com uma chave
  gratuita do TMDB, digitada uma vez nos ajustes).
- **Controle de video game**: Xbox, PlayStation e outros na tela inicial. Dentro dos apps, o controle de Xbox ganha
  mouse no analógico direito e o botão View volta para a tela inicial.
- **Jogos**: o botão Jogos abre a Steam no modo Big Picture; o Call of Duty da Steam aparece sozinho.
- **Personalização**:
  - plano de fundo: 5 animados (Aurora, Ondas, Céu estrelado, Cores fluidas, Bolhas), 6 estáticos, ou os seus:
    imagens (inclusive GIF animado) e vídeos da pasta **Fundos**, com troca automática;
  - velocidade da animação, escurecer e desfocar o fundo, tema claro ou escuro, idioma, cidade do clima;
  - **abrir junto com o Windows**, para o PC já ligar na tela de TV.
- **Leve**: a animação do fundo para sozinha quando um app ou jogo está na frente.

## Instalar

1. Baixe o `SmartTV-<versão>.zip` em **[Releases](../../releases/latest)** e extraia no pendrive ou no PC.
   (O mesmo ZIP também fica em [`download/`](download/).)
2. Dê dois cliques em **`INICIAR-TV.bat`**.
3. Para sair: segure **View + Menu** no controle, use **Ajustes > Sair do modo TV**, ou aperte **Alt+F4**.

Precisa de Windows 10 ou 11 com o Microsoft Edge (já vem no Windows). Instale pela Microsoft Store os apps que quiser
ver na tela: eles aparecem sozinhos.

## Para desenvolver

- `python3 pc/build.py --out out/SmartTV --zip out/SmartTV.zip` monta a pasta e o ZIP.
- Subir a versão em `pc/build.py` (`VERSION`) e enviar ao `main` publica a Release dela sozinha (`.github/workflows/release.yml`).
- `pc/test.sh [minutos]` testa tudo sem precisar de Windows: compatibilidade com o Windows PowerShell 5.1, o código
  do controle em C# 5, as decisões do controle, o servidor de verdade num "PC simulado" (apps, fundos, vídeos em
  trechos, abrir com o Windows, ataques) e a tela no Chromium com um controle simulado (8 tamanhos de tela, todos os
  planos de fundo e um teste longo de resistência).

| Pasta | O quê |
|---|---|
| `web/` | a tela inicial (HTML, CSS e JavaScript ES5) |
| `web/fundos.js` | os planos de fundo |
| `pc/tv.ps1` | o lado do Windows: servidor local, apps, controle |
| `assets/` | idiomas, ícones, fonte e ajustes iniciais |


## Edição Linux experimental (dual boot em desenvolvimento)

A branch \`feature/linux-dual-boot-foundation\` inicia a migração para um sistema Linux independente, sem remover a edição Windows. Ela preserva a interface web, adiciona um backend Linux para aplicativos nativos/Flatpak e prepara uma ISO Live Debian 13.7 amd64 com KDE Plasma e a loja KDE Discover.

> **Atenção:** a ISO é experimental. O instalador Calamares usa uma configuração genérica e o fluxo de instalação permanente ao lado do Windows ainda não foi validado em hardware real. A recomendação atual é testar pelo pendrive no modo Live; não instale no disco principal com Windows até que o procedimento seja validado.

**[Leia o guia completo da ISO, criação do pendrive, espaço em disco, instalação, loja e AirPlay](linux/GUIA-INSTALACAO.md).**  
**[Baixe a ISO publicada e veja como gerar/publicar novas versões](linux/COMO-PUBLICAR-ISO.md).**  
**[Veja a visão completa do produto: interface premium, streaming, AirPlay, Android Cast e controle pelo celular](linux/VISAO-TV-EXPERIENCIA.md).**
**[Veja a integração gamer Linux: jogos locais pela Steam, Proton, controles, Heroic e emuladores](linux/gaming/README.md).**  
**[Veja como funcionará a transmissão dentro dos apps, com destino TV Sala](linux/CAST-APPS-E-RECEPTORES.md).**
**[Veja os dois perfis de jogos Linux: Modo TV com streaming e Modo Console com jogos locais](linux/gaming/README.md).**

Importante sobre as partições: a ISO é gravada no pendrive, não em uma partição do HD. A ISO experimental inclui UxPlay para AirPlay Mirror básico, ativado manualmente e protegido por PIN; Cast nativo dentro dos apps (destino TV Sala), Google Cast universal, Miracast receiver e controle remoto próprio pelo celular ainda estão em desenvolvimento. A Netflix limita atualmente o Cast móvel a determinados aparelhos; um receiver Linux genérico não tem suporte confirmado. Para um futuro dual boot, o Windows deve liberar espaço como **Não alocado**; o Linux será instalado nesse espaço em uma partição própria. O sistema e os aplicativos da loja usam essa partição Linux. Não formate a partição EFI ou as partições do Windows. Uma partição exclusiva para jogos é opcional.

Para testar o backend diretamente em Debian 13:

    sudo apt install python3 chromium curl
    ./linux/run.sh

Para construir a ISO experimental em Debian 13:

    sudo apt install live-build debootstrap squashfs-tools xorriso
    sudo linux/build-iso.sh

## Licença

MIT. Veja `LICENSE`.
