# PRE298 — Resultado real do cache ARM64 PAL (2026-11-07)

**Execução:** https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42383054863  
**Relatório original:** artifact 13578999775  
**Leitura verificada:** https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42387021709

## Resultado medido

| Medição | Compilação 1 | Compilação 2 |
|---|---:|---:|
| `elapsed_wall_seconds` | 1330.06 | 1378.91 |
| Duração | 22min10.06s | 22min58.91s |
| `cacheable_calls` acumulado | 49 | 98 |
| `hits` acumulado | 0 | 0 |
| `misses` acumulado | 49 | 98 |
| `libmain.so` bytes | 116758848 | 116758816 |
| `libmain.so` SHA-256 | `74068d1a512c34b134a16838faf5f6ef12f36cd7182f29ea29ab8efd961a81fc` | `4357e9ddd42d9c97d26ffebde39fa2d50228f15af397b48b758f810eb2331299` |

**Resultado:** GitHub Actions `success` e PRE298 script `AUDIT_OK` porque as duas compilações/linkagens PAL foram bem-sucedidas, **não** porque o cache atingiu ganho ou equivalência. `PRE298_HASH_EQUAL False`, `PRE298_GAME_CACHE_PERSISTED False`.

A segunda foi **48.85 segundos mais lenta** e 32 bytes menor. Zero hits reais em ambas passagens. **Cache de objetos do jogo NÃO APROVADO para release, nem para armazenamento persistente.** PRE295C continua sendo somente o canário validado de SDK, ainda não incorporado em release.

## Interpretação e próximos testes

- As árvores temporárias PRE288 diferem entre as iterações; é hipótese que caminhos absolutos, dependências, flags, arquivos gerados ou metadados de link inviabilizem hits de `ccache` e a identidade do DSO. **Não atribuir causa sem comparação de `compile_commands.json`, arquivos .d/headers, logs de debug ccache e seções ELF**.
- O `ccache` registrou 49 chamadas cacheáveis por compilação. É possível que esse subconjunto não cubra todos os shards do motor; validar instrumentação do launcher com métricas separadas por `nativo/app`, `nativo/app_usa` e `nativo/sdk`.
- Reformar o gate de futuros ensaios: só registrar `CACHE_AUDIT_OK` se duas builds com fontes/flags equivalentes gerarem DSO equivalente (ou diferença demonstrada como exclusivamente não funcional), hits warm >0 e tempos de fases confiáveis. Não tratar sucesso do link como sucesso do cache.
- Futuro ensaio deve usar clone/árvore estável ou normalização reprodutível de paths, ccache debug com saída filtrada sem segredos, e comparar ELF .text/.rodata/.symtab/build-id, não apenas tamanho. Objetos reais não persistidos no GitHub.
- Nenhum patch de menu BMW, APK, assinatura permanente, save MARCEK ou controles foi alterado.
