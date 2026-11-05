# Instalação permanente — em desenvolvimento

A ISO atual é destinada a inicialização Live e testes da interface. A fase 1 do instalador personalizado foi iniciada: existe uma ferramenta de pré-verificação somente leitura para inventariar discos, modo UEFI, possíveis instalações Windows e partições EFI. Ainda não existe assistente gráfico nem mecanismo de particionamento/instalação.

**Não execute particionamento ou instalação no disco que contém o Windows.** A configuração genérica do Calamares não oferece, nesta versão, as garantias exigidas pelo Smart TV OS para preservar Windows, EFI e partições de dados.

O assistente final deverá detectar UEFI/GPT, identificar Windows e a partição EFI existente, permitir escolher espaço não alocado ou outro disco, mostrar uma revisão completa das alterações e bloquear qualquer operação ambígua ou destrutiva. A partição EFI existente nunca deverá ser formatada.

Até que esses requisitos sejam implementados e testados em máquina virtual com snapshots e em hardware compatível, use somente o modo Live pelo pendrive.
