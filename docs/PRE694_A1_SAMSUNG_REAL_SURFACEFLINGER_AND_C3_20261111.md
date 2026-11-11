# PRE694 A1 — Samsung, captura real do Galaxy S24 FE (11/11/2026)

## Origem e identificação

- Arquivo original: `nfsmw.zip` fornecido pelo usuário, **470311 bytes**, SHA-256 `a188508c235fa941e33f2bba9b44fa248b951c3af5cb3bb68cfd258cf0fba755`; 5 entradas; CRC ZIP **PASS**.
- Pacote: `io.github.nfsmwrecomp`, V51 (manifesto da fase; código versão verificado no preflight do wrapper), Galaxy S24 FE SM-S721B.
- Fase declarada `SAMSUNG_A1`. **Driver efetivo comprovado de forma independente pelo log:** `driverID: SamsungProprietary`, `driverName: Samsung Proprietary driver`, SPAL 25.3.3; sem marcador de carregamento RADV nessa sessão.
- A sessão A1 começou **14:16:52.609** e o último registro presente é **14:21:22.145**, duração observada **269.536 segundos (4 min 30 s aproximadamente)**. O log contém *outra sessão Samsung anterior* de 11:48:53 a 11:55:13; as métricas aqui são somente da sessão A1.
- Configuração registrada: resolução interna **1920×1080** (modo guest 1280×720 distinto), limite **60 FPS**, swapchain `MAILBOX`.
- Timestamps SurfaceFlinger da mesma sessão: **14:18:39–14:19:18 -03:00**, 30 consultas, uma SurfaceView avançando. Status `PRE690_CAPTURE=RECORDED_UNANALYZED` foi estruturalmente validado como `PRE694_CAPTURE_STRUCTURAL_VALIDATION=PASS`.

## Estatísticas reconstruídas da apresentação

| Métrica | Samsung A1 PRE694 | Samsung PRE690 anterior | RADV PRE691E anterior |
|---|---:|---:|---:|
| Intervalos contínuos após deduplicação e exclusão de lacunas | **2,327** | 2.333 | 2.321 |
| FPS médio estimado nos intervalos contínuos | **59.998** | 59,993 | 59,997 |
| Intervalo médio `actualPresent` | **16.667141 ms** | 16,668695 ms | 16,667457 ms |
| Desvio-padrão populacional | **3.846875 ms** | 3,945334 ms | 3,654309 ms |
| Intervalos 8–9 ms (arredondados) | **242** | 257 | 220 |
| Intervalos 25 ms (arredondados) | **238** | 256 | 220 |
| Transições consecutivas estritas 8↔25 ms | **278** | 290 | 250 |

Detalhamento PRE694 A1: **3,647** registros válidos de snapshots, **2,329** apresentações únicas, **1,318** duplicações de amostragem descartadas, sem conflitos entre triplas atribuídas ao mesmo timestamp efetivo. Em períodos contínuos: buckets arredondados `{'8': 234, '9': 8, '14': 1, '16': 85, '17': 1756, '19': 1, '20': 1, '21': 1, '25': 238, '33': 1, '42': 1}`. A cobertura contínua é **38.784 s**; uma lacuna de **1132.756 ms** foi **excluída por incerteza de cobertura** (não comprova congelamento real).

A pequena redução de dispersão contra a PRE690 Samsung anterior e a diferença para RADV não permitem imputar melhoria causal sem cenas, temperatura e condições reproduzidas em pares. A média se manteve perto de 60 FPS, mas a alternância 8/25 ms permanece.

## Motor C2 e anomalias na A1

