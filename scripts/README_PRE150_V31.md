# NFSMW PRE150 — captura térmica/Vulkan pareada na V31 (pendente no telefone)

Data do registro: 2026-11-04.

## Evidências verificadas
- Repositório: `Juniklx/nfsmw-actions-teste`, branch `main`.
- Script arquivado em `scripts/nfsmw_pre150_v31_profiler_termico_sessao_unica.sh`, sem segredos nem dados de jogo.
- Script local: sintaxe Bash aprovada; simulação de `rish` com UID 2000, `versionCode=31` e intent de inicialização aprovada (status 0); simulação com `versionCode=30` bloqueada (status 11).
- Nenhuma execução real da coleta PRE150 no Galaxy S24 FE foi observada até este registro.
- `CONTEXTO_NFSMW.md` canônico no Drive tem seção PRE150; ele **não** foi alterado por esta inclusão no GitHub.

## Procedimento com intervenção humana indispensável
1. Com Galaxy S24 FE e `versionCode=31`, Shizuku ativo e `~/rish` disponível, fechar o jogo e salvar o script em `~/storage/downloads/`.
2. No Termux, iniciar: `bash ~/storage/downloads/nfsmw_pre150_v31_profiler_termico_sessao_unica.sh 300 3`.
3. Jogar o cenário de teste correspondente, sem mudar 1920×1080/120 FPS/gráficos, e manter a sessão de coleta ativa.
4. Preservar `nfsmw_pre150_v31_profiler_termico_*.txt`, `nfsmw_pre150_v31_profiler_erros_*.txt` e `nfsmw_pre150_v31_profiler_*.log` quando houver cópia externa. Se não houver, obter `nfsmw.log` separadamente.

## Próximo passo após coleta
Correlacionar somente as janelas horárias sobrepostas de `vkQueuePresentKHR`, `PaintAndPresent`, GPU real por Swap, Thermal Status, GPU DEVFREQ e bateria. Não inferir causalidade térmica sem controle de cenário. Se falhar, examinar log recente antes de repetir.

## Preservação
Não gera APK nova, não altera TOML, saves, shaders, PG-9076, física, sincronização Vulkan ou limites térmicos. Se for necessária uma V32 futura: preservar `io.github.nfsmwrecomp`, certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` e usar versionCode maior que 31.
