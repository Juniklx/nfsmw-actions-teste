# PRE694 — RADV B: captura real e comparação com Samsung A1 (11/11/2026)

## Evidência e integridade

- Arquivo do usuário: `nfsmw2.zip`, 320,818 bytes, SHA-256 `08a34d1f844125f8aa17ca4a97b20d7cbbbd9007217def8d9c6c7577947903c4`, CRC ZIP **PASS**. Possui cinco entradas: `nfsmw.log`, status de captura, timestamps ordenados, manifesto e validação. Os hashes do arquivo de validação coincidem com os bytes extraídos.
- Fase rotulada `RADV_B`, dispositivo `SM-S721B`, pacote `io.github.nfsmwrecomp`, versionCode 51 comprovado no preflight do coletor; **o rótulo sozinho não prova driver**.
- **Log confirma** `Vulkan: driver propio cargado con adrenotools: .../vulkan.radeon.so`, `driverName: radv`, `driverInfo: Mesa 27.0.0-devel (git-269238e853)`; Vulkan 1920×1080, swapchain MAILBOX, cap 60 FPS.
- Há uma inicialização no log: 2026-11-11T14:45:30.676000 a 2026-11-11T14:53:20.057000 (durou 469.381s = 7m49s aproximadamente). O log termina sem mensagem explícita de encerramento; não atribuir crash ou fechamento.
- Coleta 14:46:52–14:47:31, 30/30 consultas com dados, uma SurfaceView NFSMW ativa avançando, refresco 120 Hz (8333333 ns). 

## Comparação real com A1, mesmo método de processamento

| Métrica | Samsung A1 | RADV B |
|---|---:|---:|
| FPS médio estimado, apenas trechos contínuos | 59.998 | 59.988 |
| Apresentações únicas | 2329 | 2319 |
| Intervalos contínuos | 2327 | 2317 |
| Intervalo médio `actualPresent` | 16.667141ms | 16.669922ms |
| Desvio-padrão dos intervalos | 3.846875ms | 3.737703ms |
| Buckets de 8–9ms | 242 | 214 |
| Bucket 25ms | 238 | 195 |
| Alternâncias 8↔25ms | 278 | 216 |
| Intervalos arredondados ≥33ms | 2 | 7 |
| Watchdog 5s/20s no registro | 0 | 0 |

- Na fase B, desvio-padrão 2.84% inferior e alternâncias 8↔25ms 22.30% inferiores comparadas com A1. **Observação, não ganho causal**. A2 ainda falta e condições térmicas/cena não foram verificadas como equivalentes.
- Contudo, a B teve mais intervalos longos: **7** arredondados ≥33ms contra **2** na A1, incluindo quatro de 42–50ms (B). Isso desaconselha conclusão global de que o RADV é sempre mais suave.
- B: 3650 linhas de timestamp válidas em snapshots, 2319 apresentações únicas, 1331 consultas duplicadas excluídas. Sem timestamps conflitantes. Uma lacuna de **1092.327ms** foi excluída dos intervalos contínuos por incerteza de cobertura (não prova travamento). O histograma efetivo arredondado é `{'8': 204, '9': 10, '16': 78, '17': 1823, '25': 195, '33': 3, '42': 3, '50': 1}`.
- `actualPresent` mede carimbo do SurfaceFlinger, não sensor óptico, latência de controle nem apresentação percebida pelo olho.

## C3, watchdog e motor interno

- **0 marcadores `[vigilante]`** na sessão B de 469.381s. A sessão RADV anterior da PRE692 teve sete episódios; portanto **os congelamentos prolongados não foram reproduzidos nesta execução**, não podendo ser atribuídos de forma exclusiva ou determinística ao RADV.
- Às **14:45:53.854** o PRE635 C3 reportou `indice=0`, `en_vuelo=1`, `frame=textura_frame=1230`, `epoca_ahora=epoca_primera=1230`, `offset_primera=0`, `offset_segunda=51872`, `mismos_comandos=true`, `subir=true`, `trabajo_huella=0`, `datos_bytes=43648`. O guard PRE194 confirmou `copia_duplicada=true` e acionou fallback, como também ocorreu no Samsung A1 e PRE693. Não remover a proteção.
- Foram 23 janelas C2, **27,477 intervalos internos**, dos quais 26,688 caíram entre 15–18ms. A captura SF só contém 39s; não tomar histogramas C2 de toda a sessão como se fossem histogramas SF.
- C2 marcou `GPU real por Swap 8.97 ms` às 14:47:11, enquanto a A1 tinha 9.03 e 8.89ms em janelas correspondentes. Isto não demonstra igualdade da carga nem temperatura.
- Ausência de `surface has become outdated` na sessão B. Nenhuma anomalia de Vulkan fatal observada no trecho, mas uma ausência textual não garante estabilidade perfeita.

## Próximo gate: SAMSUNG_A2

1. Voltar ao **Driver do sistema** pelo menu NFSMW e reiniciar somente o app (não desinstalar). Preservar V51, 1920×1080 internos, cap 60, gráficos completos, física, saves, controles e proteção térmica.
2. Repetir mesma cena com carro parado e executar `bash ~/nfsmw_pre694_aba_readonly.sh arm SAMSUNG_A2`; ao final `status` e `finish`; enviar os cinco arquivos da fase A2 mais `nfsmw.log` dessa sessão.
3. Comparar A1–B–A2 com mesmos cálculos, confirmar driver no log e amostras C2. Se o Samsung A2 diferir muito do A1, examinar ordem/carga/térmica antes de favorecer RADV.
4. Arquivar raw privado em `NFSMW_Android/06_Logs_e_Medicoes`, registrar resultado e atualizar `CONTEXTO_NFSMW.md` com backup e readback. **Não houve APK, patch, assinatura ou otimização de FPS.**

**STATUS PRE694_B:** ZIP_CRC_PASS; PHASE_RADV_B_STRUCTURE_PASS; RUNTIME_RADV_VERIFIED; SF_30_SAMPLES_PASS; JITTER_SD_AND_8_25_TRANSITIONS_LOWER_OBSERVED; LONG_TAIL_WORSE_OBSERVED; WATCHDOG_ZERO_IN_THIS_RUN; C3_DUPLICATE_PERSISTS; A2_PENDING; NO_CAUSAL_FPS_GAIN.


## Arquivos privados no Google Drive
- [ZIP original de evidência RADV B](https://drive.google.com/file/d/1VSS7F52_t1XCgbdotMp7tsrT6-odqwZ5/view)
- [Relatório técnico e auditoria reproduzível ZIP](https://drive.google.com/file/d/1kGo2Yyi0Wwlp8lXIqeVDEh46TmUDD5dd/view)
- [Relatório Markdown](https://drive.google.com/file/d/1jQG0UCOQ78zl2PIo_wQWoi1kVagtjsaT/view)

**Nota de segurança:** nenhum log bruto, ISO, APK, credencial ou chave privada foi adicionado ao repositório público.
