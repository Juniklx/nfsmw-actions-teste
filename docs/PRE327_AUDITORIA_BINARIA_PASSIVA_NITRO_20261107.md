# PRE327 — Auditoria binária passiva de referências ao Nitro (2026-11-07)

## Motivação comprovada
- PRE323 demonstrou `sub_82424AF0` e a origem do ponteiro `r31=ctx.r3` sem provar o owner.
- PRE324 encontrou só a definição do símbolo entre referências textuais.
- PRE325 ampliou a busca textual e corrigiu o reconhecimento exato do símbolo; o relatório da execução ainda não foi recuperado.
- PRE326 produziu analisador offline de endereços do marcador PRE247; o log bruto PRE321 V41 não estava acessível neste atendimento, portanto sem resultado real.

## Nova auditoria PRE327 publicada
- Script: `automation/kaggle/pre327_nitro_binary_xrefs_readonly.py`.
- Regressão sintética: `automation/kaggle/pre327_nitro_binary_xrefs_mock.py` (sete asserts; execução CI ainda não conferida).
- Workflow: `.github/workflows/nfsmw-pre327-nitro-binary-xrefs-readonly.yml`.
- Acionamento final após proteção de nomes sensíveis: `automation/kaggle/pre327_requests/launch_pinned_sensitive_guard_20261107.json`, commit `bdc11be42b16f25de88787abd25a09bdb0c08adb`.
- Endereço PAL auditado: `0x82424AF0` (decimal `2185382640`); procura sequências binárias big endian `82 42 4A F0` e little endian `F0 4A 42 82`.
- Fonte: backup PRE99 no Drive, com SHA-256 e tamanho validados pelos parâmetros fixados no PRE104.
- Busca limitada a membros binários candidatos de até 80 MiB, orçamento total de 256 MiB, recusa nomes classificados como sensíveis pelo PRE104. Não extrai árvore do jogo, não modifica guest, save ou APK.
- Resultado proposto: `/tmp/nfsmw-pre327/NFSMW_PRE327_NITRO_BINARY_XREFS.json` em artifact `nfsmw-pre327-nitro-binary-xrefs-<run_id>`. **Run ID, status interno, conteúdo de relatório e eventual match ainda não verificados.**

## Interpretação conservadora
- Match de quatro bytes pode ser dado aleatório, não uma entrada de vtable validada.
- Nenhum match não exclui ponteiros codificados, relocados, trampolins ou dispatch indireto.
- Nenhum resultado isolado identifica o carro do jogador.
- Nitro infinito, Speedbreaker infinito e dinheiro ilimitado continuam desativados na V41. Não existe V42 aprovada nesta etapa.
- Preserve V41, pacote `io.github.nfsmwrecomp`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, save MARCEK, controles e gráficos.

## Próxima ação
Conferir logs/artifacts das runs PRE325/PRE325B/PRE326/PRE327. Se existir hit binário, primeiro verificar o formato da seção e a origem do ponteiro antes de atribuir semântica. Para validar owner ainda será necessária evidência runtime de qual carro controla o medidor; não habilitar cheat sem essa prova.
