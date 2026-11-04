# Publicação e download da ISO — Smart TV OS

Este documento descreve o fluxo oficial de compilação e publicação da ISO no repositório.

## Onde baixar

Quando houver uma versão Linux publicada, use a página [Releases](https://github.com/slipzin/Smart-TV-for-windows/releases) e escolha a prerelease com o título **Smart TV OS** (tag no formato `v0.1.0-alpha.1`). Não confunda com a Release **Smart TV for Windows 1.0**, que contém somente o ZIP da edição Windows.

A Release Linux disponibiliza a ISO compactada em 7z e seus checksums. Se o arquivo 7z exceder o limite de 2 GiB por asset do GitHub, o workflow o divide automaticamente em volumes de 1800 MiB.

### Extrair e verificar

1. Baixe o arquivo `SmartTV-OS-live-trixie-amd64.7z` ou, se houver volumes, baixe **todos** os arquivos `.7z.001`, `.7z.002` etc. para a mesma pasta.
2. Baixe também `SmartTV-OS-live-trixie-amd64.7z.sha256` e `SmartTV-OS-live-trixie-amd64.iso.sha256`.
3. Verifique os arquivos 7z com o checksum publicado. No Linux, execute `sha256sum -c SmartTV-OS-live-trixie-amd64.7z.sha256` na pasta dos downloads.
4. Extraia com 7-Zip (Windows) ou 7zz (Linux). Se houver volumes, abra/extrai somente a partir do arquivo `.7z.001`, mantendo os demais volumes na mesma pasta.
5. Verifique a ISO extraída com `sha256sum -c SmartTV-OS-live-trixie-amd64.iso.sha256` no Linux. No Windows, compare o resultado de `Get-FileHash .\SmartTV-OS-live-trixie-amd64.iso -Algorithm SHA256` com o valor publicado no arquivo de checksum.

Se ainda não existir uma Release, o artefato temporário fica na [execução do workflow Linux ISO](https://github.com/slipzin/Smart-TV-for-windows/actions/workflows/linux-iso.yml), na seção **Artifacts**. Artefatos do Actions expiram após 30 dias; Releases não seguem essa retenção.

## Gerar uma ISO e publicar uma prerelease

1. Abra [Actions → Build Smart TV OS Live ISO](https://github.com/slipzin/Smart-TV-for-windows/actions/workflows/linux-iso.yml).
2. Selecione **Run workflow**.
3. Escolha a branch `feature/linux-dual-boot-foundation`.
4. Para apenas compilar e gerar um artefato temporário, mantenha **publish_release** desmarcado.
5. Para publicar a ISO compactada como GitHub Release, marque **publish_release**.
6. Informe uma tag nova, por exemplo `v0.1.0-alpha.1`. Não reutilize uma tag já existente.
7. Execute o workflow e aguarde o job terminar com **Success**.
8. Abra [Releases](https://github.com/slipzin/Smart-TV-for-windows/releases) e confira se a prerelease contém o arquivo 7z (ou todos os volumes) e os dois arquivos SHA-256.

A publicação é opt-in: um push normal compila e guarda o artefato no Actions, mas **não** cria uma Release. O workflow valida o formato da tag e publica os arquivos somente quando a opção for marcada.

## Segurança e estado do produto

- A branch de trabalho é `feature/linux-dual-boot-foundation`; a branch `main` não é alterada por este fluxo.
- A Release é criada como **prerelease**, não como versão estável.
- O workflow executa testes automatizados, valida os manifestos de pacotes, constrói a ISO, gera o arquivo 7z e os checksums antes da publicação.
- Uma compilação bem-sucedida não comprova compatibilidade universal nem instalação segura em dual boot.
- Não publique certificados privados Cast, chaves BitLocker, senhas ou dados pessoais.

Consulte também o [guia completo de instalação e teste Live](GUIA-INSTALACAO.md) e as [notas da versão](RELEASE-NOTES.md).
