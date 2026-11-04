# Smart TV OS — guia completo de download, pendrive e dual boot

> **Aviso importante: versão experimental.**
>
> Esta edição é baseada no Debian 13 e foi criada para testar a interface Smart TV em um PC Linux. A ISO contém o ambiente KDE Plasma, o launcher Smart TV, a loja KDE Discover e o instalador Calamares. Mesmo com o instalador presente, o procedimento de instalação permanente e o dual boot com Windows ainda precisam de validação em computadores reais.
>
> **Recomendação atual:** primeiro use o modo Live pelo pendrive. Não instale no disco principal que contém o Windows até que o fluxo de particionamento e recuperação tenha sido testado e declarado pronto pelo projeto. Este guia explica o planejamento correto e os pontos que precisam ser conferidos; não é uma garantia de instalação sem risco.

## 1. Antes de começar: ISO, pendrive e partição são coisas diferentes

Esta é a dúvida mais importante para um dual boot:

- **A ISO não precisa de uma partição no HD.** Ela é um arquivo de imagem usado para criar o pendrive inicializável. Depois de gravada, o computador inicia pelo pendrive.
- **O espaço para o Linux é reservado no HD/SSD interno.** No Windows, você diminui a partição C: e deixa o espaço liberado como “Não alocado”.
- **O Linux é instalado nesse espaço não alocado.** Ele terá uma partição própria para o sistema.
- **A loja de aplicativos instala os programas dentro do espaço do Linux.** Normalmente não é necessário criar uma partição separada para a loja ou para cada aplicativo.
- **Os jogos também podem usar o espaço da partição Linux.** Uma partição ou outro SSD exclusivo para jogos é opcional, útil apenas quando se deseja separar uma biblioteca muito grande.

Em outras palavras: não crie uma partição chamada “ISO”. O pendrive guarda a mídia de instalação/teste; o HD recebe o sistema Linux depois que a instalação for validada.

## 2. O que vem nesta edição

A ISO experimental está sendo preparada com:

- **Debian 13 Trixie, amd64** — destinada a computadores Intel/AMD de 64 bits.
- **KDE Plasma** — área de trabalho e menu de programas.
- **Smart TV OS** — interface em tela cheia, com suporte a controle, teclado e mouse.
- **Chromium** — usado para exibir a interface Smart TV.
- **KDE Discover** — loja gráfica de aplicativos e atualizações do Debian.
- **UxPlay + Avahi** — receptor inicial de AirPlay Mirror, com atalho manual protegido por PIN; não é AirPlay 2 completo.
- **Flatpak e integração do Discover com Flatpak** — suporte para catálogo Flatpak; na compilação atual o repositório Flathub é habilitado na imagem.
- **Kodi e VLC** — reprodução de mídia.
- **Lutris, GameMode e MangoHud** — ferramentas relacionadas a jogos e desempenho.

A interface Linux procura aplicativos que tenham lançadores de desktop compatíveis. A loja Discover pode instalar aplicativos do repositório Debian. Com o Flathub configurado, também pode apresentar aplicativos distribuídos como Flatpak.

### O que não está incluído ou não é garantido

- **A ISO inicia em Modo TV leve.** Steam, Wine/Proton, Lutris, GameMode, MangoHud e emuladores não são instalados por padrão. Para jogar pela rede, instale Moonlight ou Steam Link pelo KDE Discover. Para baixar jogos e executá-los localmente, selecione Modo Console em Ajustes do Início e rode o instalador gamer opcional a partir do desktop; o cliente Steam é então instalado na conta do usuário.
- Nem todo aplicativo Windows tem versão Linux.
- Compatibilidade de jogos depende de GPU, drivers, Proton e sistemas antitrapaça. Alguns jogos não funcionam no Linux.
- Serviços de streaming podem ter limitações de DRM, resolução ou controle dependendo do serviço e do navegador.
- A compatibilidade de Wi-Fi, Bluetooth, áudio, suspensão, controles e placas NVIDIA varia por computador.
- O instalador Calamares desta imagem usa uma configuração genérica. A instalação ao lado do Windows ainda não foi validada para todos os cenários.

## 3. Quanto espaço reservar no HD/SSD?

O Linux precisa de espaço livre no disco interno, separado da partição do Windows. O espaço deve ser suficiente para o próprio sistema, aplicativos baixados pela loja, atualizações e, se desejado, jogos.

