# NFSMW — PRE448 ARM64 PASS e PRE452 V48 diagnóstica iniciada (8 nov 2026)

## Estado de referência
- **V46 PRE401** mantém Nitro infinito global, comprovado pelo usuário em gameplay (PRE407). Não substituir APK funcional nem modificar save `MARCEK`.
- **V47 PRE434** (versionCode 47, pacote `io.github.nfsmwrecomp`) assinada com certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. APK SHA256 `ce2de9311b80670f7f4700e426ad1a77d6cd87a836df5ae3b36d4ec872cc7461`. Sessões reais S24 FE confirmaram BMW `type=41` com contagens candidatas `0,0,0,3,0,0,0` e Fiat Punto `type=74` com `4,4,3,3,3,4,3` em Motor, Transmissão, Suspensão, Nitro, Pneus, Freios e Indução. Não são peças compráveis comprovadas.
- **PRE446** confirmou três caminhos para zero na consulta `sub_823E5988`. **PRE447** aprovou dry-run reversível do logger de rotas sob `NFSMW_PRE447_LOOKUP_ROUTE_ENABLE`; não prova qual rota de fato foi executada pela BMW.

## PRE448 — resultado final verificado
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42496806174 — `completed/success`, atualizada em 2026-11-08 16:10:52 UTC.
- Log conclusivo `PRE448_STATUS AUDIT_OK`, `PRE448_PHASE PRE448_NATIVE_VALIDATED`, `PRE448_CMAKE_CONFIG True`, `PRE448_NATIVE_LINK True`, `PRE448_ELF_ARM64 True`, `PRE448_ALL_MARKERS True`.
- Exportações nativas ELF: `NFSMW_PRE429_TRACE_ENTRY:1`, `NFSMW_PRE429_TRACE_LEVEL:1`, `NFSMW_PRE447_ROUTE:1`.
- A biblioteca `libmain.so` real foi compilada em runner ARM64 Android NDK a partir de backup PRE99 verificado com cadeia fonte equivalente V47; includes Nitro PRE398, suporte BMW PRE305 e dois hooks PRE429. Novo hook PRE447 usa a chamada original e registra `caller`, `category`, `reason` (1=descritor não encontrado, 2=valor do atributo, 3=fallback), `candidate_count`, sem novas chamadas ou leituras/escritas de memória guest; a categoria real de cada carro vem de sessão identificada externamente.
- **Importante:** PRE448 NÃO compila APK, NÃO assina, NÃO toca no save, NÃO testa o jogo no S24 FE e NÃO corrige a tunagem. CMake/ELF PASS não comprova que o callback de rota será acionado na V48.

## PRE452 — tentativa de V48 diagnóstica, NÃO DECLARAR PRONTA
- Script: `automation/kaggle/pre452_build_signed_v48_bmw_zero_route_diag.py`.
- Workflow: `.github/workflows/nfsmw-pre452-v48-bmw-zero-route-signed.yml`.
- Run: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42498853924 — **em andamento na consulta inicial**, sem conclusão de APK, assinatura, Drive ou teste no aparelho.
- Nova APK planejada `NFSMW_V48_PRE452_BMW_ZERO_ROUTE_DIAGNOSTIC.apk`, `versionCode=48`, pacote inalterado `io.github.nfsmwrecomp`, certificado permanente inalterado obrigatório. Preserva todo o workflow da PRE434/V47 e adiciona somente logger PRE447: marker `NFSMW_PRE447_ROUTE` de eventos de retorno junto aos dois PRE429 e PRE398 Nitro; lança erro se a APK não tiver os três símbolos únicos ou assinatura verificada.
- A V48 **não** gera upgrades, não troca contagem zero por quatro, não modifica atributos, física, compras ou saves. Teste de BMW/Punto só após resultado final, relatório e APK do Drive conferidos. Nunca desinstalar V47 para atualizar nem modificar private signer. Fazer backup do save `MARCEK` antes de instalar.

## Próximo passo
1. Consultar resultado final PRE452 via GitHub Actions, depois os logs do job, relatório, SHA256, versionCode, assinatura permanente, `libmain.so` e id da APK no Drive; não inferir por `success` isolado.
2. Somente se APK aprovada, testar BMW e Punto em processos separados, abrindo as sete categorias sem comprar upgrades, e buscar `NFSMW_PRE447_ROUTE` com `reason=1/2/3`.
3. Guardar logs e atualizar o contexto canônico com novo backup, sem publicar logs privados/saves. Preservar V46/V47/V48, shaders/efeitos, controle PG-9076, 1920×1080, física e limites térmicos. Não declarar ganho de FPS ou correção de tunagem.
