# Prompt 00 — Contexto, arquitetura e regras obrigatórias

Você está contribuindo com o projeto **Smart TV for Windows + Smart TV OS (Linux)**, disponível neste repositório. Leia o README e a documentação da área que será alterada antes de editar código.

## Objetivo do projeto

Transformar um computador em uma experiência de televisão de sala, com interface em tela cheia, navegação por controle de videogame, teclado ou mouse, catálogo de aplicativos e reprodução de mídia. O repositório contém duas frentes distintas:

- **Edição Windows:** launcher que abre aplicativos já instalados no Windows e não deve ser quebrado por mudanças da edição Linux.
- **Smart TV OS Linux:** edição experimental baseada em Debian 13 Trixie amd64, com KDE Plasma, interface Smart TV e backend Linux.

## Regras de trabalho

1. Preserve a edição Windows e suas funcionalidades existentes.
2. Trabalhe na branch indicada pelo responsável. Para a frente Linux, a branch de trabalho é `feature/linux-dual-boot-foundation`.
3. **Não altere nem faça merge na branch `main` sem autorização explícita.**
4. Antes de modificar, inspecione a implementação e reutilize padrões existentes. Evite reescrever componentes sem necessidade.
5. Faça alterações pequenas, coerentes e reversíveis.
6. Não introduza credenciais, tokens, certificados privados, chaves ou dados pessoais no repositório.
7. Não afirme que algo foi implementado, testado ou publicado sem evidência verificável.
8. Atualize a documentação quando mudar comportamento, dependências, instalação ou limitações.
9. Execute os testes relevantes e informe comandos, resultados e limitações.
10. Ao concluir, liste arquivos alterados, decisões, riscos e próximos passos.

## Precisão de produto

- Diferencie recursos implementados, experimentais, planejados e não suportados.
- AirPlay Mirror via UxPlay não equivale a AirPlay 2 completo.
- Google Cast, FCast, DLNA e Miracast são tecnologias diferentes; não as apresente como sinônimos.
- Receiver Cast genérico não garante compatibilidade com cada serviço de streaming. Validar aplicativo por aplicativo; não prometer Netflix Cast sem comprovação.
- Jogos em nuvem são executados no próprio computador conectado à TV; não pressupor que o usuário tenha um segundo PC.
- Steam/Proton e emuladores pertencem ao perfil opcional Console, não à instalação padrão Modo TV.
- A instalação permanente e o dual boot com Windows não devem ser anunciados como seguros/validados até testes em hardware real.

## Formato esperado da resposta

Apresente: resumo da alteração, arquivos afetados, testes executados e resultado, limitações conhecidas e instruções para reproduzir. Separe claramente fatos verificados de hipóteses e recomendações.
