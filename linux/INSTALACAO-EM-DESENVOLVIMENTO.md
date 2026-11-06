# Instalação permanente — assistente em desenvolvimento

A ISO Live agora inclui um assistente gráfico em português para diagnóstico e
planejamento. Ele permite consultar discos, UEFI, Windows, EFI e regiões livres
e revisar um plano simulado de dual boot.

**Ainda não existe instalação permanente nesta versão.** O assistente não cria
partições, não formata, não monta sistemas de arquivos, não copia o sistema e
não altera entradas de boot. A mídia USB continua sendo apenas um ambiente Live
de diagnóstico e teste.

Não execute instalação no disco que contém o Windows. A instalação futura só
poderá ser liberada após confirmação confiável do Windows 10/11, geometria
exata do espaço não alocado, estado do BitLocker e partição EFI existente,
além de revisão explícita e testes de recuperação. A EFI não deverá ser
formatada em nenhuma hipótese.
