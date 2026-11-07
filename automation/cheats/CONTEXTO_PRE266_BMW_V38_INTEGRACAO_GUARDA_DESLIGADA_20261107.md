# NFSMW Android — PRE266: integração isolada das sondas V37 com patch BMW desativado (2026-11-07)

## Evidência confirmada
- GitHub Actions PRE266: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42322263103 — **conclusão success**, relatório `PRE266_STATUS AUDIT_OK`, `phase COMPLETE`.
- Fonte de restauração: backup PRE99 autenticado SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`. Restauração **apenas temporária em runner GitHub**; não foi upload de fonte do jogo nem modificação de cópia persistente.
- Sobre a árvore descartável, aplicadas as sondas V37 PRE246 (8 sites money) e PRE247 (8 sites nitro/speedbreaker), **total 16 sites instrumentados**, confirmados no relatório.
- Verificado o arquivo PAL `workspace/nativo/app/generated/default/nfsmw_recomp.5.cpp` com SHA256 original `26c58fa8c5b5810f2fa06bcf25d3f3f7ac131bf73692a9991a84269433b8de07`, inalterado pelas sondas V37.
- Inserido **somente na árvore descartável** o código experimental PRE264 em `sub_82578988` após âncora de comparação `BMW==41`, sob macro `NFSMW_PRE264_BMW_MENU_ENABLE` explicitamente **NÃO definido**; hash SHA256 do arquivo PAL ensaiado `1dc5745263d68e186e66545f8795b2a11fffc8d5011aec74f3ce8a9256afe11c`.
- Validado marcador único, reversibilidade exata, e ausência de chamadas extras de leitura/gravação guest, preservando o arquivo USA. Não aplicar 2 vezes.
- Artefato de auditoria sanitizado arquivado no Drive: https://drive.google.com/file/d/1mSnAjFEEV7x4ZqIvLYhehOah8wjQC4Tk/view (ZIP contendo JSON, sem save pessoal e sem credenciais).

## PRE265 anterior
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42321948518, `AUDIT_OK`, **131 C++ PAL**; analisou `sub_82578988` e `sub_82582F70` com 1 e 2 comparações tipo 41, e 8 funções auxiliares; **5.904 testes sintéticos** da política conservadora `bmw própria + fora do prólogo + ativação explícita + quantidade>0`.
- **Limite essencial:** `Physics::Upgrades::GetMaxLevel(ThePVehicle,type)` **não teve valores reais de BMW confirmados**. Mock host não é compatibilidade comprovada de um pacote de upgrade. `CustomizePerformance::RefreshHeader()` do código público acessa `GetSelectedPart()` sem guarda explícita nesse ponto; se a categoria estiver vazia, há risco de erro. Não afirmar crash real.
- A PRE266 **não testou o restante dos patches SDL/input/UI/C3 da V37**, nem compilou código nativo/game, nem construiu/assinou APK. É apenas pré-teste de compatibilidade do **código recompilado de sondas** com a transformação guardada/desligada. Não alegar integração completa da V38.

## Status release/usuário
- BMW inserida via save PRE260 no perfil MARCEK e dirigível, conforme relato do usuário; Punto, saldo e Junkman preservados. Só `Visual` no tuning, confirmado.
- Nenhum novo APK, nenhum teste novo de dirigibilidade, nenhum save modificado, nenhuma assinatura acessada neste PRE266. V37 permanece último APK testado, com pacote `io.github.nfsmwrecomp` e certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- **Próxima etapa:** identificar contagens efetivas de `GetMaxLevel()` para BMW no modelo de atributos PAL em runtime ou por análise de atributos; planejar UI que recuse zero opções sem acessar `GetSelectedPart()` nulo. Só então preparar build de teste V38 com versionCode>=38 e a mesma assinatura permanente; preservar V37, saves, PG-9076, 1920x1080, fps cap, efeitos/física e limites térmicos. Razor/BMW prólogo não corrigido.
- Atualizar contexto canônico `CONTEXTO_NFSMW.md` no Drive **somente após backup** e conciliação com seções PRE238–266. Esta nota técnica isolada mantém evidências recentes sem sobrescrever histórico desatualizado.
