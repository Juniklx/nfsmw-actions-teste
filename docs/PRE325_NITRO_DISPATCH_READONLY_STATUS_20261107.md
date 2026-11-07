# PRE325 — Nitro dispatch extended read-only audit (2026-11-07)

## Estado observado
- Script: `automation/kaggle/pre325_nitro_dispatch_extended_readonly.py`
- Workflow: `.github/workflows/nfsmw-pre325-nitro-dispatch-extended-readonly.yml`
- Trigger: `automation/kaggle/pre325_requests/launch_20261107.json`
- Commit de trigger: `2b0ecbb6f66cfb8c0ed40b087b0a41e86440385a`
- Endereço PAL: `sub_82424AF0`, hex `0x82424AF0`, decimal `2185382640`.
- Run ID, logs e artefato PRE325: **ainda não verificados** neste registro.
- Este workflow roda em GitHub Actions; a localização do script em `automation/kaggle` não significa execução no Kaggle.

## Escopo
- Download do PRE99 do Google Drive com credenciais existentes no runner e verificação de SHA-256 e tamanho fixados no PRE104.
- Varredura somente de leitura dos shards PAL C++ e fontes de código para referências textuais ao símbolo e ao endereço.
- Relatório limitado em `/tmp/nfsmw-pre325/NFSMW_PRE325_NITRO_DISPATCH.json` e artifact do Actions.
- Não gera APK, não altera guest, save MARCEK, controles, gráficos, configuração térmica ou certificado.

## Critério de interpretação
- Referência textual não prova caller real, vtable ou identidade do veículo.
- Ausência de referência não exclui dispatch indireto.
- `owner_verified=false` e `indirect_dispatch_verified=false` permanecem até prova positiva independente.
- PRE323 confirmou `r31.u64=ctx.r3.u64`, mas não que o objeto seja o carro do jogador.
- PRE321 confirmou ciclo de consumo e recarga do Nitro em V41, não cheat infinito.
- Não habilitar patch de consumo sem identificar owner e sem OFF=original, opt-in e fail-closed.

## Próxima decisão técnica automática
1. Consultar run PRE325, status interno e artifact JSON, não só status verde.
2. Se auditoria falhar, corrigir erro demonstrado sem repetir patch no código do jogo.
3. Se passar, interpretar matches e verificar se há prova suficiente de owner. Caso contrário, preparar rastreamento runtime limitado e reversível do objeto e comparação com carro do jogador.
4. Preservar V41 assinada e certificado permanente. Nenhuma V42 nesta etapa.

## PRE325C — Correção verificada do predicado textual (2026-11-07)
- Foi identificado falso positivo reproduzível na expressão `sub_82424AF0`: ela também encontrava o identificador mais longo `sub_82424AF01`.
- Correção mínima: `\\bsub_82424AF0\\b`, sem alterar o jogo. Verificação local com sete casos de teste (7/7 aprovados), incluindo correspondência positiva ao endereço hex/decimal e rejeição de identificador maior.
- Commit da correção: `db72732d4554ee60ad55982221fbeeb6bacdbdfc`.
- Arquivo de novo disparo: `automation/kaggle/pre325_requests/launch_corrected_regex_20261107.json`, commit `f0476b80e9f6b09e518d5a43e865b6863f6bfeb0`.
- O workflow PRE325B foi configurado para reexecutar quando o script PRE325 muda; **execução/resultados do GitHub Actions ainda não verificados**.
- Resultado de auditoria do PRE99, localização de caller/owner, consumo em player vs AI e V42 continuam **pendentes**. Nenhum patch Nitro, assinatura ou APK nesta correção.
