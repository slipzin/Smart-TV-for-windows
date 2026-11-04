# Publicação da ISO — Smart TV OS

Este documento descreve o fluxo oficial de compilação e publicação da ISO no repositório.

## Onde baixar

Quando houver uma versão publicada, use a página [Releases](https://github.com/slipzin/Smart-TV-for-windows/releases). Baixe os dois arquivos anexados à versão:

- `SmartTV-OS-live-trixie-amd64.iso`
- `SmartTV-OS-live-trixie-amd64.iso.sha256`

Se ainda não existir uma Release, o artefato temporário fica na [execução do workflow Linux ISO](https://github.com/slipzin/Smart-TV-for-windows/actions/workflows/linux-iso.yml), na seção **Artifacts**. Artefatos do Actions expiram após 30 dias; Releases não seguem essa retenção.

## Gerar uma ISO e publicar uma prerelease

1. Abra [Actions → Build Smart TV OS Live ISO](https://github.com/slipzin/Smart-TV-for-windows/actions/workflows/linux-iso.yml).
2. Selecione **Run workflow**.
3. Escolha a branch `feature/linux-dual-boot-foundation`.
4. Para apenas compilar e gerar um artefato temporário, mantenha **publish_release** desmarcado.
5. Para publicar a ISO como GitHub Release, marque **publish_release**.
6. Informe uma tag nova, por exemplo `v0.1.0-alpha.1`. Não reutilize uma tag já existente.
7. Execute o workflow e aguarde o job terminar com **Success**.
8. Abra [Releases](https://github.com/slipzin/Smart-TV-for-windows/releases) e confira se a prerelease contém a ISO e o arquivo SHA-256.

A publicação é opt-in: um push normal compila e guarda o artefato no Actions, mas **não** cria uma Release. O workflow valida o formato da tag e publica os dois arquivos somente quando a opção for marcada.

## Segurança e estado do produto

- A branch de trabalho é `feature/linux-dual-boot-foundation`; a branch `main` não é alterada por este fluxo.
- A Release é criada como **prerelease**, não como versão estável.
- O workflow executa testes automatizados, valida os manifestos de pacotes, constrói a ISO e gera o SHA-256 antes da publicação.
- Uma compilação bem-sucedida não comprova compatibilidade universal nem instalação segura em dual boot.
- Não publique certificados privados Cast, chaves BitLocker, senhas ou dados pessoais.

Consulte também o [guia completo de instalação e teste Live](GUIA-INSTALACAO.md) e as [notas da versão](RELEASE-NOTES.md).
