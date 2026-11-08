# PRE398–PRE401 — Nova decisão: Nitro infinito global em todos os carros (2026-11-07)

## Mudança de requisito confirmada pelo usuário
O usuário declarou explicitamente: **não se importa se todos os carros tiverem Nitro infinito**. Portanto o requisito antigo de exclusividade player-only foi removido para **Nitro**. Isso não autoriza automaticamente Speedbreaker infinito, dinheiro ilimitado, alterações na física, gráficos ou mecanismos térmicos.

## Estratégia técnica
- Base V45 PRE390 assinada com chave permanente; build isolada recriada a partir de PRE99 autenticado.
- A rotina Nitro `sub_82424AF0` escreve `r31+252` em cinco sites, confirmados por PRE242/PRE334/PRE392.
- Novo estágio `automation/kaggle/pre398_global_nitro_full_staging.py`: substitui nos **cinco sites apenas** o valor gravado `temp.u32` por literal `0x3F800000u` (float32 1,0), sem modificar endereço ou quantidade de stores, sem guest loads extras e sem filtro por slot, LR ou owner. Também atualiza o valor enviado à telemetria PRE247 para refletir os bits efetivamente gravados.
- Registro único `NFSMW_PRE398_GLOBAL_NITRO_FULL` no callback nativo existente, preservando PRE316/PRE336/PRE348/PRE383.
- Trata-se de **modificação ativa do comportamento do jogo**, não diagnóstico puramente passivo. Ela se aplica a quaisquer veículos cuja gravação de Nitro percorra esses cinco pontos, potencialmente jogador e IA. Não há prova runtime de Nitro infinito ainda.
- Staging reversível com backups de ambas as fontes isoladas; rejeita reaplicação, mudanças de outros stores e estrutura inesperada.

## Auditoria verificada PRE399
- GitHub Actions run `42439120243` [abrir](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42439120243), `completed/success`, artifact `13601200565`.
- Relatório `PRE399_GLOBAL_NITRO_SOURCE_CANARY.json`: `status=AUDIT_OK`, PRE99 SHA `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`, shard SHA `eec9b82e51bbfcb573cd0f965e3ed7639bbbd291b285f9fc6d5a7d1e77cd735f`.
- Exatamente cinco sites substituíveis, reversão exata PAL e callback, 0 stores alheios modificados, 0 extra LOAD/STORE guest. Prova **fonte somente**, não build/execução.

## PRE401 — V46 experimental
- Builder `automation/kaggle/pre401_build_signed_v46_global_nitro_full.py`, workflow `.github/workflows/nfsmw-pre401-v46-global-nitro-all-cars.yml`.
- `versionCode 46`, pacote `io.github.nfsmwrecomp`, APK alvo `NFSMW_V46_PRE401_GLOBAL_NITRO_FULL_ALL_CARS.apk`.
- Run [42439306990](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42439306990) iniciada, **em compilação quando este relatório foi preparado**; não promover APK a release validada sem gates de Gradle, ARM64 `libmain.so`, marcadores PRE398/PRE383/PRE348/PRE336/PRE316, certificado v2 original e upload/readback no Drive.
- Certificado permanente deve continuar SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; não recriar chave, não expor credenciais; preservar V45 e save `MARCEK`, controles PG-9076/touch, 1920x1080, shaders, efeitos, física e proteção térmica.
- **Status de jogo:** Nitro infinito global ainda não comprovado até teste real no Galaxy S24 FE. Não afirmar melhora FPS.

## Próximo teste após validação de release
Backup independente do `MARCEK` e instalar V46 sobre V45 sem desinstalar. Em exploração livre, usar Nitro prolongadamente e verificar se o medidor permanece 100%; depois corrida com IA e observar se o comportamento também ocorre sem crashes ou alterações inesperadas. Analisar `nfsmw.log` com marcador PRE398 e saídas PRE348. Se houver regressão, retornar à V45 e preservar logs.
