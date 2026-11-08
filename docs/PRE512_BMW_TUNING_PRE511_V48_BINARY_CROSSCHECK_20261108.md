# PRE512_BMW_TUNING_PRE511_V48_BINARY_CROSSCHECK_20261108

**Data:** 2026-11-08. **Projeto:** NFSMW Most Wanted 2005 Xbox 360 recompilado Android. **Objetivo:** desenvolver tunagem comprável/instalável/persistente para a BMW M3 GTR da carreira preservando o comportamento de V48 e todo o restante. **Estado:** feature OFF; nenhuma V49, nenhum patch de VPAK/ISO/ZIP, nenhum novo teste de jogo nem save alterado nesta etapa.

## PRE511 — cruzamento entre PRE509 histórica e APK V48 PRE452 assinado ORIGINAL

- GitHub Actions: [run 42526012913](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42526012913), `AUDIT_OK`; relatório `docs/PRE511_ORIGINAL_V48_APK_RUNTIME_MARKERS_READONLY.json`.
- APK original autenticado pelo **SHA-256 completo**, sem reempacotar ou assinar: Drive `NFSMW_V48_PRE452_BMW_ZERO_ROUTE_DIAGNOSTIC.apk`, ID `1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C`, **47.104.233 bytes**, SHA-256 `c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35`. A PRE511 validou o ZIP do APK e inspecionou ELF ARM64 **somente em memória**.
- `lib/arm64-v8a/librexruntime.so`: **9.098.232 bytes**, SHA256 `64a48c36e4046fd52b332ef185b4d21f006d5fcab72f4d86d41fbed72052d055`. Contém **uma ocorrência** de cada uma das mensagens de referência `game_data_root es una imagen de disco`, `Runtime::SetupVfs: game_data_root does not exist`, `Failed to initialize game data device` e `Failed to register host path device`. Contém marcas `HostPathDevice` (**21**), `DiscImageDevice` (**24**), `allow_game_relative_writes` (**2**) e `game_data_root` (**5**). Essas ocorrências corroboram a presença do mecanismo de montagem PRE509 no **binário efetivamente distribuído V48**.
- Outros ELF autenticados no mesmo APK: `libmain.so` 41.768.224 bytes SHA `f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3`; `libmain_usa.so` 41.749.696 bytes SHA `4f32de8f2ff10d4748aa33f208774038ef9bfa402eacc61a49dd7e70f3b1bc83`; `libfile_redirect_hook.so` 4.032 bytes SHA `9f0037be0c6e917e0c0cf420c786a829ad3a3a685778850d75fa069564ce043c`. O hook não contém os marcadores pesquisados, o que **NÃO** comprova que esteja ativo ou inativo.
- `librexruntime.so` não contém `ZDIR.BIN` nem `ATTRIBUTES.BIN` como sequências ASCII nos marcadores testados. Ausência de string literal **NÃO** prova ausência de suporte; essas referências podem estar no código guest, por hash, por recurso ou por outra forma de acesso.

## Inferências limitadas pela evidência

1. A PRE509 (fonte PRE99) encontrou `Runtime::SetupVfs` criando `HostPathDevice` para uma pasta, e `DiscImageDevice` para arquivo regular/URI de conteúdo Android, com `allow_game_relative_writes` false por padrão; a PRE511 demonstra que as mesmas mensagens e nomes aparecem na biblioteca ARM64 **V48 distribuída**. **Isso é corroboração estática**, não demonstra qual ramo executou no Galaxy S24 FE.
2. A entrada para jogo por pasta poderia permitir testar **cópia/overlay independente** de arquivo apenas após comprovar a seleção ativa da V48 e todos os detalhes do carregador, preservando os dados do usuário. Não instalar patch nem sobrescrever `ZZDATA4.BIN` ou `ZDIR.BIN` original.
3. O VPAK PRE502 com segundo motor BMW e contador nível 1 continua exclusivamente **experimento estrutural em RAM**. O ganho sintético +5% é vetor de teste, não tuning escolhido nem resultado de FPS/torque medido no aparelho.

## Próxima decisão técnica

- Procurar evidência **do runtime real da V48**, idealmente logs da própria V48 indicando `Runtime::SetupVfs` e a modalidade de origem efetivamente montada, ou metadados da seleção atual que permitam distinguir pasta de imagem/URI sem depender de /proc/maps.
- Se a modalidade em V48 for pasta, estudar um mecanismo de teste reversível que **não altere o conjunto original de arquivos do usuário**. Caso seja imagem/URI, estudar a camada `DiscImageDevice` antes de qualquer hipótese de alteração de arquivo.
- Identificar o carregador guest `ZDIR/ZZDATA/VPAK` e o significado do checksum ZDIR (campo original `0x296ad9ed`, que não é CRC32 calculado sobre os bytes VPAK). Não editar arquivos antes de identificar as verificações aplicadas.
- **Somente depois** validar instalação, preço/catalogação `FECarPartInfo`, funções guest `Physics::Upgrades`, identidade BMW tipo41, desempenho em corrida e persistência, usando **save descartável**, mantendo Nitro PRE398, PG-9076/touch, gráficos/física, 1920×1080, cap 120 FPS, limites térmicos, chave/certificado release permanente e save MARCEK. PRE479/PRE483 seguem OFF.

**Segurança:** PRE511 não executou código guest nem jogo no Android, não leu chave de assinatura, não gravou arquivos do jogo, não instalou APK e não alterou saves. O APK V48 permanece byte-exato.
