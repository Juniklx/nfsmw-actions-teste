# PRE593_HANDOFF_PRE587_GUEST_SUCCESS_PRE591_REFSPEC_ONLY_GATE_20261109

**Data local:** 2026-11-09 (America/Bahia). **Projeto:** NFSMW-Recompiled-Mobile, Xbox 360 USA 2005 → Android, APK V48 PRE452, pacote `io.github.nfsmwrecomp`, BMW M3 GTR carreira type 41.

## PRE587: sucesso no dispositivo (relato + log)

- O usuário relatou **"Agora carregou"**, após ter comunicado que executou a PRE587 no Shevery, e anexou `nfsmw.log`.
- O arquivo recebido foi realmente lido localmente: **454.088 bytes / 2.472 linhas / SHA256 `509900a226ef281ab92a8567d818cb38e5afdb98a434bc77d0216fea384a2957`**. Contém **três sessões**, iniciadas em 01:42:45, 01:58:25 e **02:25:13**; **somente a terceira corresponde ao teste mais recente PRE587**. Não atribuir as leituras do offset 0 da sessão 01:58:25 ao teste PRE587.
- Sessão 02:25:13: montagem de `/storage/emulated/0/NFSMW_PTBR` às 02:25:14.185, somente leitura, **26 entradas**; tentativa `D:\\GLOBAL\\ATTRIBUTES.BIN` -> `0xc000000f` em busca direta; leitura explícita em `NFS\\ZZDATA4.BIN` de **5.018.060 B no offset 37.898.240** às 02:25:15.369. **Nenhum log do recurso inicial de 698.004 B lido explicitamente no offset 0 desta terceira sessão**; não há checksum/hash guest impresso para o candidato novo.
- `MARCEK` de **62.688 bytes** foi aberto quatro vezes com `XamContentCreate ... resultado 00000000`, às 02:25:21.454, 02:25:22.004, 02:25:22.037, 02:25:25.170. O **usuário confirmou o sucesso de carregamento no jogo**, diferente da PRE573 com aviso de corrupção.
- Às 02:25:33.706–02:25:33.841, houve `crear MARCEK`, `XamContentCreate ... modo 2 -> crear (resultado 00000000)`, fechamento e cópia para `saves/MARCEK/actual`. Isso é **atividade real do sistema de saves**, não comprovação de integridade de conteúdo ou instalação de upgrade. Não dizer que o save não mudou.
- Às 02:25:47.320, `NFSMW_PRE292_BMW_MENU callsite=0x82578988 type=41 event=1`; `NFSMW_PRE429_ENTRY ... pvehicle=0x00000000` no mesmo instante. Confirma passagem pelo caminho de interface da BMW, **não** concessão de peças.
- Um `[error]` às 02:25:33.456 indica fallback gráfico: `C3 ... indice de textura en vuelo incoherente ... copia_duplicada=true`; sem nexo causal verificado com o recurso BMW. Zero linhas `[critical]`/`[fatal]`. Resolução interna 1920×1080, cap **60 FPS** observado, meta do projeto 120 FPS sem mudanças aqui.
- Relatório GitHub original deste teste `docs/PRE590_HANDOFF_PRE587_LIVE_UNLINKED_VLT_MARCEK_SUCCESS_20261109.md`.

## Conclusão comparativa PRE579–PRE587

| Variante | Resultado verificado |
| --- | --- |
| PT-BR original, depois de rollback | MARCEK carrega, confirmado pelo usuário |
| PRE573 combinado (coleção VLT nova + RefSpec ativo + pvehicle motor 1 + torque sintético) | Mensagem `MARCEK está corrompido`, observada em captura |
| PRE581 original-layout, apenas nove torques sintéticos BMW | MARCEK carrega, confirmado pelo usuário e por log |
| **PRE587** nova coleção/ExpN/PtrN **sem vincular ao pvehicle** (contador 0 e RefSpec original) | **MARCEK carrega**, confirmado pelo usuário; chega a menu BMW type 41 no log |

**Conclusão controlada:** o novo recurso não vinculado **não impediu** o carregamento do perfil nesta sessão. A causa da PRE573 é mais provavelmente um dos vínculos ativos do `pvehicle`/contador ou uma interação entre eles, mas **não está isolada**. O log não comprova aceitação de todos os exports, compra, instalação, física ou persistência de novos itens.

## PRE591: nova variante de *ponteiro RefSpec somente* e contador motor 0

