# PRE623 — PRE607 validada por SHA no S24 FE; zeros BMW confirmados; prévia de telemetria do atributo aprovada (2026-11-09)

## Evidência do dispositivo — PRE620

O usuário enviou os hashes completos calculados localmente no aparelho para os dois arquivos ativos:
- `/storage/emulated/0/NFSMW_PTBR/NFS/ZDIR.BIN` SHA256 **`f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2`**;
- `/storage/emulated/0/NFSMW_PTBR/NFS/ZZDATA4.BIN` SHA256 **`1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146`**.

Ambos são exatamente os arquivos previstos pela PRE606/PRE607. **Estado atual: PRE607 ativa no armazenamento confirmada por hashes fornecidos pelo usuário.** Essa prova não substitui uma telemetria guest que mostre a leitura/decodificação específica de `GLOBAL/ATTRIBUTES.BIN` nem o uso da coleção BMW nova.

## Último sintoma — PRE617

O usuário confirmou: na BMW M3 GTR normal adicionada ao perfil novo `NAME`, **todas as categorias de desempenho exceto Nitro mostram `Option Title`**. O `nfsmw.log` anexo foi lido: 3.937.714 bytes, 15.827 linhas, SHA256 **`dc9fc0bb08ba943ede3e7675570c1c1fb15ddb5db743cee74edda4393109de0e`**, última sessão 14:08:12–15:06:40. Às 15:06, a V48 registrou sete `NFSMW_PRE447_ROUTE reason=2` e `NFSMW_PRE429_LEVEL` da BMW `type=41`:
- engine categoria 4 **0**; transmissão 3 **0**; suspensão 2 **0**; Nitro 6 **3**; pneus 0 **0**; freios 1 **0**; indução 5 **0**.
- Esse mesmo vetor **0/0/0/3/0/0/0** já fora observado na BMW V47 PRE444, enquanto Fiat Punto tipo 74 possuía valores positivos em todas as sete categorias.
- `reason=2` é a **rota de atributo resolvido**, não erro/descritor ausente. O retorno pode ser zero ou positivo, como mostra Nitro 3 na mesma rota. A associação com a string literal `Option Title` é relato do usuário; a string não aparece no log.
- O novo save `NAME` está funcionando e contém uma BMW adicionada pela PRE614; isso **não torna a lista de upgrades comprável**. Não adicionar a BMW novamente nem alterar save ou outros carros.

## PRE618/621/622 — evidência de código e próximos gates

- PRE618 [GitHub Actions 42672824917](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42672824917) `AUDIT_OK`: script `automation/device/pre618_check_active_bmw_archive_readonly_shevery.sh` verifica identidade dos arquivos sem escrever. O usuário realizou sua própria leitura direta `sha256sum`; não alegar que executou esse script PRE618.
- PRE621 [run 42676653898](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42676653898), `AUDIT_OK`, `docs/PRE621_BMW_GUEST_ATTR_LOOKUP_REGISTERS_READONLY.json`. Revalidou backup privado PRE99 874780689 B, SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`, inspecionou quatro funções guest originais sem publicar C++ completo. `sub_823E5988` possui saídas em linhas relativas 60,126,153 e **lê atributo com `REX_LOAD_U32(ctx.r11.u32 + 0)` na linha 104**, ramo `reason=2`. Funções `GetMaxLevel` e `SetLevel` não identificadas; tampouco comprovação de que a segunda referência `RefSpec` da BMW foi usada.
- PRE622 [run 42677165694](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42677165694), `AUDIT_OK`, `docs/PRE622_BMW_ATTR_HOST_VALUE_RAM_PREVIEW.json`. Prévia **somente em RAM** sobre a fonte guest autenticada, modificando apenas um ponto de instrumentação imediatamente após o `REX_LOAD_U32` que já existia. Capturará `original_caller_lr`, categoria original 0–6, endereço de valor `ctx.r11`, valor já calculado `ctx.r3`, com filtro de retorno `0x8256F83C`. Nenhuma carga/store/chamada guest adicional, número de instruções PowerPC preservado, transformação fonte reversível. SHA256 da prévia descartável `2e6907363bd87ddb2d2643364ab13b72facf28eb1f2c8b6da2c360a3d871f6af`.
- **Nenhum callback C++ host foi compilado/vinculado, nenhuma APK V49 foi construída**. Ainda será preciso implementar o callback host, preservar invariantes Android/Nitro/PG9076 e certificar que diagnóstico sem efeitos colaterais é operacional antes de qualquer nova APK. Não declarar que a causa dos seis zeros já foi identificada, nem prometer peças compra/instalação/física/saves.

## Ação atual

**Nenhum script adicional no celular por enquanto.** Preservar PRE607 aplicada (hashes confirmados), perfil `NAME`, BMW existente, backups e APK V48 PRE452. Não restaurar, não introduzir novas variantes/contadores, não forçar `candidate_count` diferente de zero ou comprar entradas `Option Title`. Próximo gate de desenvolvimento: validar callback C++ host e build somente diagnóstica mantendo **certificado PERMANENTE** SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, package `io.github.nfsmwrecomp` e versionCode incrementado se houver release, sem tocar em segredos, Nitro PRE398, PG9076/touch, 1920×1080, qualidade/shaders/efeitos/física e proteções térmicas. Meta FPS 120; logs de V48 cap 60, sem ganho comprovado.
