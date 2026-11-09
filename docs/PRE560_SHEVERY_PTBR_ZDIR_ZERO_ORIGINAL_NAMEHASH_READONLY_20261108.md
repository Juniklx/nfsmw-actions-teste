# PRE560 — análise do resultado do ZDIR traduzido no Shevery (somente leitura)

**Origem:** saída enviada pelo usuário no chat de 2026-11-08 (Bahia). Na pasta extraída de NFSMW V48 PT-BR PAL, ZDIR SHA256 **832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf**, 33.312 bytes.

## Resultado do comando PRE558 recebido
```
PRE558_ZDIR_TRADUZIDO=CONFIRMADO
TOTAL_REGISTROS=1388
ATRIBUTOS_ENCONTRADOS=0
```
**Interpretação restrita:** o método `od -An -v -tu4 | awk` não localizou o identificador nominal original `0x9775379a` em nenhum dos 1.388 registros assumidos de 24 bytes. Isso NÃO comprova ausência do recurso de atributos, exclusão efetiva de registros ou leitura incorreta do jogo. Não herdar o registro original 806 nem o deslocamento 355.932.160 para a tradução.

## Checagens no repositório
- `automation/kaggle/pre461_zdir_candidate_hash_names_readonly.py`: original PAL ZDIR lido com `struct.iter_unpack("<IiIIiI", ...)` e `hname` = DJB2 com início `0xffffffff`, caixa alta, multiplicação por 33.
- `automation/kaggle/pre462_usa_raw_iso_attributes_readonly.py`: tabela original `GLOBAL\\ATTRIBUTES.BIN -> 0x9775379A`, `GLOBAL\\FE_ATTRIB.BIN -> 0x80BE7B63`, `GLOBAL\\GLOBALB.LZC -> 0x4C939B36`, `GLOBAL\\GLOBALB.BUN -> 0x4C937012`, `GLOBAL\\GLOBALA.BUN -> 0x4C815791`. A presença de identificadores em outro arquivo/edição não prova correspondência na pasta traduzida.
- Os hashes SHA-256 do `ZDIR.BIN` e `ZZDATA4.BIN` traduzidos já diferem dos originais, conforme PRE558. A tradução não foi inspecionada remotamente pelo GitHub.

## Próximo diagnóstico
Usar `automation/device/pre560_translated_zdir_bytewise_namehash_readonly.sh` no Shevery: leitura em bytes (`od -An -v -tu1`), reconstituição independente de palavras little-endian pelo `awk`, busca dos cinco hashes de nomes originais e contagem de entradas com archive no intervalo 0..9. A única saída contém indicadores e metadados de registros selecionados, sem caminhos pessoais, sem arquivo bruto ou escrita.

**Garantias:** V48, Nitro PRE398, PG-9076, arquivos PT-BR originais e save MARCEK preservados. BMW ainda não tunável.