- [GitHub Actions run 42567684579](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42567684579), `AUDIT_OK`; `docs/PRE591_BMW_REFSPEC_POINTER_ONLY_PRIVATE_METADATA.json`.
- Partiu do candidato PRE586 (reconstruído e autenticado) e reativou **somente o ponteiro `RefSpec`** da BMW, que agora aponta ao array stock+novo (destino `355056`); preservou **contador `pvehicle` de upgrades motor 0**. São exatamente **3 bytes alterados** contra PRE586 nos offsets de VPAK **642333–642335**, sem outros diffs. Contra PRE502 combinado, é diferente apenas no byte do contador em **256619**. A nova coleção VLT continua presente, mas não há upgrade comprável.
- Candidato VPAK 698.004 bytes SHA256 **`b84d1ec037b656063ded48f8ea1e075d6c8425ba438e6366d301fc308c7c9358`**, checksum EA **`98e13bed`**.
- Pasta Drive privada: https://drive.google.com/drive/folders/1uCdI3KIIV6OPnlIXMaDLSW4nzwnhrAZ4
- Fragmentos enviados e lidos novamente após upload:
  - `PRE591_ZDIR_BMW_REFSPEC_POINTER_ONLY.bin`: **33.312 B**, SHA256 **`f5ba2b4d007f7ace0aa63429dd9f973d2b9f4924db1ab9695e5569038b0715da`**;
  - `PRE591_ZZDATA4_FIRST341_REFSPEC_POINTER_ONLY.bin`: **698.368 B**, SHA256 **`6ad6e5748115380ab057e65642b2bad0ce83f74282b4d80dbbc5b71f33c8c12d`**.
- SHA256 do `NFS/ZZDATA4.BIN` **completo** esperado após sobreposição apenas dos primeiros 341 setores em cópia da fonte PT-BR original: **`522e15940379c8b746ab3c77e771fd22352b0b408cbf6264cf64e99f8a378c29`**. O ZIP original foi verificado com streaming do membro completo e o resto da árvore traduzida não foi alterado. **Não substituir ZZDATA4 completo pelo fragmento!**
- Execução guest/telefone PRE591 ainda **pendente**. Arquivos gerados no Drive somente; não leram nem modificaram o Galaxy S24 FE.

## PRE592: scripts de aplicação/rollback específicos e validação estática

- [Run 42567884850](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42567884850), relatório `docs/PRE592_SHEVERY_REFSPEC_POINTER_ONLY_STATIC_PREFLIGHT_RESULT.json`, `AUDIT_OK`: sintaxe de ambos os scripts, hashes exatos, recusa de arquivo falso sem escrever, recusa de rollback sem backup.
- Scripts:
  - `automation/device/pre592_apply_bmw_refspec_pointer_only_shevery.sh`
  - `automation/device/pre592_restore_bmw_refspec_pointer_only_shevery.sh`
  - Guia `docs/PRE592_MANUAL_BMW_REFSPEC_POINTER_ONLY_DEVICE_GATE_20261109.md`.
- **Antes de executar PRE592**, fechar V48 e **restaurar PRE587 ativa**: `sh /sdcard/Download/pre587_restore_bmw_unlinked_vlt_shevery.sh "/storage/emulated/0/NFSMW_PTBR"`, conferir `PRE587_RESTORE=ORIGINAIS_VERIFICADOS`. Não inferir rollback já executado; é intervenção manual do usuário. O script PRE592 exige os hashes originais de ZDIR e ZZDATA4, 401 MB íntegros, hashes dos próprios fragmentos e espaço para cópia temporária, e salva backups `.pre592_original_backup`.
- Depois do retorno ao original e dos downloads separados em `/sdcard/Download/PRE591`, a aplicação **manual** da PRE592 deve ser opcional e consciente do risco experimental: `sh /sdcard/Download/pre592_apply_bmw_refspec_pointer_only_shevery.sh "/storage/emulated/0/NFSMW_PTBR" "/sdcard/Download/PRE591"`. Aguarda-se `PRE592_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS`. Abrir V48 e testar a mesma carreira e menu BMW, salvar log; não afirmar tunagem ou compra. Restaurar depois com `pre592_restore_bmw_refspec_pointer_only_shevery.sh` e exigir `PRE592_RESTORE=ORIGINAIS_VERIFICADOS`.
- O usuário aceita criar save novo depois; isso dispensa exigência de isolamento, mas **não manda apagar `MARCEK`**. O jogo realizou operação de save na última sessão PRE587, preservação byte a byte de dados não foi testada.

**Preservações:** V48 PRE452 package `io.github.nfsmwrecomp`, cert permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; Nitro PRE398, PG9076/touch, gráficos/shaders/efeitos, 1920×1080, cap meta 120, física geral, proteções térmicas e backups originais. V49 **não compilada**. Compatibilidade PRE592 no celular **ainda não demonstrada**.
