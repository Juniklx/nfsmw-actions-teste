# NFSMW Android — PRE282/PRE283: integração descartável das guardas da BMW e diagnóstico passivo da vtable (2026-11-07)

## Referência de execução do aparelho
- Usuário confirmou em V37 Android `io.github.nfsmwrecomp`, perfil MARCEK, que a **BMW M3 GTR normal** criada por edição do save PRE260 está presente na garagem, selecionável e **dirigível**. No tuning, só aparece `Visual`; não aparecem `Peças` e `Desempenho`.
- Preservar Fiat Punto, fichas Junkman e outras partidas. BMW do prólogo (`M3GTRCAREERSTART`) e narrativa Razor não alterados.
- PRE261–281: `IsHeroCar` classifica tipo 41 BMW M3 GTR e oculta menu; o builder `GetPerformancePartsList` usa `GetMaxLevel`, que manipula referências em estruturas guest, logo não é seguro injetar sete consultas adicionais; a candidata a `RefreshHeader` `sub_82582A40` acessa o ponteiro selecionado sem guarda antes de `PreviewPerfPkg`. A vtable +12 usada por `sub_82582F70` é conhecida, **mas ainda não existe prova binária de que aponta a `sub_82582A40`**.

## PRE282 — execução e verificação de integração de somente fonte
- GitHub Actions **success**, run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42329075877; log `PRE282_STATUS AUDIT_OK`, `PRE282_V37_PASSIVE_SITES 16`, `PRE282_RELEASE_APPROVED False`.
- Script `automation/kaggle/pre282_bmw_v37_disposable_dual_guard_preflight.py`, workflow `.github/workflows/nfsmw-pre282-bmw-v37-dual-guard-disposable.yml`. PRE99 SHA256 autenticado `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`, restauração em diretório descartável do runner.
- Após sondas passivas V37 PRE246/PRE247 (8 pontos dinheiro + 8 pontos de recursos = **16 sites** em C++ gerado PAL), duas alterações experimentais foram colocadas em shards distintos, **ambas desativadas por macro**:
  - PRE264 `sub_82578988`, arquivo `nfsmw_recomp.5.cpp`, SHA256 original `26c58fa8c5b5810f2fa06bcf25d3f3f7ac131bf73692a9991a84269433b8de07`, SHA256 ensaio `1dc5745263d68e186e66545f8795b2a11fffc8d5011aec74f3ce8a9256afe11c`, macro `NFSMW_PRE264_BMW_MENU_ENABLE`. **Este patch identifica BMW por tipo 41, ainda NÃO limita a uma BMW da garagem/carreira**; não habilitar até resolver esse escopo.
  - PRE281 `sub_82582A40`, arquivo `nfsmw_recomp.83.cpp`, SHA256 original `21e561eeae953888b7d645719dc6bd7077dfa040f3f06896b7bbe3ba3e7774d4`, SHA256 ensaio `b71f40a1fd1770fba249192ef03c78a641f575e8a6bca9511efedf75dad54a7e`, macro `NFSMW_PRE281_BMW_EMPTY_HEADER_GUARD_ENABLE`. Desvia à saída comum se `GetSelectedPart` retornar ponteiro zero; **função real de vtable ainda não está provada**.
- Verificação byte a byte de reversão exata, igual número de chamadas e `REX_LOAD/STORE`, e quatro testes fail-closed **todos verdadeiros**: rejeitar aplicação duplicada e SHA inesperado para cada alteração. Fonte original não alterada.
- Limitação: **somente camada de fontes recompiladas com sondas V37**, sem restaurar/verificar toda a integração Android/SDL/touch/PG9076/C3; **não foi compilado C++ nativo nem APK**, nada assinado ou instalado. Mock não comprova funcionamento da BMW. `release_approved=false`.
- Arquivo de metadados no Drive: https://drive.google.com/file/d/1u0seRk8i65z1zFTKxpRRdp35Zr4kANiI/view

