# Instalador Smart TV OS — assistente gráfico e planejamento seguro

O assistente gráfico em português inspeciona o computador e permite simular
um plano de dual boot. **Ainda não instala o sistema no disco.**

## O que existe nesta fase

- Inspeção somente leitura de discos, UEFI, volumes NTFS candidatos, volumes
  BitLocker identificáveis e partições EFI pelo GUID GPT correto.
- Pré-detecção de Windows usando uma entrada `os-prober` do tipo Windows/chain
  associada a uma EFI FAT válida ou ao próprio volume NTFS Basic Data.
- Bloqueio da associação quando existem vários volumes NTFS Basic Data no
  mesmo disco; o assistente não tenta adivinhar qual seria o Windows.
- Leitura da geometria de espaço não alocado por disco.
- Interface Qt em tela maximizada, em português, com boas-vindas, diagnóstico,
  seleção de destino e revisão.
- Validador fail-closed: exige UEFI/GPT, pré-detecção no mesmo disco, região
  livre idêntica à geometria lida, EFI FAT do mesmo disco com ao menos 100 MiB,
  confirmação do usuário e reconhecimento da situação do BitLocker.
- O resultado contém `preflight_valid=true` apenas para indicar coerência do pré-plano,
  com `validation_scope=read_only_preflight_simulation`. Isso **não** significa
  que Windows/BCD/BitLocker foram verificados nem que a instalação foi autorizada:
  `windows_installation_verified=false`, `bitlocker_state_verified=false`,
  `installation_authorized=false` e `execution_enabled=false`.
- A confirmação de BitLocker na interface é somente ciência do usuário; não
  comprova suspensão/desativação. Uma detecção positiva de volume BitLocker
  bloqueia até mesmo a validação simulada.

## Limites da detecção

A associação `os-prober + NTFS Basic Data único` é apenas uma pré-detecção.
Ela não comprova que o volume contém uma instalação Windows funcional. Antes
de qualquer futura operação de escrita será necessário inspecionar o volume
Windows em modo somente leitura, verificar diretórios e arquivos essenciais,
validar a configuração BCD e confirmar que o identificador do volume bate
com o inventário atual.

O Linux não consegue certificar nesta etapa se o BitLocker está suspenso ou
desativado. Uma caixa de confirmação do usuário não é prova técnica e não
pode, sozinha, liberar um instalador destrutivo. A instalação real deve
continuar bloqueada até que essa condição possa ser verificada de forma
confiável e a chave de recuperação esteja disponível.

## Regras de segurança

1. Não aceitar Legacy/BIOS nem disco que não seja GPT.
2. Não formatar a partição EFI existente.
3. Não formatar nem modificar partições existentes.
4. Nunca usar partição NTFS como destino; somente linha Free Space reportada
   pelo parted pode ser considerada.
5. Exigir no mínimo 40 GiB não alocados, alinhamento de 1 MiB e EFI com ao
   menos 100 MiB.
6. Não escolher automaticamente entre múltiplos volumes NTFS Basic Data.
7. Não tratar a pré-detecção como autorização para instalar ou alterar o boot.
8. Exigir seleção explícita e revisão do plano.
9. Nenhuma operação de escrita é executada nesta versão.

## Executar testes

Na raiz do repositório:

```bash
linux/test.sh
```

## Dependências da interface

A imagem Live inclui python3-pyqt5. Para executar manualmente:

```bash
PYTHONPATH=linux python3 -m installer.gui
```

## O que falta antes de uma instalação real

- Verificação somente leitura do volume Windows, arquivos de sistema e BCD.
- Verificação confiável do estado do BitLocker e da chave de recuperação.
- Segunda inspeção de geometria imediatamente antes de qualquer escrita.
- Testes da interface com hardware e escalas de tela diferentes.
- Motor transacional de instalação e recuperação, ainda não implementado.
- Instalação da base Linux exclusivamente dentro do espaço não alocado.
- Configuração e validação do GRUB sem formatar a EFI existente.
- Testes de integração em imagens de disco e VM com snapshots, incluindo
  Windows 10/11, Secure Boot, BitLocker, discos SATA/NVMe e múltiplos discos.
- Teste de recuperação do Windows Boot Manager e do boot Linux.

**Estado atual:** interface de diagnóstico e planejamento em modo sem escrita.
Não use esta versão para instalar o Smart TV OS em um computador real.
