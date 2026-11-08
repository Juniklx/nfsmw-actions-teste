# PRE498_BMW_ENGINE_PROFILE_HANDOFF_20261108

**Data:** 2026-11-08  
**Projeto:** NFSMW Xbox 360 PAL recompilado para Android, repositório privado `Juniklx/nfsmw-actions-teste`, contexto canônico `CONTEXTO_NFSMW.md` Google Drive.  
**Objetivo do usuário:** habilitar tunagem de desempenho comprável e persistente na BMW M3 GTR de carreira.  
**Estado atual:** feature ainda DESLIGADA, nenhum hook/runtime ativo, nenhuma V49 produzida. **Manter V48 PRE452 estável, Nitro PRE398, controles PG-9076, assinatura de release, shaders e save `MARCEK`.**

## PRE490 — auditoria de funções PAL concluída, relatório recuperado
- Audit original [GitHub Actions #42517016343](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42517016343) processou com **`AUDIT_OK`** o backup PRE99 (SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`, 874.780.689 bytes), 129 fontes, 56.338 funções; coletou metadados de 13 funções PPC convidadas: `sub_823E5B08`, `sub_823E6560`, `sub_823E67E8`, `sub_823E5988`, `sub_82582F70` etc.
- O *workflow* original concluiu como **failure** porque o `git push` do relatório foi rejeitado como non-fast-forward, devido a commits concorrentes. O processamento do analisador foi bem-sucedido, sem erros de origem ou exceções. Os logs mostram `PRE490_STATUS AUDIT_OK`, `PRE490_FUNCTIONS 13`.
- **PRE496** recuperou o relatório exato a partir do artefato GitHub Actions ID **13632775377**, verificado SHA-256 do arquivo JSON `e33fce658a44f6b8a5e9e10466241e9cc48a26a0d234177d18d540c94c1c77a7`, sem baixar novamente 875 MB. Workflow [42519024623](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42519024623) `AUDIT_OK`; relatórios `docs/PRE490_PAL_FUNCTION_ARGS_RETURNS_READONLY.json` (13 alvos) e `docs/PRE496_PRE490_REPORT_RECOVERY.json`.
- **Não houve identificação semântica definitiva** de `Physics::Upgrades::SetLevel`, `SetPackage` ou `GetMaxLevel`; possíveis papéis das funções continuam hipóteses. Endereços do PC v1.3 não são endereços PAL Xbox.

## PRE494 — realocação segura do RefSpec do motor, em RAM
- Workflow [42518547338](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42518547338) `AUDIT_OK`, script `automation/kaggle/pre494_bmw_engine_scratch_refspec_relocation.py`, relatório `docs/PRE494_BMW_ENGINE_IN_MEMORY_REFSPEC_RELOCATION.json`.
- VPAK original `GLOBAL\\ATTRIBUTES.BIN` SHA-256 `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad`, 697.856 bytes. Geometria original: BIN offset 128, comprimento 354.959; VLT offset absoluto 355.136, comprimento 342.720.
- **Existem 49 bytes de padding zero entre BIN e VLT.** Em cópia RAM, array `engine` BMW `bmwm3gtr` de capacidade 1, count 1 e 20 bytes original no BIN relativo `256660` foi representado por novo array de 32 bytes no BIN relativo **354960**; tamanho declarado do BIN mudou somente na cópia de 354959 para **354992**, VLT não foi deslocado, sobraram 16 bytes de padding.
- A edição da cópia atualizou **uma única entrada PtrN** VLT→BIN, validando o reparsing pelo parser original. Todas as regiões fora de cabeçalho BIN, padding original e destino desse PtrN foram byte-exatas. Somente **23 bytes** da cópia sofreram alterações; arquivo em disco NÃO foi escrito.
- **A segunda referência do teste duplicava a física STOCK:** teste estrutural, não cria upgrade físico e não prova aceitação do loader Xbox.

## PRE495 — comparação de motores originais da BMW, em RAM
- Workflow [42518728013](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42518728013) `AUDIT_OK`; `docs/PRE495_BMW_ENGINE_ORIGINAL_DONOR_COMPARE_READONLY.json`.
- É possível fazer o array BMW apontar a duas coleções **originais existentes da classe `engine`**: `bmwm3gtr` (hash `cd88083f`) e `m3gtre46careerstart` (`39dae0f8`), com validação de referências, árvores de herança e PtrN, apenas na cópia RAM.
- Foram lidas curvas TORQUE[9] originais (unidades do campo não medidas em corrida): `bmwm3gtr` = **[149,179,222,266,283,275,255,235,228]**; `m3gtre46careerstart` = **[87,128,174,219,239,231,210,192,179]**. A variante de prólogo tem torque menor nas **9/9 amostras**; máximos 283 contra 239. **Não utilizar o perfil `careerstart` como upgrade de potência da BMW**, embora o teste de vinculação tenha passado.
- Não foram modificados contadores, VPAK real, Nitro, APK nem save.

## PRE497 — primeiro protótipo de perfil de motor BMW com torque superior
- Workflow [42519183600](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42519183600) `AUDIT_OK`; script `automation/kaggle/pre497_bmw_engine_torque_endpoint_synthetic.py`, relatório `docs/PRE497_BMW_TORQUE_ENGINE_SYNTHETIC_ENDPOINT.json`.
- Criada função que clona o layout autêntico da classe `engine` da `bmwm3gtr`, **96 bytes**, modifica somente os nove `float32` BE de `TORQUE` (offset +8 até +43) e revalida byte a byte que todos os outros campos e o cabeçalho do array são preservados. Dados do motor inicial autenticados pelo SHA `e09efe8e63d0971da0949e898dbf8ba1b03c2954d2da04db48e9e56cb6437471`.
- Vetores apenas matemáticos de laboratório: ganho 0% preserva SHA original, +5% dá pico 297,15, +10% dá pico 311,30 comparados ao pico original 283. O valor foi aplicado a cada uma das nove amostras. **Os percentuais 5/10% não são uma escolha ou requisito fornecido pelo usuário; não são uma calibração definitiva.**
- Nenhuma coleção nova `engine` foi criada na VLT, nenhuma ref BVM foi integrada ao jogo, nenhum `pvehicle.*_upgrades` foi alterado, nenhum arquivo de jogo nem save foi escrito. Nenhum aumento de HP ou aceleração em runtime foi medido.

## Caminho técnico de implementação, evitando regressões
1. **Criar uma coleção independente de `engine` com identidade BMW específica** na cópia dos atributos, contendo o layout final. Não usar `m3gtre46careerstart` porque a física dele é mais fraca e alterá-lo globalmente afetaria a variante do prólogo.
2. O novo bloco de física ocupa 96 bytes, além do array de 32 bytes. O padding original de 49 bytes sozinho **não comporta as duas novas estruturas**: será necessário validar alocação, crescimento/reempacotamento dos BIN/VLT, exportação `ExpN`, PtrN e tamanho do recurso. Não sobrescrever coleções existentes nem arquivos V48.
3. Só ativar um `engine_upgrades>0` da BMW após garantir que o original PAL tem as mesmas semânticas de leitura e interpolação observadas no código PC v1.3. A PRE491 prova apenas **compatibilidade estrutural/matemática**, não comportamento de runtime Xbox.
4. Testar a ligação real do carro tipo41 à coleção `bmwm3gtr`, os valores de catálogo, o preço, a aplicação física, compra, reabrir jogo e persistência em **save descartável**. Preservar Nitro PRE398, V48 e save `MARCEK`. A guarda PRE479 e transação PRE483 permanecem OFF.
5. Não produzir APK V49 funcional nem afirmar mod concluído antes desses testes. Usar GitHub Actions e Google Drive automaticamente sem pedir ao usuário para abrir navegador.

## Proveniência e verificabilidade
Todos os resultados anteriores foram registrados em relatórios privados de metadados; o arquivo PAL/USA correspondente foi autenticado conforme PRE467. A plataforma PC foi consultada apenas como hipótese matemática. **PRE494–PRE497 são testes em RAM que NÃO criaram uma tunagem utilizável.**
