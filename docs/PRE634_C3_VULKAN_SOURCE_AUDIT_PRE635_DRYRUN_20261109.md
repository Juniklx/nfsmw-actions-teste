# NFSMW PRE634 concluída / PRE635 preparada — 2026-11-09 (Bahia)

## Entradas reais
- Galaxy S24 FE, V49 confirmada pelo `PRE632B VERSION_CODE=49`, log interno 22:57:33–22:59:55 UTC−03.
- PRE632B SurfaceFlinger: 7.613 apresentações, ~59,94 FPS; 714 bins >=24 ms, 731 no bin 8 ms. Histograma cumulativo; duas coletas globais parcialmente sobrepostas; não somar.
- PRE633: `NFSMW_PRE194_C3 indice_fuera=false referencia_distinta=false copia_duplicada=true` em 22:58:03.412. C2 max Swap 500,2 ms na janela até 22:58:14; nexo causal não provado.
- Relatório anterior: https://drive.google.com/file/d/1AyD3gxvlh2dsalRNEJTcwtqwSR7HKZtB/view

## PRE634 — fonte autenticada, não V49 reconstruída
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42742959129 , `completed/success`.
- Evidência: `PRE634_STATUS=AUDIT_OK_PRE99_ONLY`, `PRE634_PRE99_VERIFIED=True`, `PRE634_SOURCE_FILES=7`; `PRE634_EXACT_V49_SOURCE_VERIFIED=false`.
- PRE99 SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`.
- Fonte PAL C3 SHA256 `046ea454634d84169ccda0237c347d17020a63da027878d4fd21f7a3520251e2`; Vulkan presenter PRE99 SHA256 `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48`. Não usar hash do ZIP histórico `eada...` como se fosse PRE99.
- PRE194 aplicada apenas em memória, SHA256 `a01f25e531af783d37f70a3c3caa0f3e7a979d2bdbdd923abf7b2c6062d29d1e`; guarda C3 preservada, reversão exata.
- Artefato GitHub ID `13730180846`; cópia Google Drive https://drive.google.com/file/d/1TM3ZV9I6XiLF6QDAnsBXuJMF8XYKDF6y/view .
- Nenhum APK gerado, chave/certificado acessado, source tree ativa alterada ou ganho de FPS medido nesta etapa.

## Novo achado restrito do código C3
- `AplazarCopia` (fonte histórica PRE185 linhas ~5754–5768) detecta a segunda tentativa quando `en_vuelo_[indice].copia` já é verdadeiro.
- `SubirTextura` (linhas ~9657–9700) limpa `textura.subir=false` após o pedido. Uma duplicação simples do ponteiro na lista de uploads sem reativação de `subir` não explica sozinha o segundo `AplazarCopia`.
- Dois caminhos produtores (`PlanearHuella` e `PrepararTextura`) podem preencher a lista, mas nenhum foi identificado como responsável pelo incidente da V49.
- A proteção `ApagarEnlaces` não deve ser removida.

## PRE635 — somente protótipo host em memória
- Script: `automation/kaggle/pre635_c3_duplicate_request_trace_dryrun.py`.
- Teste local do protótipo sobre PAL PRE185 + PRE194 autenticadas: `DRYRUN_OK`, SHA256 candidato `1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92`, reversible, double application rejected.
- Logger somente no ramo de erro por `copia_duplicada` com índice e textura válidos; compara épocas, offsets, identidade relativa do command buffer, estado `subir`, quadro e trabalho de hash, sem registrar conteúdo ou ponteiros. Mantém a decisão e fallback.
- **Não houve compilação C++ ARM64, APK V50 ou teste de dispositivo.** Nem o protótipo local nem o arquivo do repositório foram validados como substituto da árvore V49 exata.

## Próximo gate seguro
1. Reconstruir a fonte V49 exata pela cadeia PRE194→PRE246→PRE401→PRE434→PRE452→PRE626, em diretório efêmero e autenticar hashes.
2. Se o guard de V49 coincidir com o SHA pinned esperado, testar a PRE635 em memória e, depois, compilar somente `libmain.so` PAL ARM64 num gate sem APK e sem assinatura.
3. Só após aprovação do gate e estratégia de coleta temporal, considerar APK instrumentada `versionCode>49` com certificado permanente original `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Não mudar Vulkan MAILBOX, 1920x1080, qualidade, física, input, Nitro, save, nem limites térmicos por hipótese.
4. Tratar pacing 8/24–25ms em medição separada de textura C3. Não interpretar os 714 bins como 714 frames descartados.

## Persistência
- `CONTEXTO_NFSMW.md` canônico: https://drive.google.com/file/d/1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB/view, atualizado por append PRE632–PRE635, SHA256 `f0e59bbba852ec981ace2cf8980d49ea3dab0bbbb14c2fba83cb3de59abdd6e2` verificado no readback.
- Backup anterior: https://drive.google.com/file/d/1a0PlSvuU00fWSd3yo_ZRJ4mddKm9Lqx_/view .
