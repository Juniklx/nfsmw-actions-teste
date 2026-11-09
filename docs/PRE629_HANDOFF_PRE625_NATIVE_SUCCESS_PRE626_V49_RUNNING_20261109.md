# PRE629 — PRE625 ARM64 aprovado; PRE626 V49 diagnóstica disparada e compilando (2026-11-09)

## Resultado fechado da PRE625

- [GitHub Actions 42705397176](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42705397176) terminou `success`, relatório `docs/PRE625_BMW_HOST_ATTR_ARM64_NATIVE_LINK_RESULT.json` com `status=AUDIT_OK`. Este é um **teste de link ARM64 sem APK**, não instalação/execução.
- Backup PRE99 autenticado SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39` reconstituído em diretório temporário, com cadeia PRE429+PRE447 e o logger adicional PRE622.
- `native_cmake_ok=true`, `native_build_ok=true`, `native_arm64_elf=true`; `libmain.so` experimental SHA256 **`73c631fb28722ad2716147249f92aaab621f5c62f5720624ba5f11bf86335652`**.
- Exatamente **1 exportação** da nova função `NFSMW_PRE622_ATTR_VALUE` no ELF ARM64; as outras três exportações `NFSMW_PRE429_TRACE_ENTRY`, `NFSMW_PRE429_TRACE_LEVEL`, `NFSMW_PRE447_ROUTE` verificadas como preservadas; host módulo compilado uma vez e registro CMake único.
- O callback recebe dados já calculados da leitura `ctx.r3.u64 = REX_LOAD_U32(ctx.r11.u32 + 0)` do guest original, limita a 128 registros, não dereferencia ponteiro guest, não acrescenta load/store/call guest e possui transformação da fonte reversível.
- `APK_built=false`, `signed=false`, `signing_material_accessed=false`, `guest_runtime_executed=false`, `game_assets_modified=false`, `save_modified=false`, `tuning_enabled=false`.
- A primeira tentativa PRE625 [42705158328](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42705158328) falhou **antes** de compilar a biblioteca por sobrescrita acidental de símbolo de módulo Python com um dicionário `p622` (`AttributeError: 'dict' object has no attribute 'SYMBOL'`). O segundo gatilho, após corrigir sombreamento, passou. Não contar a primeira falha como falha do jogo ou APK.

## PRE626 — V49 em compilação protegida, status ainda não final

- A receita `automation/kaggle/pre626_build_signed_v49_bmw_attr_diag.py` e workflow `.github/workflows/nfsmw-pre626-v49-bmw-attr-signed.yml` foram revisados para aplicar a PRE622 como **quarta telemetria** sobre PRE452/V48, mantendo os diagnósticos anteriores, Nitro PRE398, touch/PG9076 e ajustes existentes, sem adulterar as contagens de desempenho da BMW.
- Gatilho `automation/kaggle/pre626_requests/launch_v49_bmw_resolved_attr_diag_20261109.json`; [execução **42709319413**](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42709319413), iniciada às 22:09:49Z. **No momento de registrar esta seção, o workflow estava em `in_progress`, na etapa `Build V49 passive BMW attribute diagnostic, preserve Nitro and permanent certificate`.** Não declarar sucesso, falha, assinatura ou upload até reconsultar essa execução.
- Gates já concluídos no workflow: compilação dos scripts Python; validação PRE625 obrigatória; canários de macro BMW e Nitro; testes das pontes de controle, indicadores e regressões de instrumentação; preparação NDK/CMake/SDK e caches.
- Destino pretendido, se todos os gates finais passarem: `NFSMW_V49_PRE626_BMW_ATTRIBUTE_VALUE_DIAGNOSTIC.apk`, **`versionCode=49`**, pacote `io.github.nfsmwrecomp`, mesma assinatura permanente (cert SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`). Verificações de release exigidas incluem `apksigner`, certificado DER v2, `aapt` e `libmain.so` com `PRE429_ENTRY`, `PRE429_LEVEL`, `PRE447_ROUTE`, `PRE622_ATTR_VALUE`, `PRE398_GLOBAL_NITRO_FULL`. Nunca usar debug signer, gerar nova chave ou expor credenciais.
- Nenhum resultado de build V49, SHA de APK ou ID de Drive autenticado está disponível **neste checkpoint**. `--upload` é requerido, mas **publicação só é declarada após relatório de verificação**, e eventual falha de upload não implica necessariamente falha de compilação.

## Estado do jogo e próximo passo

- **Dispositivo permanece conforme último teste informado:** Galaxy S24 FE com V48 PRE452 instalada e funcionando; arquivos PRE607 ativos verificados pelo usuário com hashes `f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2` (ZDIR) e `1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146` (ZZDATA4), perfil `NAME` com BMW já importada. Seis consultas (Motor, Transmissão, Suspensão, Pneus, Freios, Indução) retornam **0**, Nitro **3**. A UI mostra `Option Title` nas seis categorias, segundo relato e log PRE617.
- **Nenhum APK novo instalado ou testado no Galaxy**, nenhum ganho de FPS ou correção de tunagem comprovado; V48 continua referência. O usuário não precisa mexer no telefone enquanto a PRE626 não concluir assinatura/certificado e upload.
- Se PRE626 for validada, analisar relatório/símbolos/cert/versão/Drive antes de oferecer download. O teste de usuário futuro deve comparar categoria e valor da `[NFSMW_PRE622_ATTR_VALUE]` contra a trilha antiga `[NFSMW_PRE447_ROUTE]`, especialmente BMW versus Punto. A V49 é **diagnóstica**, não cria peças reais nem altera preços, instalação, física ou saves.
- Se PRE626 falhar, ler primeiro relatório e jobs da execução, corrigir a fase específica sem sobrescrever APKs ou fontes existentes.
- Preservar 1920×1080, meta 120 FPS (V48 cap 60 em log), shaders/efeitos/texturas/física, controle físico iPega PG-9076/touch, Nitro e proteções térmicas. Não limpar saves nem alterar chaves.
