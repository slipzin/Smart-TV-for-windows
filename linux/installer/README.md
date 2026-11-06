# Instalador Smart TV OS — assistente gráfico e planejamento seguro

O assistente gráfico em português apresenta a inspeção do computador, permite
selecionar um disco GPT, uma região explicitamente não alocada e uma EFI do
mesmo disco. A leitura de espaço livre usa apenas o comando de consulta
\`parted ... print free\`.

## O que existe nesta fase

- Inspeção somente leitura de discos, UEFI, possíveis partições Windows,
  volumes BitLocker identificáveis e partições EFI pelo GUID GPT correto.
- Leitura da geometria de espaço não alocado por disco.
- Interface Qt em tela maximizada, em português, com boas-vindas, diagnóstico,
  seleção de destino e revisão.
- Validador fail-closed: exige Windows confirmado pelo os-prober, GPT/UEFI,
  região livre idêntica à geometria lida, EFI FAT do mesmo disco, confirmação
  do usuário e reconhecimento da situação do BitLocker.
- A interface não contém rotina de particionamento, formatação, cópia do
  sistema, montagem, fstab ou instalação do GRUB.

## Regras de segurança

1. Não aceitar Legacy/BIOS nem disco que não seja GPT.
2. Não formatar a partição EFI existente.
3. Não formatar nem modificar partições existentes.
4. Nunca usar partição NTFS como destino; somente linha Free Space reportada
   pelo parted pode ser considerada.
5. Exigir no mínimo 40 GiB não alocados e alinhamento de 1 MiB.
6. Exigir Windows 10/11 confirmado pelo os-prober; uma partição NTFS isolada
   não comprova que há Windows instalado.
7. O estado do BitLocker não pode ser certificado pelo Linux nesta fase.
   A confirmação solicitada na interface é uma declaração do usuário, não
   uma detecção técnica. A futura instalação deve continuar bloqueada até
   haver uma verificação confiável e a chave de recuperação disponível.
8. Exigir seleção explícita e revisão do plano.
9. O resultado sempre contém execution_enabled=false.

## Executar testes

Na raiz do repositório:

\`\`\`bash
linux/test.sh
\`\`\`

## Dependências da interface

A imagem Live inclui python3-pyqt5. Para executar manualmente:

\`\`\`bash
PYTHONPATH=linux python3 -m installer.gui
\`\`\`

## O que falta antes de uma instalação real

- Verificação confiável do estado do BitLocker e da chave de recuperação.
- Testes da interface com hardware e escalas de tela diferentes.
- Integração de um motor de instalação transacional e recuperação.
- Instalação de base Linux em partição criada exclusivamente dentro do espaço
  não alocado, com segunda leitura da geometria imediatamente antes da escrita.
- Configuração e validação do GRUB sem formatar a EFI existente.
- Testes de integração em imagens de disco e VM com snapshots, incluindo
  Windows 10/11, Secure Boot, BitLocker, discos SATA/NVMe e múltiplos discos.
- Teste de recuperação do Windows Boot Manager e do boot Linux.

**Estado atual:** interface de diagnóstico e planejamento em modo sem escrita.
Não use esta versão para instalar o Smart TV OS em um computador real.
