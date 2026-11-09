# PRE597_HANDOFF_PRE592_DEVICE_LOAD_AND_COUNTER_ONE_BYTE_20261109

**Data:** 2026-11-09, America/Bahia. **Jogo:** Need for Speed: Most Wanted (2005), Xbox 360 USA → Android. **Build:** V48 PRE452, package `io.github.nfsmwrecomp`, key release permanent cert SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.

## PRE592 — resultado positivo no Galaxy S24 FE, confirmado pelo usuário

Após ter aplicado, segundo o contexto da conversa, o candidato PRE592 (nova coleção VLT + `RefSpec` ativo, contador engine `pvehicle=0`), o usuário declarou: **"Consegui carregar"** e anexou um `nfsmw.log`. A saída literal `PRE592_RESULTADO` e os hashes atuais da pasta Android **não** foram fornecidos: a aplicação específica é atribuída pela sequência de execução, não por comparação direta dos bytes do telefone.

O log foi **realmente lido na conversa** a partir do arquivo anexado. Evidências:
- **112.401 bytes, 675 linhas**, SHA256 **`842fbc19031e81adb7988ad3e2fbd2de35850ce19abde581681025c4172ed1b9`**.
- **Uma sessão** interna `2026-11-09 04:27:55.751` até `04:28:14.945` (não misturar com logs anteriores que concatenavam 2–3 sessões).
- Montagem VFS de `/storage/emulated/0/NFSMW_PTBR`, **28 entradas**, só leitura, às `04:27:56.513`.
- Quatro aberturas bem-sucedidas `XamContentCreate` do contêiner `MARCEK` **62.688 bytes**, todas `resultado 00000000`, às `04:28:07.168`, `04:28:07.734`, `04:28:07.784`, `04:28:10.911`. Cópias ao diretório interno `saves/MARCEK/actual`. A **confirmação de carreira realmente carregada** é fornecida pelo usuário, não inferida apenas dos códigos de abertura.
- **Não contém** linhas `[error]`, `[critical]`, `[fatal]`, nem eventos `NFSMW_PRE292_BMW_MENU` ou `NFSMW_PRE429_ENTRY`. **Não afirmar que a oficina BMW foi visitada nesta sessão**, nem que upgrade foi comprado, instalado ou persistido.
- `D:\\GLOBAL\\ATTRIBUTES.BIN` falhou como arquivo avulso por `0xc000000f`, e há leitura `NFS\\ZZDATA4.BIN` de **5.018.060 bytes em offset 37.898.240**; **não há no log a leitura explícita do VPAK alterado em offset 0**. Portanto, não há prova independente de hash/runtime do VPAK ou de lookup da nova coleção, apesar do sucesso de entrada na carreira.
- Renderização interna **1920×1080**, cap **60 FPS efetivos na configuração do log**, versus meta 120 FPS. Nenhuma medição de ganho ou mudança gráfica; sem edição de controles térmicos.
- O arquivo completo de log permaneceu anexo no chat e **não foi publicado no GitHub**.

## PRE596 — prova de isolamento da diferença binária

- [GitHub Actions run 42580244909](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42580244909), `AUDIT_OK`; resultado `docs/PRE596_BMW_COUNTER_ONE_BYTE_GUEST_SEMANTICS_READONLY.json`. Primeiro run 42580158603 falhou **somente** por marcador textual não coincidente; corrigido e rerun passou. Não houve patch novo nem alteração em arquivos do jogo ou save.
- Base PRE501/PRE502/PRE591 autenticada: VPAK candidato PRE591, **698.004 bytes**, SHA256 **`b84d1ec037b656063ded48f8ea1e075d6c8425ba438e6366d301fc308c7c9358`**, contador BMW motor 0, `RefSpec` ativo com 2 entradas; VPAK PRE502 combinado/ PRE573, **698.004 bytes**, SHA256 **`d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6`**, mesmos layouts/referências, contador BMW motor 1. Builder PRE591 prova que **só difere o byte absoluto 256619** no VPAK (último byte de inteiro big-endian 32 bits no offset 256616, BIN-relative 256488). O ZDIR/checksum EA externos foram atualizados independentemente para as variantes.
- O BMW M3 GTR no VPAK original tem limite engine 0 e RefSpec de 1 entrada; o Fiat Punto original tem limite engine 4 (PRE473/PRE474). A PRE591 mantém RefSpec estendido (2) e count=0, e foi compatível com carregamento; o conjunto com count=1 (PRE573) gerou aviso `MARCEK está corrompido`.
- **Inferência forte porém não causalidade definitiva:** elevar o contador para 1, ou o caminho de resolução/uso da nova segunda referência quando o contador se torna positivo, é o gatilho candidato. O erro **não prova corrupção permanente do save**. PRE490 ainda não demonstra semântica real `GetMaxLevel`, `SetLevel`, `SetPackage`. O identificador da coleção nova não estava na StrE original (PRE499); não sabemos se o convidado exige registro de nome para resolver a coleção.
- **Não reaplicar PRE573**: o experimento combinado com motor 1 já falhou. Próximo gate deve auditar código guest/lookup de `pvehicle`, `GetMaxLevel/SetLevel` e `StrE`/Export para uma segunda coleção válida, antes de preparar outro teste de dispositivo.
- **Não promover a tunagem como implementada**: compra no FE, instalação, ganho físico real e persistência continuam não verificados.

## Estado atual e próximo passo

- PRE592 **aparentemente ainda aplicado** no telefone conforme relato; não afirmar que o usuário já restaurou. Antes de qualquer novo patch, fechar a V48 e executar **apenas uma vez**, mediante estado confirmado, `pre592_restore_bmw_refspec_pointer_only_shevery.sh` em `/storage/emulated/0/NFSMW_PTBR`; exigir `PRE592_RESTORE=ORIGINAIS_VERIFICADOS`. Se o usuário continuar usando a V48 como está, não trocar automaticamente os dados.
- Preservar backups `ZDIR.BIN.pre592_original_backup` e `ZZDATA4.BIN.pre592_original_backup`, a tradução original PT-BR, o histórico, V48 e certificado permanente, Nitro PRE398, PG-9076/touch, 1920×1080, shaders/efeitos/física geral e proteção térmica. Meta cap 120 FPS; log atual mostra 60.
- O usuário antes liberou não exigir isolamento de save e disse que poderá criar outro depois; **não apaga MARCEK automaticamente**.

**Status:** PRE592 loaded career `USER_CONFIRMED`; PRE596 read-only one-byte delta `AUDIT_OK`; guest lookup and BMW tunability **PENDENTES**.
