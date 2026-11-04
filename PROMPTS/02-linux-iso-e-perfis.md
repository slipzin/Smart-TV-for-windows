# Prompt 02 — Edição Linux, ISO e perfis TV/Console

Atue como engenheiro Linux/DevOps responsável pela edição experimental Smart TV OS baseada em Debian 13 Trixie amd64. Leia `linux/README.md`, `linux/GUIA-INSTALACAO.md`, os manifestos de pacotes e o workflow antes de alterar a imagem.

## Arquitetura desejada

- Modo TV é o perfil padrão, leve e voltado a streaming, mídia, Bluetooth/controles, PipeWire, Chromium, Kodi/VLC, aceleração gráfica e loja Discover/Flatpak.
- Jogos em nuvem (por exemplo, Xbox Cloud Gaming, GeForce NOW e Boosteroid) são acessados no próprio computador por navegador/atalhos compatíveis; disponibilidade depende de conta, região, assinatura e suporte do serviço.
- Modo Console é opcional e instalado somente após escolha explícita. Reúne Steam, Wine/Proton, Lutris, Heroic, Bottles, GameMode, MangoHud, Gamescope e emuladores conforme manifestos separados.
- Jogos locais são executados no hardware da máquina. Compatibilidade depende de GPU, drivers, Proton, DRM e anti-cheat.
- Não instalar o conjunto gamer na base Modo TV.

## Regras de implementação

1. Preserve separação entre manifestos TV e Console.
2. Faça o instalador Console solicitar confirmação e oferecer modo de simulação/plano quando aplicável.
3. Valide nomes de pacotes Debian, IDs Flatpak e disponibilidade de componentes externos.
4. Não baixar catálogos inteiros desnecessariamente em testes.
5. Garanta que scripts sejam idempotentes, tratem erros e não executem comandos destrutivos sem confirmação.
6. Preserve boot Live e inicialização em hardware amd64 compatível.
7. Não presumir que instalação permanente ou dual boot estejam seguros: essa etapa requer validação física e procedimentos de recuperação.

## Construção e validação

- Execute os testes em `linux/test.sh` e o validador de manifestos.
- Construa a ISO pelo script oficial e verifique existência, tamanho e checksum.
- Confirme que o workflow publica ISO e SHA-256 como artefato.
- Para Releases, mantenha publicação opt-in e prerelease até haver autorização para versão estável.
- Não altere `main` nem faça merge sem autorização explícita.

## Relatório obrigatório

Informe a versão/base Debian, arquitetura, pacotes incluídos em cada perfil, testes e resultados, tamanho/checksum da ISO, artefatos gerados e limitações que ainda exigem teste em hardware real.
