# PRE590_HANDOFF_PRE587_LIVE_UNLINKED_VLT_MARCEK_SUCCESS_20261109

**Data:** 2026-11-09 (America/Bahia). **Projeto:** NFSMW-Recompiled-Mobile, APK release V48 PRE452, BMW M3 GTR carreira `type=41`.

## Resultado de dispositivo informado pelo usuário

- Após aplicar `pre587_apply_bmw_unlinked_vlt_shevery.sh` (atualização comunicada na conversa; saída exata `PRE587_RESULTADO` e hashes atuais do celular não foram fornecidos), o usuário afirmou **"Agora carregou"** e anexou um novo `nfsmw.log`. É um teste de sucesso de carregamento do perfil com a variante de nova coleção VLT não vinculada, conforme estado comunicado, não readback binário direto do telefone.
- Arquivo anexado `nfsmw.log`: **454.088 bytes**, **2.472 linhas**, SHA-256 **`509900a226ef281ab92a8567d818cb38e5afdb98a434bc77d0216fea384a2957`**. Analisado localmente neste chat; não publicar o log integral ou o conteúdo do save no repositório.
- **Três sessões concatenadas**: 01:42:45 (controle original), 01:58:25 (PRE581 torque-only, segundo relatos prévios) e **02:25:13** (nova sessão PRE587). A interpretação abaixo se restringe à terceira sessão, a mais recente.
- Na sessão PRE587, o VFS montou `/storage/emulated/0/NFSMW_PTBR` em `\\Device\\Harddisk0\\Partition1` às **02:25:14.185**, somente leitura, **26 entradas**. A contagem de entradas 22→24→26 decorre da presença de arquivos na árvore entre sessões, mas não atribuir nomes aos novos arquivos sem listagem.
- Aos **02:25:15.320** ocorreu tentativa direta `D:\\GLOBAL\\ATTRIBUTES.BIN` com `NtCreateFile -> 0xc000000f`, como nas sessões anteriores. Aos **02:25:15.369** o runtime registrou leitura de **5.018.060 bytes** de `NFS\\ZZDATA4.BIN` no offset **37.898.240**. **Não há nesta terceira sessão uma linha explícita de leitura de 698.004 bytes no offset zero** nem digest do recurso VLT, portanto **não afirmar que o novo recurso foi validado byte a byte no guest**, embora o resultado positivo de carreira seja consistente com a aplicação relatada.
- Aos **02:25:21.454**, **02:25:22.004**, **02:25:22.037** e **02:25:25.170**: quatro `XamContentCreate` com `resultado 00000000` em `MARCEK`, com **62.688 bytes**. O usuário confirmou o sucesso de carregamento; a abertura do contêiner isoladamente não garantiria o conteúdo da carreira.
- **Novo dado:** às **02:25:33.706–02:25:33.841**, há `crear «MARCEK»`, `XamContentCreate ... modo 2 -> crear (resultado 00000000)`, fechamento do contêiner com 62.688 bytes e cópia para `.../saves/MARCEK/actual`. Logo, o **jogo registrou atividade de escrita** no save durante essa sessão; não afirmar que o conteúdo original foi preservado byte a byte ou que nova peça foi instalada.
- Às **02:25:47.320**, logs `NFSMW_PRE429_ENTRY manager=0x82C5D9E8 tuning_car=0xAD68FA64 pvehicle=0x00000000` e `NFSMW_PRE292_BMW_MENU ... type=41 event=1`: o caminho de interface da BMW foi atingido. `pvehicle=0` naquela chamada não demonstra upgrade instalado nem prova seu valor posterior em runtime.
- Há **um** `[error]` na terceira sessão às **02:25:33.456**: mecanismo de texturas `C3` desligado por `DIFERENCIA: indice de textura en vuelo incoherente ... copia_duplicada=true`. É um mecanismo/fallback de validação gráfica, **não foi demonstrada relação causal com PRE587**; não esconder o erro nem declarar sessão sem erro. Não há `[critical]` ou `[fatal]`.
- Resolução interna indicada no início da última sessão: **1920×1080**, limite efetivo **60 FPS**. A meta de 120 FPS do projeto permanece; não mudar qualidade, térmicas ou FPS neste teste.

## Matriz de compatibilidade até o momento

1. **Arquivos PT-BR originais**: `MARCEK` carrega (PRE579, usuário confirmou).
2. **PRE573 combinado**: VLT/ExpN/PtrN/RefSpec + contador pvehicle motor 0→1 + nova coleção + torque sintético +5%: interface mostrou `MARCEK está corrompido` e não carregou.
3. **PRE581 torque-only**: estrutura VLT/contador originais, apenas 24 bytes alterados em nove torques sintéticos: `MARCEK` carrega (PRE584, usuário e log).
4. **PRE587 nova coleção VLT *não vinculada***: preserva original contador motor 0 e original ponteiro de `RefSpec` do pvehicle enquanto inclui nova coleção/Export/PtrN: `MARCEK` **carrega**, confirmado pelo usuário e log, inclusive entrada na UI de BMW.

**Conclusão limitada:** a presença de uma coleção VLT ampliada e **não vinculada à BMW ativa** não bloqueou o uso da carreira nesta sessão. O fracasso da PRE573 aponta para a mudança de vínculo/contador, interação entre elas ou outro efeito da variante ativa. Ainda faltam testes isolados para distinguir campos. A ausência de leitura explícita do primeiro recurso na terceira sessão impede afirmar aceitação universal do recurso por todos os caminhos guest.

## Próximo gate

- **Não reaplicar PRE573.** Criar variante diagnóstica `PRE591`: estrutural `PRE586` com **apenas ponteiro `RefSpec` reativado** para o array stock+novo, mantendo `pvehicle` motor `0` e restante do VPAK intacto. Compará-la à PRE587 para saber se a mudança de referência ativa, sem subir contador, é compatível com carregar `MARCEK`. Preparar arquivos em Drive privado somente após SHA/EA checksum/ZIP verificados. Não fabricar APK.
- Para eventual execução no S24 FE, **antes restaurar PRE587** (somente com V48 completamente fechada) e confirmar `PRE587_RESTORE=ORIGINAIS_VERIFICADOS`. A variante seguinte exige o SHA dos arquivos originais; scripts PRE587 não podem ser usados com novos fragmentos.
- Se o vínculo sozinho funcionar, testar posteriormente contador 0→1 sob condições controladas e sem dados fora do layout. Se falhar, investigar sem assumir corrupção irreparável do save.
- Objetivo final continua tunagem BMW comprável, instalável, física e persistente. Ainda **não foi alcançado**. Não confundir o registro de `MARCEK` criado com prova de persistência do novo item de tunagem.

**Preservações:** APK V48 PRE452, package `io.github.nfsmwrecomp`, cert SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, Nitro PRE398, PG9076/touch, resolução 1920×1080, meta 120 FPS, qualidade/shaders/física geral e proteção térmica. Nenhuma mudança de APK, save ou jogo via GitHub durante esta análise.