- Watchdog `[vigilante]`: **0 ocorrências na sessão A1**. Ausência de alertas não é prova de ausência de microstutter ou pausa visual.
- C3 duplicado: **uma ocorrência às 14:17:15.613**, antes da captura SF, com `NFSMW_PRE635_C3_TWOREQUEST_TRACE` e `NFSMW_PRE194_C3 ... copia_duplicada=true`, assinatura idêntica às registradas em Samsung PRE693 e RADV PRE692: `indice=0`, `en_vuelo=1`, `offset_primera=0`, `offset_segunda=51872`, `mismos_comandos=true`, `subir=true`, `trabajo_huella=0`, `datos_bytes=43648`. O guard desativou a thread auxiliar e preservou fallback. **Não reaplicar patch nem desabilitar guard.**
- Dentro da janela SurfaceFlinger: relatórios C2 encerrados **14:18:53.320** (1.200 swaps, 1.162 entre 15–18ms, 29 entre 18–25ms; GPU real por Swap **9,03 ms**) e **14:19:13.321** (1.200 swaps, 1.175 entre 15–18ms, 16 entre 18–25ms; GPU real por Swap **8,89 ms**). Histograma C2 interno e `actualPresent` são métricas diferentes.
- Fora da janela SF: C2 registrou máximos de **100,5ms às 14:17:13** e **99,5ms às 14:17:33**; em **14:21:22**, ~2 minutos após o fim da captura, ocorreu um diagnóstico `[tiron] fotograma de 100.0 ms` (GPU 12,6ms, com longa espera da thread preparadora). Esses eventos não devem ser incluídos como se fossem ocorrências dentro da janela de SurfaceFlinger de 14:18:39–14:19:18. A causa não é demonstrada.
- A sessão terminou no arquivo sem mensagem explícita de crash; não declarar encerramento, apenas último registro disponível.

## Integridade e próximo passo

- SHA-256 do `nfsmw.log` enviado: `8b252808b60efa63f56404bfbaf98dfcb2a0752e2d1051fb1881dfd0c83f3993`, tamanho **2.168.402 bytes**, com sessão anterior concatenada.
- Hashes das três peças críticas (status, raw SF e manifesto) presentes no arquivo de validação conferidos **exatamente** com os bytes dentro do ZIP.
- Arquivo original privado preservado no Drive: [PRE694 A1 ZIP](https://drive.google.com/file/d/1pYPrNP-YD3vJbaNQblVBtK5GDsZsYel_/view). Não publicar log bruto no repositório público.
- **PRE694 A1 = PASS de captura e identificação Samsung; resultado de desempenho não causal.** Próxima fase: **RADV_B**, selecionando RADV v1.8.0 manualmente na UI, reiniciando só o aplicativo, mantendo 1920×1080, cap 60, tudo visual intacto, e coletando o mesmo trecho e duração com `bash ~/nfsmw_pre694_aba_readonly.sh arm RADV_B`; ao final, `status` e `finish` e anexar `nfsmw.log` da sessão. Em seguida será necessário **SAMSUNG_A2**. Não modificar APK/assinatura, saves, controles ou proteções térmicas.
- Sincronização com `CONTEXTO_NFSMW.md` no Drive ainda pendente de backup + append, sem apagar histórico; não supor que arquivo canônico esteja atualizado além da PRE690.


**Private original**: raw log archived on Google Drive; not mirrored into this public GitHub repository.


## PRE694 A1 — atualizacao de contexto canônico verificada (2026-11-11)

O arquivo histórico completo `NFSMW_Android/CONTEXTO_NFSMW.md` foi atualizado **somente por append**, incorporando as evidências PRE690 real, PRE691F, PRE692, PRE693 e PRE694 A1. Backup integral independente: [CONTEXTO_NFSMW_BACKUP_ANTES_PRE694_A1_REAL_20261111.md](https://drive.google.com/file/d/1zU0rSWVRsbCySJUxZSTcv_hyhi4Ai38M/view) SHA256 `1f66fe4c5448b28697c16ec5c0f001ca9f330319e31fec9b378b1bcbde89c190`, 1.157.094 bytes. Canônico após o append: [CONTEXTO_NFSMW.md](https://drive.google.com/file/d/1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB/view), 1.164.785 bytes, SHA256 `a5464d2860184bf46c26801bbb2ed38483897fe4805a8929e2a28d419973b1ba`. **Readback completo byte a byte idêntico ao append preparado, prefixo original idêntico ao backup.** Informações antigas no texto acima indicando "sincronização pendente" foram superadas por esta atualização posterior.

Próximo gate **RADV_B** com coleta A/B/A (A1 concluída, B e A2 pendentes), sem alterações na APK V51, driver de sistema ou térmica. Nenhuma causalidade sobre travamentos ou ganho de FPS demonstrada.
