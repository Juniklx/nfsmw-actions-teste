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

## Resultado confirmado por log e artefato GitHub — PRE325 revisada
- Run `42407721044` / job `128508932656`: `completed/success`; log `PRE325_STATUS AUDIT_OK`, `PRE325_PAL_SHARDS 129`, `PRE325_MATCHES 5`, `PRE325_OWNER_VERIFIED False`.
- PRE99 SHA-256 autenticado; 129 shards PAL gerados e 11.126 outros arquivos-fonte examinados. Artefato `13588336479` baixado e JSON aberto.
- As **cinco** referências textuais são: 
  1. `workspace/nativo/app/generated/default/nfsmw_funcs.h:30869` — `DECLARE_REX_FUNC(sub_82424AF0);` (declaração);
  2. `workspace/nativo/app/generated/default/nfsmw_init.cpp:30887` — `{ 0x82424AF0, sub_82424AF0 },` (tabela de inicialização);
  3. `workspace/nativo/app/generated/default/nfsmw_recomp.66.cpp:16124` — `DEFINE_REX_FUNC(sub_82424AF0) {` (definição PAL);
  4. `workspace/nativo/app/generated/default/nfsmw_register.cpp:30869` — `registrar->SetFunction(0x82424AF0, sub_82424AF0);` (registro runtime);
  5. `workspace/nativo/app_usa/generated/default/nfsmw_recomp.66.cpp:16351` — `ctx.lr = 0x82424AF0;` numa sequência `REX_CALL_INDIRECT_FUNC(ctr.u32)` **da edição USA**, contexto `sub_82424988`. O endereço é valor de link/retorno do callsite USA, não prova de invocação da rotina PAL.
- Nenhuma referência constitui **named direct caller PAL**. A tabela `nfsmw_init.cpp` é mecanismo de registro, não objeto do jogador. O alvo permanece `sub_82424AF0`; owner permanece desconhecido.
- PRE327 run `42407723203` também terminou com AUDIT_OK, mas seu único binário candidato foi `sdk/thirdparty/sdl3/test/moose.dat`, tornando-o inconclusivo para dados de vtable do jogo. Não insistir em varredura binária indiscriminada.
- Mantenha a PRE321 V41 como evidência runtime dos stores +252. Próximo trabalho justificável: acessar `nfsmw.log` V41 original para correlacionar endereços PRE247 e definir instrumentação passiva contextual de owner, sem habilitar cheat antes da validação.
