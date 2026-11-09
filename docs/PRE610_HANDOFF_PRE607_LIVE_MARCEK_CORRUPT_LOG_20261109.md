# PRE610 — RESULTADO REAL PRE607: MARCEK REJEITADO, HERANÇA BMW CORRIGIDA INSUFICIENTE (2026-11-09)

**Projeto:** NFSMW-Recompiled-Mobile, Need for Speed Most Wanted 2005 Xbox 360 USA → Android, APK V48 PRE452, pacote `io.github.nfsmwrecomp`, Samsung Galaxy S24 FE. **Evidência nesta conversa:** captura de tela anexada pelo usuário e arquivo `nfsmw.log` anexado e efetivamente analisado nesta conversa. **Não** há neste turno confirmação textual de `PRE607_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS` nem SHA256 independente dos arquivos ativos no Android; por isso o diagnóstico exato de aplicação PRE607 é **presumido pela sequência de instruções, não comprovado por readback**.

## Imagem observada

A captura enviada mostra o próprio jogo na interface espanhola: **`MARCEK está corrompido.`**, com botão Ok. Overlay do jogo na captura indica **58 fps / 17,3 ms**; esta é uma medição momentânea de FPS e não um benchmark de desempenho. A screenshot não fornece stack trace nem prova que bytes do save em repouso tenham sido corrompidos.

## Log anexado realmente lido

- `nfsmw.log` local do chat: **219.076 bytes, 1.324 linhas, SHA256 `489ba96f60d3eccdbd9e7d5b456e6c39a4f582a430787529e1dd9ab834e7c033`**. Log foi lido na íntegra localmente, não publicado (nem save) no GitHub.
- Contém **duas sessões**, separadas pela linha 676:
  - Primeira sessão **2026-11-09 04:27:55.751**, anteriormente associada à PRE592, com VFS PTBR **28 entradas**; em conversa anterior usuário confirmou que MARCEK carregou.
  - **Segunda sessão** (novo teste) **2026-11-09 07:53:21.442 a 07:53:39.396**, VFS PTBR `/storage/emulated/0/NFSMW_PTBR` montado como `\\Device\\Harddisk0\\Partition1` aos **07:53:22.198**, read-only, **30 entradas**. A variação 28→30 é compatível com novos arquivos de backup no diretório, mas não identifica nem autentica os binários ativos.
- Em **07:53:23.278**, tentativa direta `D:\\GLOBAL\\ATTRIBUTES.BIN` retornou `0xc000000f`, como na sessão anterior; o arquivo costuma ser lido do arquivo compactado `NFS/ZZDATA4.BIN`. **Não apareceu no log da segunda sessão leitura explícita de `NFS/ZZDATA4.BIN`** ou hash VPAK; portanto **não afirmar que a nova coleção foi carregada ou validada byte a byte**.
- `MARCEK` **62.688 bytes**, localizado em diretório privado; operações de `XamContentCreate` bem-sucedidas com `resultado 00000000` às **07:53:29.221, 07:53:29.787, 07:53:29.841, 07:53:32.963**, todas modo `3 -> abrir`. Houve cópia/fechamento de `MARCEK` para diretório de trabalho `saves/MARCEK/actual`, mas não prova integridade dos bytes do save nem sucesso da validação do jogo.
- **Zero** ocorrências `[error]`, `[critical]`, `[fatal]` na segunda sessão; muitas mensagens `[warning]` de busca por arquivos soltos inexistentes ou leitura lenta, que também aparecem em outras execuções funcionais. **Não aparece no log a string de corrupção/causa**; a evidência da rejeição efetiva é a captura.
- Não houve evento `NFSMW_PRE292_BMW_MENU` ou `NFSMW_PRE429_ENTRY` na nova sessão; a oficina de tunagem BMW **não foi testada** na PRE607. Resolução interna reportada 1920×1080, limite de 60 FPS (meta do projeto 120). Não atribuir erro a shaders/temperatura sem evidência.

## Comparação controlada

- PRE573/PRE502: BMW motor=1, coleção VLT nova e `RefSpec` ativo, coleção sintética derivada de `default`; aviso `MARCEK está corrompido`.
- PRE592/PRE591: BMW motor=0 com mesma lista `RefSpec` e coleção VLT sintética; MARCEK carregou, confirmado pelo usuário em teste anterior.
- PRE607/PRE606: BMW motor=1 com o mesmo VPAK PRE502 exceto **quatro bytes do parent da coleção nova** (default `eec2271a` → BMW stock `cd88083f`); no novo teste, captura mostra **mesma rejeição da carreira**.
- **Conclusão:** apenas trocar o parent para herança BMW stock **não eliminou a rejeição neste teste**. Não é prova de irrelevância do parent em toda condição, mas suficiente para **não repetir essa mesma variante**. O caminho ativado por motor=1 (e.g., segunda `RefSpec`, lookup/atributo/controle de save) continua suspeito, **não identificado**. Não afirmar que 1 seja sempre inválido.
- O console informou abertura bem-sucedida do *contêiner* de save, não necessariamente validação da carreira. Não declarar `MARCEK` fisicamente corrompido sem teste após rollback.

## Ação imediata no telefone (não executada remotamente)

1. **Fechar completamente a V48**.
2. No Shevery, executar **somente** `sh /sdcard/Download/pre607_restore_bmw_child_parent_corrected_shevery.sh "/storage/emulated/0/NFSMW_PTBR"`. Esse script exige SHA de backups PTBR originais e do par PRE607 ativo e preserva o par experimental; ele recusa se hashes ou backups divergirem. **Exigir `PRE607_RESTORE=ORIGINAIS_VERIFICADOS`**.
3. Após essa confirmação, abrir a V48 e testar `MARCEK` com os arquivos PTBR originais. **Se carregar novamente**, reforça incompatibilidade dos assets experimentais com o caminho de validação do perfil; se continuar rejeitado, examinar erro e snapshot do save antes de qualquer outra alteração.
4. Se o rollback recusar, não misturar backups PRE592, PRE607 ou de outras variantes e não repetir scripts às cegas. Anexar saída para auditoria.
5. Não deletar `MARCEK`, não limpar os dados do aplicativo, não compilar V49, não reaplicar PRE573 ou PRE607. O usuário anteriormente aceitou criar outro perfil, mas não solicitou apagar o existente.

## Próxima direção de desenvolvimento

Propor **gate read-only** que compare a sequência `engine pvehicle counter=1`, `RefSpec` 2 entradas, `ExpN`/destino `PtrN` e registro da nova coleção `engine`; investigar instrumentação de caminho de validação guest *sem* lançar novo patch de dados que reproduza a corrupção. A PRE599–601 reclassificou falsos candidatos de `GetMaxLevel`; não assumir identificação dessas funções.

**Preservações:** V48 PRE452, package `io.github.nfsmwrecomp`, cert SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; Nitro PRE398, PG9076/touch, 1920×1080, shaders/efeitos/física completa, prot. térmicas. Nenhum script de projeto no CI neste turno alterou jogo, APK, saves ou assinatura. **Estado de rollback PRE607: PENDENTE de confirmação do usuário.**