Como referência de planejamento — não como requisito mínimo oficial:

| Uso pretendido | Espaço sugerido para o Linux |
|---|---:|
| Sistema e aplicativos básicos | 80 a 100 GB |
| Sistema, aplicativos e alguns jogos | 200 GB ou mais |
| Biblioteca grande de jogos | 300 a 500 GB ou mais, conforme os jogos |

Jogos modernos podem ocupar dezenas ou centenas de gigabytes. Verifique o tamanho dos jogos que pretende instalar e deixe espaço livre para atualizações.

### Partições: o arranjo recomendado para começar

Em um computador Windows instalado em UEFI/GPT, o cenário esperado é:

| Área do disco | O que fazer |
|---|---|
| Partição EFI (FAT32) já existente | Reutilizar para iniciar o Linux, normalmente montada em /boot/efi, **sem formatar** |
| Partição Windows (NTFS, geralmente C:) | Preservar; **não formatar nem excluir** |
| Partições MSR e Recuperação do Windows | Preservar; **não formatar nem excluir** |
| Espaço que você liberou no Windows | Usar para criar a partição Linux em ext4, montada em / |

A partição Linux principal, montada em /, guarda o sistema e o espaço usado por aplicativos instalados pela loja. Aplicativos Flatpak também ocupam espaço no armazenamento Linux — globalmente ou na conta do usuário, dependendo de como forem instalados.

**Não é necessário criar uma partição separada para /home, para a loja ou para aplicativos.** Para uma primeira instalação, manter sistema e arquivos do usuário dentro da mesma partição Linux reduz a quantidade de decisões e erros possíveis.

Uma partição adicional para jogos pode ser planejada mais tarde, por exemplo uma partição ext4 montada em /games, ou uma biblioteca em outro SSD. Isso é opcional e não deve ser feito por quem ainda não domina particionamento.

Para jogos Steam/Proton, mantenha a biblioteca no armazenamento Linux (ext4) ou em outro volume Linux adequado. Não recomendamos compartilhar a mesma biblioteca Steam entre Windows e Linux numa partição NTFS: os prefixos Proton, links simbólicos e diferenças de nomes/maiúsculas podem causar incompatibilidades. A partição Windows deve continuar preservada para o Windows.

## 4. Requisitos

- Computador com processador Intel ou AMD de 64 bits.
- Pendrive vazio de 16 GB ou maior.
- Conexão com a internet para baixar a ISO e testar a loja.
- Teclado e mouse para o primeiro teste, mesmo que a intenção seja controlar a TV com um gamepad.
- Backup de todos os arquivos importantes antes de alterar partições.
- Para uma experiência mais confortável, recomendamos 8 GB de RAM ou mais. Jogos podem exigir muito mais memória e uma GPU compatível.

A gravação da ISO apaga todo o conteúdo do pendrive. Confirme que escolheu o dispositivo USB certo.

## 5. Baixar a ISO

A imagem é disponibilizada como artefato do GitHub Actions:

