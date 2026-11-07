# NFSMW Android — PRE284: fontes completas V37 + módulo nativo PRE283 compilável em host (2026-11-07)

## Resumo verificável
- **PRE284 retry1 concluída com sucesso** no GitHub Actions run `42330124913`: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42330124913, com `PRE284_STATUS AUDIT_OK`.
- A primeira tentativa `42329949083` falhou (`ValueError`, não incluiu mensagem detalhada no primeiro relatório). Corrigida a verificação de destino criado pela PRE131, que não deve exigir que todos os arquivos gerados preexistam no PRE99; hashes dos arquivos produzidos continuam exigidos. A segunda execução aprovada confirma o fluxo após a correção; não afirmar causa inequívoca do primeiro ValueError.
- Código reproduzível: `automation/kaggle/pre284_v37_full_passive_vtable_link_preflight.py`; workflow `.github/workflows/nfsmw-pre284-v37-source-native-preflight.yml`.
- Backup PRE99 **autenticado**, SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`. Restore em diretório temporário do GitHub Actions; nenhuma fonte permanente atualizada.

## V37 reconstruída como FONTES, não APK
Ordem reproduzida do script de build V37 `pre246_build_signed_v37_passive_money_trace.py`:
1. PRE117 e PRE128, UI/touch em `settings_overlay.cpp`, ambos com SHA-pins.
2. PRE131: 5 arquivos de modernização da UI/touch, com SHAs individuais, inclusive um header gerado.
3. PRE133: ponte SDL mouse/swipe, resultado confirmado por hash.
4. PRE157 callback, PRE165 SDL wake, PRE170 input pump (cpp+header).
5. PRE180 patch do SDL3 `SDL_events.c`, SHA de saída `bdd3200a44e055168e5092cec7f5adbf5f24cabe7af0b629fceec866f567cb33`.
6. PRE194: guard/diagnóstico C3 na fonte PAL, SHA `a01f25e531af783d37f70a3c3caa0f3e7a979d2bdbdd923abf7b2c6062d29d1e`.
7. PRE246: 8 sondas passivas de dinheiro; PRE247: total de 16 sites (8 dinheiro + 8 nitro/Speedbreaker).
- Resultado: hashes/exigências de todos os pontos acima validados e reaplicados **somente na árvore temporária**. Não foi recuperado o pacote APK V37 nem construído substituto; o fato de a cadeia de fonte passar não comprova execução no S24 FE.

## PRE283 integrando um registrador virtual em CMake (somente diagnóstico)
- Shard de origem `workspace/nativo/app/generated/default/nfsmw_recomp.11.cpp`, SHA base `0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3`, após inserção pontual `1ce6208a0848955df6e918e7d56a28616afbf822e5a05b9747e4300e37bbaba9`, byte-reversível.
- O callback nativo `NFSMW_PRE283_VTABLE_TARGET_TRACE` recebe o `ctr.u32` já calculado no ponto guest `0x825837D4` de `sub_82582F70`, sem alterar chamadas guest nem acrescentar `REX_LOAD/STORE`. O destino real da vtable+12 **não foi medido**.
- C++ temporário `nativo/app/src/nfsmw_cheats_trace_pre284.cpp`, SHA256 `5114d0835ab15fbc99f424185c77fc369f563bf69dccdf7a6c8e1e894c5ca11f`. Registro único em `nativo/app/CMakeLists.txt` após PRE246 e PRE247; CMake SHA256 `16a9e687a3e264ef791bfddc96ff855d599b316ce8c1aceaffb6e9f3dba3023a`.
- A macro `NFSMW_PRE283_VTABLE_TARGET_TRACE_ENABLE` **não** foi definida/ativada no código gerado. Não ativados os patches PRE264 (menu BMW por tipo, escopo de propriedade incompleto) nem PRE281 (proteção de header, método virtual ainda não identificado conclusivamente).
- Teste isolado host: módulo nativo **original** compilou e vinculou em executável de teste com declaração `extern "C"` e símbolo não decorado identificado por `nm`. **200 eventos simulados, somente 12 logs**, `PRE284_NATIVE_LINK_200_EVENTS_12_LOGS_PASS`. Para esse teste de ligação, `rex/logging/macros.h` foi substituído por um shim que contabiliza chamadas, logo isto NÃO é ligação ao sistema real Android.
- Verificação adicional independente: `c++ -fsyntax-only` do módulo **com cabeçalho real** `rex/logging/macros.h` e includes do SDK restaurado: `passed=true`. É compilador host, **não** Clang NDK ARM64 ou compilação inteira do `libmain.so`.

## Relatórios
- Relatório PRE284, ZIP JSON técnico, arquivado no Drive, sem save pessoal ou credenciais: https://drive.google.com/file/d/1tM9ftVVDj4j4ouXPIsVYsb0nxtOS9kYm/view
- GitHub Actions run aprovado: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42330124913
- GitHub Actions inicial falhou: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42329949083 (não tratar como resultado final).

## Estado e próximos passos seguros
1. **PRE285:** validar com o Android NDK ARM64 a compilação do módulo de logging real, a compilação do shard PAL protegido por macro e o vínculo CMake no alvo `nfsmw`, ainda em árvore temporária, **sem assinatura**. Só depois decidir se deve construir **V38 exclusivamente diagnóstica** para medir o endereço da vtable a partir do **Fiat Punto**, usando a mesma assinatura permanente de V37.
2. Nunca desbloquear `HeroCar` globalmente: a PRE264 trabalha por tipo `41`, ainda não distingue BMW de carreira/propriedade, e não cria pacotes de desempenho. Zero pacotes e `GetSelectedPart()==nullptr` exigem tratamento adequado. `GetMaxLevel` tem efeitos guest; não invocar sete vezes artificialmente.
3. APK V37 permanece a última testada. Usuário confirmou BMW normal inserida via save PRE260, dirigível no perfil `MARCEK`, mas oficina só exibe `Visual`. Fi̇at Punto, fichas Junkman e outros saves devem ser preservados. Nenhum teste de BMW/tuning realizado nesta PRE284.
4. Qualquer V38 futura: `versionCode>=38`, mesmo package `io.github.nfsmwrecomp`, **mesmo certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`**, sem recriar chave, sem debug e sem solicitar ou expor senhas. Preservar SDL/touch/PG-9076, FPS cap atual, 1920×1080, gráficos/física/efeitos, C3 e limiares térmicos.
5. `CONTEXTO_NFSMW.md` canônico no Drive está defasado (última seção lida PRE237); **não sobrescrever** documento extenso com resumo. Consolidar este adendo e PRE238–284 com **backup integral, identificação da versão remota e reconciliação**.

## Resultado inequívoco
- PRE284: **replay de fontes V37, CMake registration, ABI host compile/link e sintaxe do SDK host aprovados**.
- Android ARM64 NDK, APK V38, assinatura, instalação, menu BMW e valores reais dos upgrades: **não realizados/comprovados**.
- Nenhuma fonte persistente do jogo, save pessoal, material de assinatura, APK V37 ou chaves foi alterado/acessado.