## PRE283 — identificar em runtime o destino da chamada virtual sem desbloquear BMW
- GitHub Actions **success**, run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42329366778; log `PRE283_STATUS AUDIT_OK`, `PRE283_REVERSED True`, `PRE283_ACTUAL_TARGET_KNOWN False`.
- Script `automation/kaggle/pre283_bmw_vtable_target_passive_dryrun.py`; workflow `.github/workflows/nfsmw-pre283-bmw-vtable-target-passive-dryrun.yml`. No arquivo `nfsmw_recomp.11.cpp` PAL autenticado SHA256 `0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3`, a função `sub_82582F70` chama vtable **+12** via `ctr.u32` em guest PC `0x825837D4` (LR para `0x825837D8`).
- A PRE283 propõe callback de log `NFSMW_PRE283_VTABLE_TARGET_TRACE(ctr.u32,r29.u32,0x825837D4)` **antes** da chamada virtual existente, sem alterar seu alvo, sem novas leituras/gravações guest. A macro `NFSMW_PRE283_VTABLE_TARGET_TRACE_ENABLE` está **OFF por padrão**. SHA256 da fonte ensaiada somente em memória `1ce6208a0848955df6e918e7d56a28616afbf822e5a05b9747e4300e37bbaba9`.
- Protótipo C++ de logger native limitado a **12 mensagens no máximo** por processo; MOCK host C++ passou **200 casos** com limite 12. **Nem o logger real foi compilado/linkado, nem o jogo gerou logs PRE283.** Artefato JSON no Drive https://drive.google.com/file/d/1N3zkiWwCXWhBeU_URw2oaQUAZ7bxWiwL/view .
- **Possível teste futuro menos arriscado:** uma V38 estritamente diagnóstica, se construída com mesma assinatura e somente sonda PRE283 habilitada, pode pedir ao usuário para entrar em **Desempenho do Fiat Punto**, que usa a mesma classe de tela; isso tende a disparar `sub_82582F70` sem abrir categorias bloqueadas da BMW. Correlacionar endereço `ctr.u32` com candidatos como `sub_82582A40`. Pode ser thunk; nesse caso precisa resolver próximo salto. Nada disso foi testado ainda.
- Não confundir a captura do método virtual com informação sobre `GetMaxLevel` da BMW. Os valores reais dos sete upgrades continuam desconhecidos.

## Próximo passo recomendado
1. **PRE284**: validar em árvore de build descartável a instrumentação PRE283 com as fontes V37 completas e verificar que o logger é vinculável, com captura limitada; se for construir V38 diagnóstica depois, garantir `versionCode>=38`, package `io.github.nfsmwrecomp`, **certificado permanente idêntico** SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Não criar chaves, não pedir senha nem usar debug.
2. Não habilitar PRE264/281 ainda: vtable real não resolvida, filtro BMW carreira não implementado e UI de lista vazia ainda não validada.
3. Manter intactos V37, saves MARCEK e demais, Fiat Punto, BMW M3 GTR, vouchers Junkman, controle PG-9076, 1920×1080, limite de FPS atual, gráficos, física e proteção térmica; nenhuma alegação de ganho FPS ou Razor vencido.
4. Histórico canônico `CONTEXTO_NFSMW.md` do Drive ainda termina em PRE237 apesar de ter ~567 KB em última leitura (atualização 2026-11-06). Este arquivo é **adendo GitHub**, não substituição. Para consolidar PRE238–283 no Drive, fazer backup íntegro, confirmar a versão remota e conciliar todos os adendos antes de qualquer escrita.

## Estado final verificável
- PRE282/283: **GitHub Actions success, testes estáticos/sintéticos confirmados**.
- APK V38: **não compilada, assinada nem instalada**.
- Destino virtual `RefreshHeader` e níveis de upgrades reais: **não medidos**.
- Saves e V37: **não modificados por estas etapas**.
