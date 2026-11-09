# PRE627 — Preparação de callback nativo BMW e gate V49 sem release, após PRE624 (2026-11-09)

## Estado anterior confirmado

- V48 PRE452 (`versionCode 48`, pacote `io.github.nfsmwrecomp`, certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`) permanece última APK efetivamente validada no aparelho; **não criar chave nova**.
- Galaxy S24 FE contém **PRE607 ativa**, confirmado diretamente pelo usuário com dois hashes em `NFS/`:
  - `ZDIR.BIN` SHA-256 `f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2`;
  - `ZZDATA4.BIN` SHA-256 `1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146`.
- Save novo `NAME` com BMW normal de fim de carreira injetada via PRE614; BMW acessa a oficina, mas no último log PRE617, SHA256 `dc9fc0bb08ba943ede3e7675570c1c1fb15ddb5db743cee74edda4393109de0e`, retorna **0** em Motor, Transmissão, Suspensão, Pneus, Freios e Indução e **3** em Nitro. UI exibe `Option Title` nas seis categorias zeradas segundo usuário. Compra/instalação/efeito físico/persistência das peças seguem NÃO verificados.
- PRE621 [run 42676653898](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42676653898) `AUDIT_OK`: `sub_823E5988`, ramo reason=2, usa `ctx.r3.u64 = REX_LOAD_U32(ctx.r11.u32 + 0)` no código PPC recompilado. PRE622 [run 42677165694](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42677165694) `AUDIT_OK`: prévia em RAM adiciona chamada host para registrar caller, categoria, endereço e valor já resolvido, **sem cargas/stores guest adicionais**.
- PRE624 [run 42677744651](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42677744651) `AUDIT_OK`: contexto canônico Drive tinha **953585 bytes** SHA256 **`d1422be8fc846427819e8f568e194101d86fafc7af401102583b691e76ea6f0c`**, backup criado, readback confirmado.

## PRE625 — callback host em compilação ARM64 isolada

- Novos arquivos no repositório:
  - `automation/kaggle/pre625_bmw_attr_host_arm64_noapk.py`;
  - `.github/workflows/nfsmw-pre625-bmw-attr-host-native-link.yml`;
  - `automation/kaggle/pre625_requests/`.
- O experimento reconstrói fonte privada PRE99 autenticada, reproduz a cadeia original PRE429/PRE447, injeta a telemetria do PRE622 após a leitura guest **já existente**, e adiciona módulo host `nfsmw_bmw_attr_value_pre625.cpp` em CMake numa árvore temporária.
- Callback `NFSMW_PRE622_ATTR_VALUE(caller,category,address,value)`: filtro `caller == 0x8256F83C`, `category <= 6`, limite de **128 linhas** via contador atômico; **sem dereferenciar endereço guest, sem chamadas guest, sem mudar retorno nem contador de upgrades**. Os três callbacks PRE429+PRE447 e Nitro PRE398 devem permanecer preservados. O gate compara compilações e exige exatamente uma exportação do novo símbolo no ELF ARM64 **antes de autorizar build APK**.
- Primeira execução [run 42705158328](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42705158328) falhou logo no orquestrador por colisão entre variável `p622` do módulo e dicionário JSON (`AttributeError: dict.SYMBOL`). **Não compilou APK; não alterou celular nem arquivos de jogos**. Correção no script em commit `8f6b4e53adafa25c65f35c0c153e1ecc9dd764b5`.
- Segunda execução [run 42705397176](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42705397176): **até o checkpoint desta nota** passou sintaxe/Python e instalação NDK/CMake e estava na **reconstrução nativa ARM64 em andamento**. **Não declarar sucesso ou falha antes do resultado final**, nem inferir que quatro símbolos foram realmente vinculados. O logger/ELF não está no telefone.

## PRE626 — receita de V49 assinada, SOMENTE preparada

- Novo script `automation/kaggle/pre626_build_signed_v49_bmw_attr_diag.py` e workflow `.github/workflows/nfsmw-pre626-v49-bmw-attr-signed.yml`, **sem request de execução e sem APK produzida**.
- A receita reproduz PRE452/V48 como base, reusa a fonte `sub_823E5988` autenticada, adiciona o único callback PRE622 após `REX_LOAD_U32`, mantém PRE429, PRE447, Nitro PRE398, áudio/SDL/input/PG9076, shaders, texturas e física original.
- **Gate obrigatório antes de tocar credenciais:** `docs/PRE625_BMW_HOST_ATTR_ARM64_NATIVE_LINK_RESULT.json` deve ser `AUDIT_OK`, provar ARM64 ELF real e os quatro símbolos corretamente vinculados. Se ausente ou falho, a PRE626 deve bloquear; não executar manualmente saltando o gate.
- Caso a build seja autorizada depois, prevê `versionCode 49`, APK nova `NFSMW_V49_PRE626_BMW_ATTRIBUTE_VALUE_DIAGNOSTIC.apk`, **mesmo package `io.github.nfsmwrecomp` e mesmo certificado permanente**, sem debug signer. A receita verifica marcador de Nitro e quatro símbolos no `libmain.so` da APK assinada; `--upload` só após verificação.
- **PRE626 NÃO compilada, NÃO assinada, NÃO instalada, NÃO testada no Galaxy**, ganho de FPS e melhorias compráveis continuam inexistentes/não demonstrados. Mesmo uma compilação bem-sucedida seria diagnóstica.

## Próxima ação e preservações

1. Checar o [run PRE625 42705397176](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42705397176) e metadados `docs/PRE625_BMW_HOST_ATTR_ARM64_NATIVE_LINK_RESULT.json`. Se falhar, corrigir com base no motivo real, não assumir prova ARM64.
2. Se PRE625 `AUDIT_OK`, revisar segurança, acionar PRE626 pelo GitHub Actions (sem editar assinatura); somente após `apksigner` confirmar cert/release e `versionCode 49` publicar/instruir instalação. Não afirmar resultados de telefone até usuário instalar e testar.
3. Na próxima sessão diagnóstica comparar BMW vs Punto para a **mesma rota e tipo** de atributo, registrando `[NFSMW_PRE622_ATTR_VALUE]`, sem trocar `candidate_count` por números artificiais ou fabricar preços/peças.
4. Manter a V48 e o save NAME, os backups, PRE607 no armazenamento, resolução interna **1920×1080**, meta 120 FPS, todas as configurações gráficas/física, controle iPega PG9076/touch, Nitro PRE398 e proteção térmica. Logs anteriores ainda indicam cap configurado em **60 FPS**; esta etapa não altera cap nem demonstra desempenho superior.
