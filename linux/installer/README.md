# Instalador Smart TV OS — fundação de segurança

O instalador está sendo desenvolvido em etapas. Esta branch ainda não deve ser
usada para instalar o sistema no disco: a execução de operações destrutivas
continua desabilitada.

## Componentes existentes

- `smarttv_installer.py`: inventário somente leitura de discos, modo UEFI,
  possíveis instalações Windows e partições EFI.
- `disk_plan.py`: validador puro de um plano de instalação em dual boot.
  Ele aceita como alvo apenas uma região explicitamente não alocada, exige GPT
  e UEFI, exige confirmação do usuário e valida o reaproveitamento da EFI sem
  formatá-la.
- `test_installer.py` e `test_disk_plan.py`: testes com inventário simulado.

## Regras de segurança implementadas no planejador

1. Não aceitar inicialização Legacy/BIOS nem disco que não seja GPT.
2. Não formatar a partição EFI existente.
3. Não formatar nem modificar partições existentes.
4. Não escolher automaticamente uma partição Windows como destino.
5. Exigir uma região não alocada de pelo menos 40 GiB e tamanho raiz dentro
   dessa região.
6. Bloquear o plano se BitLocker estiver detectado até que a proteção seja
   resolvida no Windows e a chave de recuperação esteja disponível.
7. Exigir confirmação explícita da revisão do plano.
8. O retorno informa `execution_enabled: false`: ainda é apenas simulação.

## Executar testes

Na raiz `linux`, em ambiente Python com a biblioteca padrão:

```bash
python3 -m unittest discover -s installer -v
```

## O que falta antes de uma instalação real

- Leitura de geometria real (setores inicial/final) com segunda inspeção
  imediatamente antes de qualquer escrita.
- Interface gráfica em português (assistente de boas-vindas, teclado, discos,
  resumo e progresso).
- Integração testada com Calamares ou um frontend equivalente.
- Motor transacional de particionamento, instalação, fstab e GRUB com rollback.
- Testes de integração em imagens de disco e VM com snapshots, incluindo
  Windows 10/11, Secure Boot, BitLocker, discos SATA/NVMe e múltiplos discos.
- Validação de recuperação do Windows Boot Manager e do boot Linux.

**Estado atual:** planejamento e validação em modo sem escrita. Nenhuma
partição é criada, redimensionada, formatada ou montada. Não use esta versão
para instalar o Smart TV OS em um computador real.
