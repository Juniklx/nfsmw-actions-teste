# NFSMW — Roadmap de otimização de código após PRE642/V50 (2026-11-10)

## Decisão do usuário

Suspender **a investigação de fluidez/frame pacing/SurfaceFlinger**, inclusive novas coletas nessa trilha, e seguir por otimizações de código organizadas pelo potencial de desempenho. A fase investigativa C3 PRE643 permanece **em espera como prioridade de desempenho**, sem rejeitar a correção futura nem alterar os guardas PRE194/PRE635. Não inferir que foi corrigida.

## Baseline e fatos verificáveis

- APK V50 PRE638 assinada, `versionCode=50`, `io.github.nfsmwrecomp`, cert SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Log PRE641 no Galaxy S24 FE de 2026-11-10 01:00:45–01:05:18 contém marcador PRE635 e falha C3 (worker desativado; fallback mantido); versão exata no aparelho não atestada independentemente no log.
- V50, janelas C2 01:01:45–01:05:05: `12.002 / 200,055 s = 59,994 FPS` internos, sob limite **60 FPS**, renderização **1920x1080**, GPU `10,099 ms/Swap` ponderados; sem medição de melhoria causal.
- C2, janela fechada 01:05:05: GPU por Swap `escena=3,51 ms`, `320 cubo e desfoco=1,45`, `reflejo=1,12`, `sombras=1,05`, `copias=1,77`, `borrados=0,56`, `escena sem profundidade=0,42`. Não somar com a métrica `hueco entre trabajos=6,68` (convenção diferente).
- Processador por pacote: `op 22=480,9 ms/s` (`4.174.724` pacotes medidos), `op 3C=382,2 ms/s` (`54.251` pacotes), na janela de log de 20 s; custos de CPU, não tempo de GPU. Auditoria de fonte deve confirmar significados e localizar os trechos reais antes de patch.
- C6 aproximadamente `3.480 desenhos por fotograma` em passes (sombras 1.376, cena 937, reflexo 408, cubo 694, menores 4, sem profundidade 61), cerca de `19 copias` e `10,31 Mpixels` por fotograma. C6 vértices: dedupe já evita `4.515,02 MB` no intervalo (~41% dos bytes subidos), mas aponta `27.266 colisões` cumulativas da tabela. C5a IM_LOAD shortcut e cache de shaders já ativos; cache de samplers tem muitos acertos.
- PRE180/V35 já reduziu custo SDLThread `74,41% -> 0,79%` de um núcleo observado comparado a V34; não restaurar problema corrigido nem supor ganho de FPS. PRE398 Nitro, ponte PG9076, shaders, controles, assets, save, física e thermal sempre preservados.

## Priorização de potencial, não de ganhos demonstrados

1. **GPU: shaders e estágios de renderização** — reduzir instruções e acessos redundantes mantendo equivalência visual; maior área de tempo GPU; risco alto.
2. **CPU: comando 0x22/0x3C e processamento de registros do anel** — custos CPU altos diretamente observados, candidato inicial mais controlável; risco médio-alto.
3. **GPU: cópias de cor/profundidade, resoluções e staging** — 1,77 ms/Swap e 10,31 Mpixels por frame; só eliminar operações se comprovadamente redundantes; risco alto.
4. **CPU/Vulkan: gravação de draw calls e mudança de estado** — milhares de desenhos por frame, preservar ordem, sem fundir draw calls com semântica diferente; risco alto.
5. **Vulkan: passes, transições de destino, layout e barreiras** — muitos passes/retomadas, remover apenas sincronizações comprovadamente excessivas; risco alto.
6. **Uploads de textura/C3** — problema real, mas impacto em FPS desconhecido; não suprimir a segunda cópia nem desativar fallback; risco alto.
7. **Vértices/índices/constantes** — redução adicional de cópias e colisões de dedupe; parte já otimizada, ganho incerto; risco médio.
8. **Alocações, reutilização de buffers, caches temporários** — medir antes de propor pools; impacto não dimensionado; risco médio.
9. **Criação de pipelines/caches** — possível melhora de carregamento, pouco potencial sustentado observado, `116 pipelines, 188 ms` acumulados; risco médio.
10. **Instrumentação/logs remanescentes** — testar overhead em A/B mantendo erros e diagnósticos, sem presumir impacto; risco baixo.

## Ordem de execução escolhida

Começar pela **prioridade 2** (opcodes 0x22 e 0x3C) apesar da GPU ser prioridade potencial número 1. Justificativa: alvos CPU mensurados e oportunidade de patch pequeno, reversível e verificável sem alterar renderização. Nova auditoria **somente leitura** da fonte exata que compõe V50 (PRE99 + cadeia verificada). Identificar pontos e custos reais; validar equivalência de sequência de comandos/registros, microbench e ARM64 `no APK`. Se benefício real e sem regressão, versão posterior **V51**, `versionCode>50` e certificado permanente original; não reconstruir chave, pedir segredos ou tocar saves. Comparação de FPS com cap 60 não prova melhoria acima de 60; mensurar custo CPU e eventual GPU com protocolo controlado. Se sem benefício, seguir shaders GPU.

Esta nota é **planejamento e mudança de prioridade**: nenhum patch, compilação, APK, instalação, teste de melhoria ou alteração de configuração foi executado aqui.
