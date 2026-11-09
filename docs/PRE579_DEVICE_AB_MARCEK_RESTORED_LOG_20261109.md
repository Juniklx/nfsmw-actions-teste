# PRE579 — CONTROLE A/B NO DISPOSITIVO: MARCEK VOLTA A CARREGAR (2026-11-09)

**Resultado comunicado pelo usuário:** após a orientação para restaurar os arquivos PT-BR originais com o script de rollback da PRE573, respondeu: **"Consegui carregar o save normalmente"**. Um novo arquivo `nfsmw.log` foi anexado nesta conversa e analisado localmente. **A resposta não continha a saída literal do script de rollback nem hashes diretos dos arquivos do telefone**; a associação ao rollback é fundamentada pela sequência de teste, não por verificação remota de bytes. Nenhum teste de tunagem BMW foi reportado com os dados experimentais ativos.

## Evidência do arquivo novo

- Nome fornecido: `nfsmw.log`. Tamanho **112.350 bytes**, **665 linhas**, SHA-256 **`83522f3f328bc9385c8fb9ebf20b6f0b668f4a7519db08a4d38d4881ffa37cde`**; timestamps internos `2026-11-09 01:42:45.174` até `01:43:03.933` (hora indicada no log).
- Linha 127: `/storage/emulated/0/NFSMW_PTBR` montado em `\\Device\\Harddisk0\\Partition1` com **22 entradas**, `solo lectura`.
- Linhas 428, 440, 448, 461: o save `MARCEK` foi localizado com **62.688 bytes**, no contêiner `rmcsave`. Linhas 430, 442, 450, 463: quatro retornos `XamContentCreate ... resultado 00000000`.
- Linhas 432, 444, 452 e 467: quatro cópias internas do save para `.../saves/MARCEK/actual`.
- Após 01:43:00, registradas consultas a recursos do ambiente de carreira, incluindo busca `CAREER_SAFEHOUSE.LZC` via `NtCreateFile` (retorno `0xc000000f` para arquivo direto) e leitura de `NFS/ZZDATA0.BIN`. **Não afirmar que o arquivo CAREER_SAFEHOUSE independente foi aberto com sucesso**: é um aviso de tentativa por caminho direto, possivelmente seguido do acesso pelo arquivo empacotado.
- Não há string literal de erro de save corrompido no log novo. Isso, sozinho, não provaria sucesso da carreira, mas o **usuário confirmou explicitamente que conseguiu carregar normalmente**.
- A sessão informa resolução interna 1920×1080 com cap de 60 FPS, não 120; apenas descrição do estado observado, não otimização.

## Comparação com a sessão anterior PRE573

- Sessão **com fragmentos PRE572 aplicados via PRE573**, segundo `PRE573_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS` fornecido pelo usuário: captura mostrava `MARCEK está corrompido.`; PRE577 analisou o primeiro log com 154.955 bytes, SHA-256 `5ef32c7a3cab4f6219a34a0f790d37b50570d7797e63a9cd108d12bb38eed2e0`. Acesso ao contêiner do save era bem-sucedido, mas a carreira não carregava.
- Sessão **após instrução de restauração dos dados originais**: novo `nfsmw.log`, mesmo save de 62.688 bytes, carreia carregada com sucesso de acordo com o usuário.
- **Inferência forte, ainda não prova causal definitiva:** o bloqueio de carregamento estava associado aos dados experimentais PRE573. Não foi verificado byte a byte no telefone se os dois arquivos retornaram exatamente ao estado original nem qual alteração de VPAK/ExpN/RefSpec/PtrN/pvehicle gerou o conflito.
- O aviso de `corrompido` **não significa necessariamente dano permanente ao arquivo `MARCEK`**; na sessão controle o arquivo voltou a carregar.
- Componente a investigar: modificação experimental de `GLOBAL/ATTRIBUTES.BIN` (primeiros 341 setores de `ZZDATA4.BIN`) e linha 805 de `ZDIR.BIN`, não a assinatura/instalação da V48.

## Próximo gate sem repetir experimento falho

1. Não reaplicar o pacote combinado PRE573 diretamente. Manter a situação restaurada e o save carregável como **baseline funcional**.
2. Preparar somente em GitHub Actions/Drive uma variante de diagnóstico **de alteração mínima, sem repack VLT, sem novo ExpN/RefSpec/PtrN, sem alterar o limite do motor `pvehicle`**. Ela poderá diferenciar se uma alteração de valor físico com o layout original intacto também afeta o carregamento do perfil. Esta é proposta experimental, não calibração final.
3. Somente após inspeção dos hashes, criar novo script de aplicação/rollback com backup distinto e com janela de teste no telefone explicitamente informada, nunca reutilizar PRE573 com entradas parcialmente diferentes.
4. Se variante mínima carregar o save, há evidência apontando para estrutura/pointer/catálogo do pacote combinado. Se também falhar, investigar validade/checksum VPAK e integração do loader, sem conclusões automáticas.
5. Continuar objetivo final de **tunagem comprável, instalável, física e persistente para BMW M3 GTR**, que ainda não está ativada.

**Preservações:** APK V48 PRE452 `io.github.nfsmwrecomp`, assinatura permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, Nitro PRE398, controle PG-9076/touch, 1920×1080, cap desejado 120 FPS, qualidade, física geral, salvamentos, e proteções térmicas. Nenhuma alteração foi realizada pelo ato de analisar o log e criar este relatório. **Nova compilação V49: NÃO.**
