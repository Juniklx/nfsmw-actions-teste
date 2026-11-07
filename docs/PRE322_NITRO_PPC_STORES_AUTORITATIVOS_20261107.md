# PRE322 — Revisão do fluxo PPC do Nitro PAL: ordem dos cinco stores

Data: 2026-11-07. **Apenas leitura**, sem APK, save, assinatura ou patch.

- Auditoria fonte PRE312 autenticada: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42399195782, artifact 13584608070. Fonte `nfsmw_recomp.66.cpp` SHA256 `eec9b82e51bbfcb573cd0f965e3ed7639bbbd291b285f9fc6d5a7d1e77cd735f` (pinned).
- PRE322 GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42403504371 `success`, 5 sites originais verificados com janelas limitadas PPC. No mesmo instante, usuário apresentou log V41 com 58 eventos PRE316 e quase o ciclo completo de Nitro, registrado em `docs/PRE321_V41_NITRO_CICLO_RUNTIME_20261107.md`.

## Fluxo PPC autenticado
1. **Site 1**, linha relativa 377 `stfs f13,252(r31)`: após carregar +252, executa `fsubs f13,f5,f31` e escreve **resultado preliminar de subtração**. Logger runtime V41 mostrava 150 amostras decrescentes 0,993333→0,000000815.
2. **Site 2**, linha 411 `stfs f13,252(r31)`: depois de `fcmpu cr6,f13,f30`, se `!cr6.gt`, `f13=f30`; então escreve o **valor limitado inferiormente** no campo +252. **É a última escrita observada estruturalmente nesse caminho**, não uma prova suficiente de objeto/owner válido para cheat. Na sessão, os valores de sites 1/2 coincidiram.
3. **Site 3**, linha 508 `stfs f0,252(r31)`: lê campo +252, executa `fadds f0,f31,f12` e escreve o **resultado preliminar de recarga**.
4. **Site 4**, linha 518 `stfs f0,252(r31)`: após `fcmpu cr6,f0,f28`, se `!cr6.lt`, define `f0=f28`, e grava o **valor limitado superiormente**, última escrita desse caminho. Na sessão sites 3/4 tiveram 2004 amostras cada, chegando a 0,995188 mas sem confirmação de 1.0 exato.
5. **Site 5**, linha 525 `stfs f30,252(r31)`: caminho alternativo `loc_82424E38` grava valor de `f30` e depois segue para `loc_82424E3C`. Não houve evento PRE316 site 5 no log V41, logo funcionalidade e frequência ainda não caracterizadas. Não remover/suprimir.

**Cuidado:** `f30` e `f28` são limites em registradores PPC. Não assumir seus valores numéricos ou a semântica do proprietário sem verificar a inicialização e contexto. Igualdade das gravações 1/2, 3/4 em runtime é compatível com o fato de o clamp não precisar modificar valores ainda dentro do domínio.

## Próxima etapa proposta
- Criar gate opt-in Nitro **OFF por padrão** para operar apenas quando estado de jogo, objeto, propriedade e intervalo permitido estiverem comprovados; sem reescrever sites 1–5 indiscriminadamente, sem manipular save. `PRE309` é C++ host-only, não integrado.
- Para um experimento real, adotar fonte isolada PRE99, proteção de fingerprint, teste OFF=original e ON isolado, relatório/sentinelas, versionCode incremental 42, mesma assinatura permanente e backup independente MARCEK. Não ativar sozinho só porque os stores estão mapeados.
- V41 continua o APK validado e testado para diagnóstico de consumo/recarga; nenhum cheat funcional ainda.
