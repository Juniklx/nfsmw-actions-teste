# Fluxo NFSMW Android — ideias do SpeedBreaker com gates de evidência

**Instituído:** 2026-11-10. **Referência externa somente leitura:** [SpeedBreakerProject/speedbreaker](https://github.com/SpeedBreakerProject/speedbreaker), `main` no commit `fe04285d7629377c6e422a6ace8f535368f23c31` (consulta em 2026-11-10). A análise de origem foi registrada em [PRE673_SPEEDBREAKER_EXTERNAL_VULKAN_REVIEW_20261110.md](PRE673_SPEEDBREAKER_EXTERNAL_VULKAN_REVIEW_20261110.md).

Este documento transforma ideias verificadas do SpeedBreaker em **candidatos rastreáveis de engenharia**, **não em patches aprovados**. O SpeedBreaker tem arquitetura própria, funcionalidades de desktop e código GPL-3.0-or-later; referenciar uma técnica não licencia automaticamente colar código em outro projeto. A implementação, se viável, deve ser original ou passar por revisão de compatibilidade legal.

## Base protegida do projeto

- Referência atual: NFSMW-Recompiled-Mobile **V51 PRE652** (Android, Xbox 360 USA); `io.github.nfsmwrecomp`, `versionCode=51`, APK SHA256 `207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b`.
- **Certificado permanente intocável:** SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Não ler nem regenerar senhas/chaves; nova APK exige autorização, mesma identidade e `versionCode>51`.
- Preservar 1920×1080 internos, gráficos e efeitos completos, sombras, SPIR-V, física, entradas touch e PG-9076, Nitro PRE398, BMW, C3 PRE194/PRE635, saves, backups e proteções térmicas. Objetivo 120 FPS não implica simulação a 120 passos/s ou configuração de tela atual.
- C2/PRE648/PRE671/PRE672 são referências instrumentadas e separadas; novos pools nunca devem interferir no C2. PRE643 C3, SurfaceFlinger e frame pacing ficam **pausados**, salvo nova decisão explícita.
- A fonte canônica de estado é `NFSMW_Android/CONTEXTO_NFSMW.md` no Drive; adendos sob backup prévio e leitura de retorno exata. Um workflow concluído não significa APK instalada, GPU medida ou FPS melhor.

## Ordem de execução e candidatos

| ID | Prioridade | Referência SpeedBreaker | Objetivo em nosso motor | Estado real / próximo gate |
|---|---|---|---|---|
| SB-01 | P0 | `runtime/gpu/renderer.cpp`: `NFSMW_PASS_PROFILE` e `NFSMW_GPU_TIMING` | Medir **por passe Vulkan**, incluindo tempo entre passes, resolves, uploads, submits e draws VS62/PS58; sem alegar tempo exclusivo do shader | PRE671 ARM64 default OFF, PRE672 HOST e **PRE673 ARM64 compile-only aprovados** (run [42863564617](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42863564617)). A PRE673 compilou adapter + guards default OFF, sem criar pool Vulkan real nem APK. Próximo: sondar timestampValidBits, period, multiview, per-tile, estágios suportados, fences reais e disponibilidade; sem APK até gates |
| SB-02 | P1 | `runtime/gpu/shadow_lend.h` | Identificar resolves/cópias de depth D24S8 elegíveis para adiar, mantendo sombras idênticas | **Somente hipótese**. Primeiro comparar dependências, consumidores guest, layouts, image views, barriers, invalidações e cópia para CPU do nosso V51; proibir patch antes de teste negativo e equivalência |
| SB-03 | P2 | `runtime/gpu/renderer.cpp`: `NFSMW_PASS_MERGE` | Estudar unificação de quebras de renderpass para halo/sol; não retirar efeitos válidos | Aguardar perfis SB-01 e prova de mesma saída color/depth/occlusion |
| SB-04 | P2 | `runtime/gpu/shader_translator.cpp`: `ScalarizeRegisters`, `xmul` | Auditar custo de registradores e da precisão Xenos por shader dominante | Aguardar tempo real por passe; comparar SPIR-V, resultados de operações especiais, imagens e desempenho no Xclipse 940; benefício MoltenVK/AMD **não transfere automaticamente** |
| SB-05 | P3, PAUSADO | `runtime/gpu/command_processor.cpp`: `IdleSpin` | Investigar janelas busy-yield vs sleep e wakeups sem prejudicar input | Não alterar agora; SDL DIAG36/39 é outro caminho de CPU. Exigir CPU clock, latência de controles e Perfetto pareado |
| SB-06 | P3, PAUSADO | `runtime/video/present_schedule.h`, `presenter.cpp`, `game/frame_time.cpp` | Investigar cadência de apresentação (60 aparentando 30), tempos p95/p99 e passos de simulação | Sem patch agora; medir entrega de frames na tela e vblank, `VK_KHR_present_wait`/ID apenas se presentes no driver; respeitar física original |
| SB-07 | FUTURO, NÃO PORTAR | `Smooth Motion` em `presenter.cpp` | Referência conceitual de quadros intermediários | Não disponível/validado no Android; não substituir jogos/steps de 60 Hz por 120 Hz fictícios nem declarar ganhos |

O backlog formal e suas dependências estão em `docs/NFSMW_SPEEDBREAKER_BACKLOG_20261110.json` (mantido no repositório e validado por CI). Prioridade representa **ordem de estudo**, não previsão de ganho.

## Pipeline operacional obrigatório por candidato

1. **G0 — descoberta e fonte imutável:** anotar commit e caminhos dos arquivos externos, trecho/linha e finalidade. Checar licença. Consultar primeiro o contexto do Drive e os artefatos GitHub mais recentes; nunca importar blobs terceiros na fonte ativa por conveniência.
2. **G1 — mapa de compatibilidade, apenas leitura:** comparar operações equivalentes no nosso código **autenticado por SHA**. Identificar mecanismo, consumidores, vida de recursos e riscos. Uma técnica sem dependências equivalentes deve ser rejeitada com motivo.
3. **G2 — segurança e equivalência simulada:** implementar modelo/ensaios unitários com asserções negativas, ASan/UBSan e **fail closed**; garantir reversão byte a byte de todos os patches de fixture; padrões desativados e orçamento limitado.
4. **G3 — compilação Android real, SEM APK:** replay do V51 autenticado em diretório temporário; Clang NDK AArch64; validação ELF, marcadores Nitro/C3/PRE648, SHA e falta de chamadas novas sem autorização. CI deve arquivar stdout, erro, relatório e ZIP com hashes. Nunca confundir um header compilado com código executado.
5. **G4 — diagnóstico em dispositivo (somente depois de desenho e aprovação):** confirmar capacidades Vulkan no **Galaxy S24 FE**; coletar amostras da GPU, preferencialmente por renderpass e intervalos entre passes, com `VkResult`, disponibilidade, fence explícita e custo de instrumentação ON/OFF. Números de draws não são duração. Separar experimentos de controle/touch e de GPU.
6. **G5 — experimento visual/físico isolado:** A/B/A com mesma cena do carro parado após cinemática, mesma resolução, limite, configurações e temperatura/bateria inicial semelhante. Recolher `nfsmw.log`, clock/temperatura (Shizuku), jitter de quadros p50/p95/p99, custo por passe e gaps, hashes/frames comparáveis, bugs e entradas. Melhorias devem ser atribuídas a um patch por vez; se risco visual ou C3, reverter.
7. **G6 — release opcional:** somente com gates anteriores e decisão do usuário. Mesmo pacote/certificado, `versionCode` crescente, APK SHA/certificados verificados, backup de saves, teste real de instalação, execução touch/PG-9076, condições térmicas intactas.
8. **G7 — memória e próxima ação:** enviar relatório ao Drive `06_Logs_e_Medicoes`, fazer backup do `CONTEXTO_NFSMW.md` antes de acrescentar adendo e provar readback byte-idêntico; declarar o que foi *medido*, *simulado*, *compilado*, *instalado* e *não comprovado*.

## Exigências particulares para timestamps Vulkan (SB-01)

- Não conectar macros da PRE672 diretamente ao renderpass sem verificar `multiview`, `per-tile`, suporte a pipeline stage, `timestampValidBits`, `timestampPeriod`, disponibilidade de query, `VkResult` e conclusão real da fence. Ausência de informação é **não suportado**, não permissão tácita.
- Query pool **novo e exclusivo** por slots, número limitado, reset fora do renderpass, serialização de queries com uso de slot depois da fence, erro desliga o recurso; C2 intocado. Não aplicar opções de experimentos de SpeedBreaker via variáveis `NFSMW_*` automaticamente: não existem na nossa V51 apenas porque existem no projeto externo.
- Duração entre `TOP_OF_PIPE` e `BOTTOM_OF_PIPE` mede uma janela na fila, **não custo exclusivo** do par VS/PS. Relatório deve distinguir *time in pass*, *between passes*, *GPU execution* e *presentation latency*, com intervalo e sobreposição claros.

## Conclusão de governança

Adotamos **o método de investigação e o backlog de hipóteses** do SpeedBreaker. **Não importamos código nem prometemos FPS**, não substituímos o renderer e não fabricamos V52. A cada avanço do SpeedBreaker, uma nova ideia só entra no backlog após leitura e referência ao commit; nunca se executa automaticamente um cherry-pick upstream.
