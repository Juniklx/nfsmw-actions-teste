# PRE717 — Auditoria lexical do fallback de instância Vulkan na V51 (2026-11-12)

## Evidências verificadas
- GitHub Actions: [run 43280564101](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43280564101) concluída com `success`; artefato `13974095194` contém os JSONs `PRE717_V51_KAGGLE_VALIDATED_SUMMARY.json` e `NFSMW_PRE717_KAGGLE_REMOTE.json`.
- Cópia preservada no [Google Drive](https://drive.google.com/file/d/1SJswr7Ib45bW8LP4AZ5znoR_NpUkMCnb/view): `NFSMW_PRE717_REAL_KAGGLE_VERIFIED_43280564101.zip`, 34.376 bytes, SHA-256 `3b26ffaac23c102c85f422f5166eac93b882575e02552149db38c60b5ee32555`; readback byte a byte comparado com o ZIP original: idêntico.
- Fontes V51 autenticadas pela receita PRE704/PRE99. `vulkan_instance.cpp` SHA-256 `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`.
- `vkCreateInstance` ocorre lexicalmente nas linhas 523 e 537; chamadas com três argumentos textualmente idênticos (SHA-256 de argumentos `6e6d4abda4348a13b95cb47349c5f5b338d05cf7edc03e03b7b3f73a7522d353`).
- Condição da linha 525 contém os tokens `VK_ERROR_EXTENSION_NOT_PRESENT` e `VK_ERROR_LAYER_NOT_PRESENT`. Na linha 528, `for` de intervalo sobre a coleção lexicalmente declarada `std::vector<bool*>` na 356; linha 529 escreve `false` ao ponteiro da variável iterada. `enabledExtensionCount` aparece na linha 535, antes da segunda chamada; a linha 540 contém condição com `VK_SUCCESS`.
- No recorte 516–540, a análise PRE717 **não identificou referências lexicais a `ppEnabledExtensionNames`**, mas a análise do vetor, de atribuições e do campo aponta para a próxima auditoria.

## Limitações explícitas
A análise é **lexical**, sem AST/CFG C++ completos. O mecanismo de recuperação, a condição realmente tomada, o estado final de extensões Vulkan, a validade temporal de `std::vector::data()` e a identidade fonte→ELF da APK V51 **não foram provados**. O relatório marca `actual_recovery_semantics_proven=false` e `runtime_retry_observed=false`. Não houve build de APK, modificação de fontes, acesso a credenciais, alteração de certificados ou ganho de FPS medido. `VK_GOOGLE_display_timing` permanece não confirmada como habilitada em execução.

## Próxima etapa
PRE718: examinar as operações de `ppEnabledExtensionNames`, `enabledExtensionCount` e do vetor de nomes de extensão entre as chamadas 523/537, com fonte autenticada e sem exportação do código completo. Qualquer risco de ponteiro obsoleto é hipótese até existir evidência de controle de fluxo e validade real dos apontadores.

**Base preservada:** Android V51, mesmo pacote e certificado permanente; nenhuma V52, nenhuma alteração de resolução 1920×1080, efeitos, texturas, sombras, física, iPega PG-9076, touch ou políticas térmicas.
