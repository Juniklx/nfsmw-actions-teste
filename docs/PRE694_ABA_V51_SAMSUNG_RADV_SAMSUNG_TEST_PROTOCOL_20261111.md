# PRE694 — Protocolo A/B/A com V51 e driver Samsung/RADV (2026-11-11)

## Base comprovada
- APK instalada no Samsung Galaxy S24 FE SM-S721B: pacote `io.github.nfsmwrecomp`, versionCode 51, SHA256 `207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- PRE691F: RADV v1.8 carregou de fato, 2321 intervalos SF contínuos, menor dispersão observada que Samsung, mas **nenhum ganho de FPS médio comprovado**. Comparação não pareada de cenas/condições.
- PRE692: RADV 11:10 teve 7 episódios do watchdog (6 retomados e 1 sem retomada no fim do arquivo), alguns ANTES do desarme C3.
- PRE693: Samsung 11:48 teve ZERO eventos do watchdog em ~6m20s de log, mas C3 duplicado na mesma assinatura observada em RADV e GPU até ~16ms/Swap em trechos de maior carga. Diferenças não provam causalidade.
- Relatórios históricos: docs/PRE691_REAL_PHASE_AND_RADV_XCLIPSE_LOADING_FEASIBILITY_20261111.md, docs/PRE692_REAL_RADV_C3_WATCHDOG_CHRONOLOGY_20261111.md, docs/PRE693_REAL_SAMSUNG_CONTROL_C3_WATCHDOG_GPU_20261111.md.

## Objetivo e limites
- A/B/A: `SAMSUNG_A1` → `RADV_B` → `SAMSUNG_A2`, uma captura SurfaceFlinger por etapa, cada uma com seu `nfsmw.log` de mesma sessão. A distinção de drivers deve ser **verificada pelo log**, não pelo rótulo da pasta.
- Não alterar APK, assinatura, saves, PG-9076, resolução interna 1920x1080, cap 60 FPS, shaders, textura, efeitos, física, estado térmico ou propriedades do Android. **Nunca** forçar relógios, desativar proteção térmica ou inserir driver no sistema.
- Escolher driver manualmente na UI da APK antes de iniciar cada etapa e reiniciar somente o aplicativo para aplicar a seleção; NÃO apagar dados nem reinstalar APK. Condições térmicas, cena, clima no jogo, posição do carro e opções gráficas devem ser tão similares quanto possível. Se não forem, marcar ensaio como não pareado.

## Ferramentas
- Coletor PRE690 verificado: `automation/termux/nfsmw_pre690_ordered_latency_adb.sh`.
- Novo wrapper PRE694 somente leitura: `automation/termux/nfsmw_pre694_aba_readonly.sh`.
- `bash nfsmw_pre694_aba_readonly.sh preflight` exige ADB shell uid 2000, dispositivo SM-S721B, versionCode 51 e SurfaceFlinger disponível.
- Para cada etapa: `bash nfsmw_pre694_aba_readonly.sh arm SAMSUNG_A1` (substituir por `RADV_B` ou `SAMSUNG_A2` somente nas etapas seguintes). O comando usa `arm 110 30`, isto é, espera 110 segundos e coleta 30 amostras de históricos rolling. Abra gameplay e mantenha carro estacionado; não trocar app durante a coleta.
- Acompanhar `bash nfsmw_pre694_aba_readonly.sh status`; ao concluir, executar `bash nfsmw_pre694_aba_readonly.sh finish`. Valida apenas estrutura, conclusão, uma única camada ativa e amostras suficientes. **Não analisa FPS nem garante driver**.
- Artefatos isolados em `~/storage/downloads/NFSMW_PRE694_ABA/<FASE>_<AAAAMMDD_HHMMSS>/`: `PRE694_PHASE_MANIFEST.txt`, `NFSMW_PRE690_CAPTURE_*.status.txt`, `NFSMW_PRE690_ORDERED_PRESENT_*.txt` e `PRE694_PHASE_CAPTURE_VALIDATED.txt`. Enviar estes e o `nfsmw.log` da mesma sessão; preservar arquivos originais, não misturar logs. Observar congelamentos perceptíveis ao longo de 5–8 minutos e anotar se houver.
- Só passar à etapa seguinte depois de confirmar `PRE694_PHASE_CAPTURE=PASS_STRUCTURAL_ONLY`; se o script acusar erro, não alternar driver ou repetir patches às cegas. `finish` não reescreve APK nem altera sistema.

## Gate publicado e evidência
- GitHub Actions `43049979241` `completed/success`: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43049979241.
- Teste sintético `automation/tests/test_pre694_aba_synthetic.sh`: três fases isoladas, versões/modelos/dispositivos inválidos rejeitados, múltiplas coletas bloqueadas. **Nenhum teste real S24 FE executado neste gate sintético**.
- Esta fase PRE694 está **PREPARADA**; ainda faltam capturas reais A1/B/A2. A seleção de driver e diferenças de FPS/latência continuam por verificar.

## Atualização canônica
- O `CONTEXTO_NFSMW.md` no Drive (`1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB`) ainda termina em PRE690; PRE691–PRE694 permanecem em documentação GitHub e Drive separada. Antes de atualizar canônico, copiar backup integral e aplicar apenas append com evidências, paths e ressalvas; não substituir histórico nem promover hipóteses.

STATUS: PRE694_LOCAL_SYNTHETIC_PASS; PRE694_GITHUB_SYNTHETIC_PASS; REAL_A1_B_A2_PENDING; NO_NEW_APK; NO_PROVEN_DRIVER_CAUSALITY; NO_PROVEN_FPS_GAIN.

## PRE694 A1 — atualizacao de contexto canônico verificada (2026-11-11)

O arquivo histórico completo `NFSMW_Android/CONTEXTO_NFSMW.md` foi atualizado **somente por append**, incorporando as evidências PRE690 real, PRE691F, PRE692, PRE693 e PRE694 A1. Backup integral independente: [CONTEXTO_NFSMW_BACKUP_ANTES_PRE694_A1_REAL_20261111.md](https://drive.google.com/file/d/1zU0rSWVRsbCySJUxZSTcv_hyhi4Ai38M/view) SHA256 `1f66fe4c5448b28697c16ec5c0f001ca9f330319e31fec9b378b1bcbde89c190`, 1.157.094 bytes. Canônico após o append: [CONTEXTO_NFSMW.md](https://drive.google.com/file/d/1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB/view), 1.164.785 bytes, SHA256 `a5464d2860184bf46c26801bbb2ed38483897fe4805a8929e2a28d419973b1ba`. **Readback completo byte a byte idêntico ao append preparado, prefixo original idêntico ao backup.** Informações antigas no texto acima indicando "sincronização pendente" foram superadas por esta atualização posterior.

Próximo gate **RADV_B** com coleta A/B/A (A1 concluída, B e A2 pendentes), sem alterações na APK V51, driver de sistema ou térmica. Nenhuma causalidade sobre travamentos ou ganho de FPS demonstrada.
