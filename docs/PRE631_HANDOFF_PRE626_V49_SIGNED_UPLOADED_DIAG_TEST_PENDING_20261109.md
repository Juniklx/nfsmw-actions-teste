# PRE631 — PRE626 V49 diagnóstica assinada e publicada; teste no Galaxy pendente (2026-11-09)

## Resultado comprovado
- A execução PRE626 GitHub Actions 42709319413, https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42709319413, terminou completed/success em 2026-11-09T22:36:39Z.
- O arquivo pre626-v49-report.json do artefato GitHub 13716742145 traz status PRE626_V49_SIGNED_ATTR_DIAGNOSTIC_VERIFIED, signed_apk_verified=true, permanent_certificate_verified=true, pre626_signed_all_four_callbacks_verified=true e drive_upload_success=true.
- A APK do mesmo artefato tem 47.103.605 bytes, SHA-256 0fad0c82d9ef5ff591c7f23b32fdab513fe16483756e32a6dd4aab5d4f18447a e MD5 395c60462ddeec7fc0b4648016ea32e0. Ambos os hashes foram calculados diretamente a partir do arquivo extraído; o SHA-256 confere com o relatório. ZIP do GitHub: SHA-256 c61a7c31691572761e8baa7a79f16c5176237bc3bcc0ee50055ecb4e9205cbc4.
- APK no Google Drive em NFSMW_Android/02_APKs/: https://drive.google.com/file/d/1sa__qEk1t6ZF2_qrgy9MZEx6G4ixZpkh/view , ID 1sa__qEk1t6ZF2_qrgy9MZEx6G4ixZpkh; nome NFSMW_V49_PRE626_BMW_ATTRIBUTE_VALUE_DIAGNOSTIC.apk, 47.103.605 bytes, pasta confirmada por metadados. PRE631 ainda verifica MD5 remoto antes da atualização canônica.
- Package io.github.nfsmwrecomp, versionCode 49, certificado PERMANENTE SHA-256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Nunca criar chave nova nem usar assinatura debug.
- Libmain ARM64 contém NFSMW_PRE429_ENTRY, NFSMW_PRE429_LEVEL, NFSMW_PRE447_ROUTE, NFSMW_PRE622_ATTR_VALUE e NFSMW_PRE398_GLOBAL_NITRO_FULL. O relatório de llvm-nm confirma exportação única de cada callback NFSMW_PRE429_TRACE_ENTRY, NFSMW_PRE429_TRACE_LEVEL, NFSMW_PRE447_ROUTE e NFSMW_PRE622_ATTR_VALUE. O logger PRE622 limita o registro a 128 linhas, sem carga de memória guest adicional.
- V49 NÃO cria pacotes de tunagem, não altera candidate_count, arquivos do jogo, preços nem saves. Nitro PRE398, SDL, touch/PG-9076, shaders e física foram preservados pelos gates de build; regressões funcionais precisam de teste físico.

## Teste ainda pendente
- V49 assinada e publicada, mas NÃO instalada/testada no Galaxy S24 FE; nenhum ganho FPS ou tunagem real confirmado. V48 PRE452 segue última versão funcional informada no aparelho.
- PRE607 permanece aplicada aos ZDIR.BIN/ZZDATA4.BIN ativos no S24 FE segundo hashes enviados pelo usuário. Não repatchar nem restaurar. Preservar perfil NAME com BMW M3 GTR normal já importada via PRE614.
- Último log V48/PRE617: BMW type=41 com Motor 0, Transmissão 0, Suspensão 0, Nitro 3, Pneus 0, Freios 0, Indução 0. Usuário viu Option Title nas seis categorias sem valor positivo. O motivo não está resolvido.
- Próximo gate após instalação V49 sobre V48: confirmar abertura, touch, PG-9076, Nitro, abrir oficina BMW e Fiat Punto sem comprar peças, salvar nfsmw.log novo. Correlacionar [NFSMW_PRE622_ATTR_VALUE] (caller/category/addr/value) com [NFSMW_PRE447_ROUTE] e [NFSMW_PRE429_LEVEL], identificando valores que geram zeros BMW e positivos Punto. Se limite de 128 linhas for atingido, marcar telemetria incompleta; não inventar ausência de valores.
- Preservar 1920×1080, meta 120 FPS (logs V48 exibem cap 60), gráficos/efeitos/shaders/física, controle PG9076/touch, Nitro PRE398, proteções térmicas, saves, PKCS12 e credenciais.
- Diferenças entre compilação, assinatura e teste de jogo são explícitas: somente as duas primeiras e o upload remoto estão comprovados.