1. Abra a página de [execuções do workflow de criação da ISO](https://github.com/slipzin/Smart-TV-for-windows/actions/workflows/linux-iso.yml).
2. Entre na execução mais recente da branch **feature/linux-dual-boot-foundation** que terminou com **Success**.
3. No final da página, procure a seção **Artifacts**.
4. Baixe **SmartTV-OS-Live-Debian13-amd64**.
5. Extraia o ZIP. Ele deve conter a ISO e seu arquivo SHA-256.

Se a execução estiver em andamento, falhou ou não mostrar a seção Artifacts, ainda não há uma ISO pronta naquela execução. Não use artefatos de uma compilação que falhou.

O nome esperado da imagem é:

    SmartTV-OS-live-trixie-amd64.iso

Os artefatos deste workflow têm retenção limitada (atualmente 30 dias). Se o arquivo tiver expirado, será necessário gerar uma nova execução bem-sucedida.

## 6. Conferir o arquivo baixado

O SHA-256 ajuda a verificar se a ISO baixada corresponde ao arquivo publicado.

### No Windows

1. Coloque a ISO e o arquivo .sha256 na mesma pasta.
2. Abra o PowerShell nessa pasta.
3. Execute:

    Get-FileHash .\SmartTV-OS-live-trixie-amd64.iso -Algorithm SHA256

4. Compare o valor exibido em Hash com o valor no arquivo .sha256.

Os valores precisam ser idênticos. Se forem diferentes, baixe novamente o artefato. Não grave uma ISO cuja conferência falhou.

### No Linux

Na pasta onde estão os dois arquivos, execute:

    sha256sum -c SmartTV-OS-live-trixie-amd64.iso.sha256

O resultado esperado termina com:

    SmartTV-OS-live-trixie-amd64.iso: OK

## 7. Criar o pendrive inicializável

> **Atenção: o pendrive inteiro será apagado.** Não selecione o HD ou SSD interno do computador.

### Opção A — balenaEtcher

1. Baixe o [balenaEtcher no site oficial](https://etcher.balena.io/).
2. Conecte o pendrive.
3. Abra o Etcher e escolha **Flash from file**.
4. Selecione a ISO extraída.
5. Clique em **Select target** e selecione o pendrive correto.
6. Confira nome e capacidade do dispositivo USB.
7. Clique em **Flash** e confirme.
8. Aguarde a gravação e a verificação terminarem.

### Opção B — Rufus

1. Baixe o [Rufus no site oficial](https://rufus.ie/).
2. Conecte o pendrive e abra o Rufus.
3. Em **Dispositivo**, selecione o pendrive correto.
4. Em **Seleção de boot**, selecione a ISO.
5. Inicie a gravação.
6. Se o Rufus perguntar sobre o modo de gravação da imagem híbrida, escolha **DD Image mode**.
7. Confirme e aguarde o término.

Não remova o pendrive durante a gravação. Ao terminar, ejete-o com segurança.

**Mensagem de formatação no Windows:** depois de gravar, o Windows pode dizer que precisa formatar uma unidade ou que não consegue ler uma partição. Cancele. Não formate o pendrive: ele agora contém partições Linux que o Windows pode não conseguir abrir.

## 8. Iniciar pelo pendrive e testar o modo Live

O modo Live executa o sistema diretamente do USB. É a primeira etapa recomendada e não exige modificar o disco interno.

1. Desligue o computador completamente.
2. Conecte o pendrive.
3. Ligue o computador e pressione repetidamente a tecla do **Menu de Boot**. Exemplos comuns são F12, F11, F9 ou Esc; isso depende do fabricante.
4. Na lista, selecione o pendrive. Se houver duas opções, prefira **UEFI: nome do pendrive** quando o Windows também estiver em UEFI.
5. Aguarde o Debian iniciar e entrar no KDE Plasma.
6. A interface Smart TV deve abrir automaticamente. O menu do KDE também permite abrir aplicativos e a loja Discover.

Se o pendrive não aparecer, confira a seção de solução de problemas. Não altere várias opções do firmware sem saber o que fazem.

### O que testar

Antes de qualquer instalação, confira:

- O computador inicia pelo USB repetidamente.
- A resolução está correta na TV ou no monitor.
- O áudio funciona na saída desejada, inclusive HDMI se for o caso.
- Wi-Fi ou Ethernet conectam à internet.
- Teclado, mouse e controle USB/Bluetooth funcionam.
- A interface Smart TV abre, responde ao controle e retorna depois de sair de um aplicativo.
- Kodi e VLC abrem.
- A loja Discover abre e consegue consultar os repositórios.
- A GPU não apresenta tela preta, travamentos ou superaquecimento.

O modo Live é temporário. Aplicativos e configurações instalados durante esse teste podem desaparecer quando o computador for reiniciado. Isso é esperado; o pendrive de teste não deve ser usado como instalação permanente.

Para sair, desligue o sistema pelo menu. Remova o pendrive somente depois que o computador estiver desligado.

## 9. Preparar o Windows para o dual boot

> Faça backup antes. Redimensionar partições e alterar a inicialização pode causar perda de dados. Se não conseguir identificar o disco ou as partições com certeza, pare e peça ajuda técnica.

### 9.1 Fazer backup

1. Copie documentos, fotos, trabalhos e arquivos importantes para um HD externo ou armazenamento em nuvem.
2. Abra alguns arquivos do backup para confirmar que foram copiados corretamente.
3. Tenha disponível um pendrive de recuperação/instalação do Windows.
4. Em computador de empresa ou escola, consulte o administrador antes de alterar o disco.

### 9.2 Verificar BitLocker ou Criptografia do Dispositivo

1. No Windows, pesquise **Gerenciar BitLocker** ou **Criptografia do dispositivo**.
2. Se a unidade estiver criptografada, localize e guarde a chave de recuperação de 48 dígitos em local seguro e separado do PC.
3. Confirme que consegue acessar a chave.
4. Antes de uma instalação permanente, suspenda temporariamente a proteção conforme a documentação da Microsoft. Depois de confirmar que Windows e Linux iniciam corretamente, retome a proteção.

Consulte [como fazer backup da chave de recuperação do BitLocker](https://support.microsoft.com/pt-br/windows/security/encryption/back-up-your-bitlocker-recovery-key). Nunca publique essa chave em fóruns ou capturas de tela.

### 9.3 Desativar a Inicialização Rápida

1. Abra o **Painel de Controle**.
2. Entre em **Opções de Energia**.
3. Escolha **Escolher a função dos botões de energia**.
4. Clique em **Alterar configurações não disponíveis no momento**.
5. Desmarque **Ligar inicialização rápida** e salve.

### 9.4 Identificar UEFI ou Legacy

1. Pressione **Win + R**.
2. Digite **msinfo32** e pressione Enter.
3. Procure **Modo da BIOS**.
4. Anote se aparece **UEFI** ou **Herdado/Legacy**.

O pendrive e o instalador devem ser iniciados no mesmo modo de firmware usado pelo Windows. Este guia descreve principalmente o cenário UEFI/GPT. Se seu Windows usa Legacy/MBR, não siga o particionamento UEFI sem um procedimento específico.

### 9.5 Liberar espaço no Windows sem criar um volume

1. Inicie o Windows normalmente.
2. Pressione **Win + R**, digite **diskmgmt.msc** e pressione Enter.
3. Identifique o disco que contém o Windows, normalmente a unidade C:.
4. Clique com o botão direito na partição C: e selecione **Diminuir Volume**.
5. Informe o espaço que deseja liberar para o Linux.
6. Confirme e aguarde.
7. Ao final, o Gerenciamento de Disco deverá mostrar uma área **Não alocada**.

**Não crie um novo volume NTFS nesse espaço.** Deixe-o não alocado para que o instalador Linux possa usá-lo. Não exclua, não formate e não redimensione as partições EFI, MSR ou Recuperação do Windows.

Consulte o guia da Microsoft sobre [Gerenciamento de Disco no Windows](https://support.microsoft.com/pt-br/windows/experience/storage-filemanagement/disk-management-in-windows).

### Exemplo de planejamento

Se você liberar 200 GB, esses 200 GB serão destinados ao Linux. Na instalação, o objetivo é criar uma partição Linux ext4 dentro desse espaço. O sistema, a loja e os aplicativos vão ocupar essa partição. Não reserve uma parte desses 200 GB para guardar a ISO: a ISO está no pendrive.

Se desejar uma biblioteca enorme de jogos, planeje espaço adicional antes de instalar. Uma partição de jogos separada é opcional e pode ser configurada depois, quando o sistema básico estiver estável.

## 10. Instalação permanente ao lado do Windows: atenção ao estado experimental

<badge>Não recomendado para iniciantes nesta versão</badge>

O Calamares está presente na ISO, mas a configuração do instalador ainda é genérica e o fluxo de dual boot não foi validado em hardware real. Por isso, **não recomendamos instalar esta versão no computador principal com Windows e dados importantes**. O uso recomendado agora é o modo Live ou uma máquina virtual com disco descartável e snapshot.

O roteiro abaixo explica o que precisa ser conferido em um teste. As telas e opções do instalador podem variar; se não corresponderem ao que está descrito, cancele.

### 10.1 Conferência antes de abrir o instalador

Todos estes itens precisam estar confirmados:

- Backup testado.
- Chave BitLocker salva, se aplicável.
- Windows inicia normalmente.
- Existe espaço **Não alocado** no disco certo.
- O pendrive foi iniciado no mesmo modo UEFI/Legacy do Windows.
- Você identificou o disco correto por modelo e capacidade.
- Não há outro disco com arquivos importantes que possa ser selecionado por engano.

### 10.2 Abrir o Calamares em ambiente de teste

1. No KDE, localize o atalho **Instalar Smart TV OS** na área de trabalho.
2. Abra o instalador.
3. Revise idioma, região, fuso horário e teclado.
4. Na seleção do disco, compare modelo e capacidade com o disco que você preparou.
5. Leia a etapa de particionamento e a prévia das mudanças com atenção.

Se o instalador oferecer somente apagar o disco, se não reconhecer o Windows, se não mostrar claramente o espaço não alocado ou se sugerir formatar o disco inteiro, **cancele**.

### 10.3 Resultado de particionamento esperado (UEFI/GPT)

Em um futuro instalador validado, o objetivo de dual boot é:

1. Criar uma nova partição Linux **ext4**, dentro do espaço não alocado que foi reservado no Windows, montada como **/**.
2. Reutilizar a partição EFI System Partition (ESP) existente do Windows como **/boot/efi**, sem formatá-la.
3. Manter todas as partições NTFS do Windows intactas.
4. Manter as partições MSR e de Recuperação intactas.
5. Instalar o carregador de inicialização no disco correto, preservando os arquivos EFI existentes.

**Nunca marque para formatar a partição EFI existente. Nunca formate a partição NTFS do Windows.** Não exclua partições para “abrir espaço”: use somente o espaço não alocado que você criou no Windows.

A partição Linux principal é onde ficam o sistema e os programas instalados pela loja. Não é necessário criar uma partição para o Discover ou outra partição para cada aplicativo. Uma partição separada para jogos é opcional e não faz parte do primeiro passo.

Se houver uma opção explícita de instalar ao lado do Windows, ainda assim leia o resumo de alterações. Se não houver uma opção que preserve claramente o Windows e a partição EFI, não tente adivinhar no particionamento manual: cancele.

### 10.4 Revisão obrigatória antes de confirmar

Antes de qualquer botão final de instalação, confirme que a tela informa claramente:

- A nova partição Linux foi criada dentro do espaço que estava não alocado.
- A partição NTFS do Windows não será formatada nem excluída.
- A partição EFI será reutilizada sem formatação.
- As partições de recuperação permanecem intactas.
- O carregador de inicialização está no disco correto.

Se a tela não permitir conferir esses itens, pare. O projeto ainda precisa testar e documentar esse fluxo em máquinas reais.

## 11. Primeira inicialização depois de uma instalação de teste

Somente em uma máquina de teste ou depois que o instalador estiver validado:

1. Desligue o computador e remova o pendrive.
2. Ligue novamente.
3. Confira se aparece um menu GRUB.
4. Teste a entrada Smart TV OS.
5. Reinicie e teste **Windows Boot Manager**.
6. No Windows, confira se arquivos e programas continuam acessíveis.
7. Só depois de comprovar que o Windows inicia normalmente, retome o BitLocker, se a proteção foi suspensa.

Se o Windows não aparecer no GRUB, não formate nada e não reinstale às pressas. O Windows Boot Manager pode continuar disponível pelo menu de boot do firmware. Procure suporte antes de executar comandos que alterem partições ou o bootloader.

## 12. Usar a loja de aplicativos depois da instalação

Depois que o Smart TV OS estiver instalado no disco e conectado à internet:

1. Abra o menu de aplicativos do KDE ou procure **Discover** na interface Smart TV.
2. Abra a loja KDE Discover.
3. Aguarde a atualização dos catálogos.
4. Pesquise o aplicativo desejado.
5. Abra a página do aplicativo e confira descrição, origem e permissões.
6. Clique em **Instalar** e autorize a operação quando o sistema solicitar.
7. Aguarde o download e a instalação.
8. Volte à interface Smart TV. Aplicativos com lançador compatível deverão aparecer no catálogo depois de atualizados.

Os aplicativos instalados pelos repositórios Debian usam espaço na partição Linux. Flatpaks também usam espaço no armazenamento Linux, mesmo quando são instalados somente para o usuário atual. A loja não instala programas na partição C: do Windows.

### Habilitar Flathub para encontrar mais aplicativos

A compilação atual configura o catálogo Flathub para o sistema. Abra o Discover, atualize os catálogos e procure o aplicativo. Se o catálogo não aparecer (por exemplo, se estiver usando uma ISO anterior), abra o Konsole e execute:

    flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

Depois, feche e abra o Discover novamente. O Flathub é uma fonte de terceiros: confira o nome do publicador, as permissões e a procedência antes de instalar qualquer aplicativo.

### Onde os aplicativos ficam instalados?

Para o usuário, o detalhe técnico pode ser resumido assim: os programas e seus dados ocupam espaço no disco Linux que foi reservado na instalação. Não é necessário escolher ou criar uma partição diferente para cada aplicativo. Se o espaço Linux acabar, será necessário liberar espaço, ampliar a partição com cuidado ou mover uma biblioteca de jogos para outro volume.


## 13. Receber mídia e conectar o celular

A ISO em desenvolvimento inclui uma primeira integração de recepção AirPlay, mas os protocolos têm compatibilidades diferentes. O menu e a documentação devem identificar qual tecnologia está ativa.

### iPhone, iPad e Mac — AirPlay básico

1. Inicie a Smart TV OS e conecte o computador e o aparelho Apple à mesma rede local.
2. Na área de trabalho KDE, abra o atalho **Receber AirPlay**.
3. Uma janela do Konsole abrirá o UxPlay. Deixe a janela aberta enquanto quiser receber a transmissão.
4. No iPhone/iPad, abra a Central de Controle e toque em **Espelhar a Tela**.
5. Selecione **Smart-TV-OS** e digite o PIN exibido no computador.
6. Para encerrar, pare o espelhamento no aparelho ou feche a janela do Konsole.

O UxPlay é uma implementação de AirPlay Mirror e áudio AirPlay. Não é um receptor de vídeo AirPlay 2 completo. Aplicativos com conteúdo protegido podem bloquear o espelhamento; a Netflix, por exemplo, não oferece AirPlay. Para esses serviços, abra a versão web/app compatível diretamente na TV.

O atalho é iniciado manualmente e protegido por PIN; ele não fica aceitando conexões automaticamente ao ligar o computador.

### Transmissão iniciada dentro do próprio aplicativo (destino "TV Sala")

O objetivo de longo prazo é permitir que o telefone e a TV funcionem como em uma Smart TV compatível:

1. Abra o serviço de streaming no celular.
2. Toque no botão **Transmitir/Cast** dentro do aplicativo.
3. Quando o serviço aceitar o receiver Smart TV OS, escolha **TV Sala**.
4. A TV abre o receiver/app compatível e reproduz o conteúdo diretamente da internet.
5. O celular controla a sessão (por exemplo, pausar, retomar e buscar), conforme os recursos permitidos pelo serviço.

Isso **não é espelhamento de tela**. O app do telefone envia o pedido de reprodução para um receiver; a TV recebe o conteúdo. Porém, cada serviço decide quais aparelhos aceita.

**Importante sobre a Netflix:** a documentação oficial atual lista apenas Chromecast de 3ª geração ou anterior sem controle remoto, Google Nest Hub e alguns modelos Vizio/Compal como destinos do Cast móvel. Um computador Linux com receiver genérico não está confirmado nessa lista. Assim, não é possível garantir que "TV Sala" apareça no botão de transmissão da Netflix. A Netflix também não oferece AirPlay. Para esse caso, a alternativa será abrir a Netflix diretamente na TV e usar o controle do sistema, ou futuramente o controle companion do Smart TV OS no celular.

A compatibilidade de Prime Video, Disney+, Max, YouTube, Spotify e cada outro serviço deverá ser testada separadamente. Não basta o telefone estar na mesma rede: o app remetente precisa aceitar o protocolo e o receiver anunciado. Veja [Cast nativo dos aplicativos — destino TV Sala](CAST-APPS-E-RECEPTORES.md).

### Android — o que já existe e o que ainda será desenvolvido

O KDE Discover com o catálogo Flathub permite instalar aplicativos de recepção que usem protocolos abertos, como o **FCast Receiver**, quando disponível no catálogo. A imagem também prepara o **VibeCast** como receptor Google Cast com o player local anunciado como **TV Sala**. O envio depende de um aplicativo Android que ofereça suporte ao protocolo FCast; isso não transforma o Smart TV OS em Chromecast universal.

O Google Cast dos aplicativos e o espelhamento completo da tela Android (Miracast/Smart View) são recursos separados. O receptor VibeCast está incluído, mas exige autenticação de dispositivo Cast válida em `~/.config/smart-tv/cast/certs.json`; esse arquivo privado não acompanha a ISO e não deve ser publicado. Sem esse material, o celular não consegue concluir a autenticação. Depois de configurado, a descoberta do dispositivo ainda depende do app remetente aceitar o receiver e do player/DRM suportar o serviço. Netflix não é provider listado pelo VibeCast v0.2.0. Não prometa compatibilidade geral antes de validar o modelo do telefone, o adaptador Wi-Fi, o aplicativo e o serviço de streaming. Consulte [a documentação do receptor TV Sala](cast/README.md).

### Controle da TV pelo celular

O controle remoto por QR code/PIN, com direcional, OK, voltar, início, volume e teclado para busca, está no plano de desenvolvimento. Não é uma função entregue nesta ISO experimental. No momento, use o controle USB/Bluetooth, teclado ou mouse.

## 14. Solução de problemas

### O pendrive não aparece no menu de boot

- Confira se a gravação terminou sem erro e se o SHA-256 confere.
- Tente outra porta USB.
- Refaça a gravação com Etcher ou Rufus em modo DD.
- Confira se selecionou a entrada UEFI quando o Windows também usa UEFI.
- Não altere várias opções do firmware de uma vez.

### Tela preta depois de iniciar

Pode haver incompatibilidade com o driver gráfico, especialmente em algumas GPUs NVIDIA ou configurações híbridas. Não instale no disco para tentar corrigir. Anote os modelos do PC e da GPU.

### Wi-Fi, Bluetooth, áudio ou controle não funciona

O suporte depende do chipset e do firmware disponíveis no Debian. Se possível, teste Ethernet e anote o modelo exato do componente para relatar o problema.

### A loja Discover abre, mas não mostra aplicativos

- Confirme que o computador está conectado à internet.
- Aguarde a atualização do catálogo.
- Verifique se os repositórios Debian estão acessíveis.
- Para aplicativos Flatpak, confirme que o Flathub foi adicionado conforme a seção anterior.

### Um aplicativo instalado não aparece na interface Smart TV

A interface lista aplicativos que fornecem um lançador Linux compatível. Feche e abra a interface Smart TV ou encerre e inicie a sessão. Alguns aplicativos podem não fornecer um atalho compatível.

### O Windows não aparece no menu GRUB

Não formate nenhuma partição. Confira se o Windows Boot Manager ainda aparece no menu de boot do firmware. A correção do GRUB precisa ser feita com cuidado para não danificar a inicialização dos dois sistemas.

## 15. Como relatar um problema

Ao abrir uma issue no repositório, informe:

- Marca e modelo do computador.
- Processador e quantidade de memória RAM.
- Modelo da GPU.
- Se o Windows usa UEFI ou Legacy.
- Se estava no modo Live ou em uma instalação de teste.
- O que tentou fazer e o que apareceu na tela.
- Fotos ou mensagens de erro, sem mostrar chaves de recuperação, senhas ou dados pessoais.

Não publique a chave BitLocker, números de série, senhas ou arquivos pessoais.

## 16. Links úteis

- [Repositório Smart TV for Windows / Smart TV OS](https://github.com/slipzin/Smart-TV-for-windows)
- [Execuções e download da ISO](https://github.com/slipzin/Smart-TV-for-windows/actions/workflows/linux-iso.yml)
- [balenaEtcher — site oficial](https://etcher.balena.io/)
- [Rufus — site oficial](https://rufus.ie/)
- [KDE Discover](https://apps.kde.org/pt-br/discover/)
- [Debian — Flatpak](https://wiki.debian.org/Flatpak)
- [Microsoft — chave de recuperação BitLocker](https://support.microsoft.com/pt-br/windows/security/encryption/back-up-your-bitlocker-recovery-key)
- [Microsoft — Gerenciamento de Disco](https://support.microsoft.com/pt-br/windows/experience/storage-filemanagement/disk-management-in-windows)

---

**Resumo para não errar:** grave a ISO no pendrive; no Windows, diminua C: e deixe o espaço como **Não alocado**; instale o Linux somente nesse espaço quando o instalador estiver validado; preserve a partição EFI e todas as partições do Windows. O sistema e os aplicativos da loja compartilham o espaço Linux. A partição exclusiva para jogos é opcional.
