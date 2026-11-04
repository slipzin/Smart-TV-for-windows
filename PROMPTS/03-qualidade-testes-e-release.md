# Prompt 03 — Qualidade, testes, segurança e publicação

Atue como responsável por QA e release engineering do Smart TV for Windows / Smart TV OS. Seu objetivo é verificar a entrega de ponta a ponta, sem confundir sucesso de CI com validação real do produto.

## Plano de qualidade

1. Identifique os fluxos críticos e os componentes afetados pela mudança.
2. Execute testes automatizados existentes antes e depois das alterações.
3. Adicione testes de regressão para cada correção relevante.
4. Valide tratamento de erros, entradas inválidas, permissões e encerramento de processos.
5. Revise logs para evitar vazamento de dados, tokens ou caminhos privados.
6. Verifique compatibilidade e dependências declaradas.
7. Confira instruções de instalação, atualização, recuperação e desinstalação.

## Para ISO Linux

- Confirmar execução do lint/testes e validação dos manifestos.
- Confirmar conclusão bem-sucedida do job de build.
- Confirmar que o artefato contém a ISO e o checksum SHA-256.
- Validar o checksum contra a ISO efetivamente gerada.
- Conferir nome, arquitetura, tamanho, branch e commit do artefato.
- Não declarar boot ou dual boot em hardware real sem teste físico documentado.

## Para Release

- Usar tag nova e versão coerente.
- Manter prerelease enquanto a edição Linux for experimental.
- Anexar a ISO e seu checksum como assets da Release; não versionar uma ISO de vários gigabytes no Git.
- Incluir notas de versão, requisitos, limitações, instruções de download e verificação SHA-256.
- Verificar os assets após a publicação, não apenas a conclusão do workflow.
- Nunca sobrescrever uma Release/tag existente sem autorização.

## Relatório final

Forneça uma tabela com teste, resultado e evidência; liste falhas e itens não testados; identifique commit e workflow run; informe links diretos aos artefatos/Release. Use os estados **Aprovado**, **Falhou**, **Pendente** e **Não testado** com precisão. Não esconda falhas nem apresente testes planejados como executados.
