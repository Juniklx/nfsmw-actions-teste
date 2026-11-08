# PRE504_BMW_ENGINE_INTEGRATION_CHECKPOINT_20261108

**Data:** 2026-11-08. **Projeto:** NFSMW Xbox 360 PAL recompilado para Android. **Objetivo:** tunagem real de desempenho na BMW M3 GTR da carreira; permitir instalar/comprar níveis de motor, com física e save persistentes. **ATENÇÃO:** V48 PRE452 continua original e funcional; nenhum APK V49 foi gerado, e `MARCEK`, Nitro infinito PRE398, controles PG-9076 e outras funções permanecem intactos.

## PRE499 — regra de identidade de coleção e arquivo autêntico
- Workflow [42521869514](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42521869514): `AUDIT_OK`. Relatório `docs/PRE499_BMW_ENGINE_COLLECTION_REPACK_PREFLIGHT.json`.
- A comparação do código de hash VaultLib identificou a regra exata de identificação de exportação para as duas coleções originais de motor: `hash32("engine/bmwm3gtr")=0xda48882c` e `hash32("engine/m3gtre46careerstart")=0xf5ae15da`. Não é igual ao hash isolado do nome do carro. A nova coleção experimental `bmwm3gtr_upgrade_engine_pre499` usa hash `0x33b0fa80` e exportação derivada `0x61ade503`.
- VLT autêntico: `DatN` 164.784 bytes (sem espaço no final), `ExpN` 48.000 bytes e 2.399 exportações originais, `PtrN` 129.872 bytes; 2.339 coleções. `CollectionLoad(engine,bmwm3gtr)` possui 36 bytes no VLT, incluindo descritor e um registro de tipo, e o ponteiro aponta ao bloco físico de 96 bytes no BIN.
- A nova identidade não consta do StrE original; **não está provado que o loader PAL aceite coleção sem string registrada**. Nenhuma mídia foi modificada.

## PRE500 — coleção BMW física independente totalmente reconstruída em RAM
- Workflow [42522238585](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42522238585): `AUDIT_OK`; relatório `docs/PRE500_BMW_ENGINE_FULL_VPAK_SCRATCH_REBUILD.json`.
- Construiu uma cópia efêmera do VPAK original de 697.856 bytes para 698.004 bytes, contendo uma **nova coleção engine só para a BMW** e um perfil físico de motor experimental de +5% na curva TORQUE[9]. O ganho é vetor de teste matemático, **não escolhido pelo usuário**, nem ganho de potência medido no jogo.
- Recompôs `DatN`, `ExpN` e `PtrN`, acrescentando a coleção física, um registro de exportação e um ponteiro para o bloco físico; redirecionou somente a referência engine do pvehicle BMW para um array de duas entradas, estoque e novo motor. Validação independente releu 2.400 exportações e 2.340 coleções; todas as 2.399 exportações e 2.339 coleções originais permaneceram byte-exatas/recuperáveis, e o motor `careerstart` não foi modificado.
- Nenhum asset foi publicado, nenhuma imagem binária foi gerada em disco, nenhum save nem APK foi alterado.

## PRE501 — contador de nível exclusivamente da BMW
- Workflow [42522448262](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42522448262): `AUDIT_OK`; `docs/PRE501_BMW_ENGINE_ONE_LEVEL_COUNTER_SCRATCH.json`.
- Campo físico PAL pvehicle `bmwm3gtr.engine_upgrades`: BIN relativo **256488**, `int32` big-endian, original 0. Testou exclusivamente 0 → 1 em RAM e revalidou outras seis categorias, Nitro original =3, Punto =4 no motor, `m3gtre46careerstart`=0 no motor, sem modificações.

## PRE502 — conjunto completo em uma única cópia in-memory
- Workflow [42522672553](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42522672553): `AUDIT_OK`; `docs/PRE502_BMW_ENGINE_FULL_LEVEL1_COMBINED_SCRATCH.json`.
- Repetiu a reconstrução VPAK da PRE500 **com engine_upgrades=1 na mesma cópia**, mantendo todas as demais condições invariantes. Classe engine original, segundo bloco de torque, novo `CollectionLoad`, `ExpN`, `PtrN`, array `RefSpec[2]` e limite de nível 1 juntos no VPAK experimental. Todos os registros de origem, recursos e carro de prólogo preservados.
- É a primeira **integração estrutural completa em memória**, **não** executada pelo Xbox PAL nem pelo Android e sem catálogo de loja, compra real, teste de física ou gravação em save. Não declarar que a tunagem já funciona. Feature `safe_to_enable_or_build_tuning=False`.

## PRE503 — espaço reservado no pacote ISO original e checksum
- Workflow [42522826803](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42522826803): `AUDIT_OK`; `docs/PRE503_XBOX_ZZDATA_ATTRIBUTE_SECTOR_SLACK_READONLY.json`.
- O recurso do arquivo `ZZDATA4.BIN` da **ISO USA de referência** ocupa 697.856 bytes em **341 setores de 2.048 bytes** (698.368 bytes reservados). Os **512 bytes de padding seguintes são zeros reais**, sem sobreposição do próximo recurso. A cópia PRE502 cresceria 148 bytes e deixaria 364 bytes livres. **Esse dado refere-se somente à ISO USA consultada, não comprova alocação idêntica do ZIP PAL nem do pacote Android.**
- O registro ZDIR correspondente precisa de atualização de tamanho caso haja futura substituição. Campo checksum original `0x296ad9ed` **não coincide** com `zlib.crc32` do VPAK original `0xb73ff1d9`. Não assumir CRC32 nem alterar registro até identificar sua semântica ou provar que é irrelevante. A ferramenta NÃO alterou ZDIR, ZZDATA ou ISO.
- Nenhuma compatibilidade do loader V48 para VPAK de tamanho diferente foi demonstrada.

## Próxima etapa: validação de carregador e compra
1. Inspecionar **como V48 carrega os atributos** dentro do pacote Android, usando fonte reprodutível existente em Google Drive/GitHub, sem depender de instalar a versão experimental por cima da V48 estável. Verificar se o nome novo precisa estar registrado na tabela StrE e como o índice `ExpN` resolve `engine/bmwm3gtr_upgrade_engine_pre499`.
2. Investigar significado do checksum ZDIR e diferença da mídia PAL versus referência USA para propor forma correta de empacotar o novo recurso sem sobrescrever ROM original ou arquivos pessoais.
3. Confirmar no runtime PAL os métodos de `Physics::Upgrades::GetMaxLevel`, `SetLevel` e `SetPackage`, a identidade do carro `type=41` ↔ `bmwm3gtr`, títulos, preços e nível na oficina. Todas as verificações de menu precisam usar dados reais, não placeholders, e `GetPerfPackageCost` não pode aceitar ausência de FEPartInfo como preço válido zero.
4. Se confirmado, construir apenas APK EXPERIMENTAL reversível, separado de V48, mantendo assinatura release e testando exclusivamente em save descartável. Preservar `MARCEK`, Nitro PRE398, PG-9076 e outras correções.

**Proveniência:** SHA-256 do `GLOBAL\\ATTRIBUTES.BIN` original PAL/USA validado para ESTE ARQUIVO: `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad`. Os novos dados resultam de ensaios exclusivamente em memória e relatórios privados. **Nenhum arquivo de jogo modificado foi gerado, distribuído ou aplicado ao dispositivo.**
