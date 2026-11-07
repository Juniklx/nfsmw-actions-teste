# PRE336–PRE337 — Diagnóstico passivo de diversidade de destinos Nitro (2026-11-07)

## Fundamentação comprovada
- PRE323: `sub_82424AF0` usa `r31=ctx.r3` e campo `+252`; PRE329–PRE330: `0xBFA9E7FC` observado na execução V41, sem prova de owner exclusivo do jogador.
- PRE334: o padrão estático original do Nitro foi isolado frente aos cinco outros candidatos mais próximos da assinatura estrutural.
- A rotina consulta interfaces via `r31+88` (slot virtual +44) e `r31+72` (slot +152). Nenhuma delas foi identificada como player pointer.

## PRE336: monitor C++ host-only compilado e testado
- Fonte `automation/kaggle/pre336_nitro_address_diversity.hpp`; mock `pre336_nitro_address_diversity_mock.cpp`.
- Run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42412305302, job `128522875268`, `completed/success`, status allowlisted `PRE328_PRE336_SANITIZED_STATUS.json` = `AUDIT_OK`.
- Distingue até 16 endereços de destinos de escrita já calculados, registra apenas slots efêmeros/contagens/bitmasks de sites, rejeita endereço inválido, sinaliza overflow sem reutilizar slot, não lê guest e **não classifica** player/NPC.

## PRE337: integração textual passiva reversível validada
- Script `automation/kaggle/pre337_nitro_diversity_staging.py` e mock `pre337_nitro_diversity_staging_mock.py`.
- Run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42412457916, job `128523332606`, `completed/success`, status allowlisted `PRE328_PRE337_SANITIZED_STATUS.json` = `AUDIT_OK`.
- Em código **descartável**, injeta a PRE336 no callback da PRE317, antes da limitação de 12 logs/site do PRE247; os snapshots usam somente `guest_address` já calculado e mantêm log PRE316.
- Testes verificam reversão byte a byte, preservação da lógica PRE247/PRE316, zero `REX_LOAD_U32`/`REX_STORE_U32` extras, rejeição de dupla aplicação e de fonte que não tenha PRE317.

## Limitações
- Essas duas runs testam somente a sonda isolada e a inserção textual no callback. **Não comprovam compilação/link final do callback C++ com todos os includes, e NÃO comprovam execução no Galaxy S24 FE.**
- A PRE337 não foi aplicada em nenhuma APK; não existe V42 nem cheat funcional. Não concluir que endereço único é carro do jogador.
- Antes de qualquer APK diagnóstica, compilar o callback composto, conferir integração isolada PRE99/CMake e preservar o certificado permanente; depois teste no aparelho com sessão controlada e distinção de player/NPC por referência independente.

## Integridade
V41, `MARCEK`, controles, 1920x1080, física, shaders, efeitos, limites térmicos e chave permanente foram preservados.
