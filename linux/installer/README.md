# Instalador Smart TV OS — fase 1

Esta fase adiciona o primeiro componente executável do instalador personalizado:
**inspeção somente leitura** do modo de boot, discos/partições, possíveis instalações
Windows e partições EFI.

## Executar

```bash
python3 /usr/local/lib/smarttv-installer/smarttv_installer.py --inspect
python3 /usr/local/lib/smarttv-installer/smarttv_installer.py --inspect --json
```

O relatório não altera o computador. A instalação permanece deliberadamente
bloqueada: ainda não existe código de particionamento, formatação, cópia do sistema,
configuração do GRUB ou restauração/validação do Windows Boot Manager.

## Próximas fases

1. Inspeção robusta de GPT/UEFI, Windows, BitLocker e geometria real de espaço livre.
2. Interface guiada em português com seleção de disco e revisão explícita.
3. Motor de instalação transacional com salvaguardas, sem formatar a EFI existente.
4. Configuração e validação do menu de dual boot, com recuperação em caso de falha.
5. Testes automatizados com imagens de disco e testes em VM com snapshots.

Nenhuma fase posterior poderá habilitar escrita até que a revisão de segurança e os
testes de recuperação estejam concluídos.
