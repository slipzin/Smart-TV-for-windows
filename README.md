# Smart TV for Windows + Smart TV OS (Linux)

Transforme o computador numa smart TV. Uma tela inicial em tela cheia, no estilo das TVs mais modernas, comandada pelo
**controle de video game**, pelo teclado ou pelo mouse. Ela abre os **aplicativos instalados no Windows** (Netflix,
Prime Video, Disney+, Apple TV, Spotify, Xbox, Battle.net, Steam no modo Big Picture e outros), sem nada pelo
navegador. Não instala nada e não muda o Windows: roda direto de um pendrive.

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

A branch `feature/linux-dual-boot-foundation` inicia a migração para um sistema Linux independente, sem remover a edição Windows. Ela preserva a interface web, adiciona um backend Linux com descoberta de aplicativos nativos/Flatpak, integração com Steam Big Picture e uma base para ISO Live Debian 13.7 amd64.

**Ainda não é uma ISO estável nem um instalador dual boot validado.** A imagem experimental usa Calamares e precisa de testes em máquinas UEFI reais antes de instalação permanente. Veja [linux/README.md](linux/README.md) para os requisitos, a construção da imagem, os cuidados com partições e as limitações atuais.

Para testar o backend diretamente em Debian 13:

```bash
sudo apt install python3 chromium curl
./linux/run.sh
```

Para construir a ISO experimental em Debian 13:

```bash
sudo apt install live-build debootstrap squashfs-tools xorriso
sudo linux/build-iso.sh
```

## Licença

MIT. Veja `LICENSE`.
