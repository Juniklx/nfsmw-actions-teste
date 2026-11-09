# PRE565_HANDOFF_PRE561_PRE564_PTBR_ZDIR_SECTOR0_BMW_RAM_20261108

**Contexto:** NFSMW-Recompiled-Mobile; V48 PRE452 no Galaxy S24 FE; save `MARCEK` protegido, Nitro PRE398, iPega PG-9076 e baseline gráfico intactos. **Objetivo:** tunagem real da BMW M3 GTR carreira (type=41) com melhorias compráveis, instaláveis e persistentes. Nenhuma APK nova ou alteração dos dados/saves foi realizada neste conjunto.

## Informação diretamente fornecida pelo usuário
- Os dados da edição PAL traduzida para PT-BR são executados por **pasta extraída**, sem ISO.
- O usuário informou a localização do ZIP-fonte no Google Drive: `Nfsmw_android/Traducao_PTBR_2026/NFSMW_PT-BR.zip`.
- Shevery: `NFS/ZDIR.BIN` 33.312 bytes, SHA256 `832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf`; `NFS/ZZDATA4.BIN` 401.068.032 bytes, SHA256 `7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951`.
- Shevery PRE560 encontrou `GLOBAL\\ATTRIBUTES.BIN` como hash `0x9775379a`, registro 805, arquivo 4, setor 0, tamanho 697.856. Cinco hashes conhecidos também foram encontrados.

## PRE561 — ZIP PT-BR autenticado diretamente no Drive
- Workflow [42555184282](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42555184282): `AUDIT_OK`. ZIP Drive id `1M95wS9iqrMI-p328Wual7TreqfaPgdL0`, tamanho 5.416.276.032 bytes; diretório interno ZIP com 50 entradas, SHA256 central directory `8253300ee65d9d921f7965605087e31a2557fa3bbd667401865db9c6fec67222`.
- `NFS/ZDIR.BIN` extraído **somente em RAM** do ZIP através de bytes range HTTP206, SHA256 **igual ao Shevery**. Confirmado `GLOBAL/ATTRIBUTES.BIN`, linha 805: `name_hash=9775379a`, `archive=4`, `sector=0`, `total_field=0`, `size=697856`, `checksum=296ad9ed`. Em **11** registros o setor é zero, **1377** não são zero; o zero é realmente presente no arquivo, não erro do comando do telefone.

## PRE562 — comparação PAL original versus PAL PT-BR
- Run inicial falhou de modo seguro porque havia hashes de nomes repetidos, e foi corrigido para comparar hashes duplicados sem forçar unicidade.
- [42555615911](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42555615911): `AUDIT_OK`. PAL original 1.390 registros, PT-BR 1.388, **1.384 hashes de nome distintos em ambos**; 2 ocorrências a mais de nomes repetidos no original. Nenhum hash distinto exclusivamente presente em uma versão.
- Nos 1.381 nomes com registro único em ambas, todas as linhas têm alguma diferença de campo. Cinco hashes que tinham setor diferente de zero no original têm setor zero na tradução; o próprio `GLOBAL\\ATTRIBUTES.BIN` passa do registro 806/setor 173795 para o registro 805/setor 0.
- A evidência indica **reempacotamento/reorganização física** do índice e dos arquivos, não simples alteração de textos. Os deslocamentos PAL originais não podem ser aplicados à tradução.

## PRE563 — comprovação do recurso traduzido no setor zero
- [42555961126](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42555961126): `AUDIT_OK`. O ZIP PT-BR `NFS/ZZDATA4.BIN` foi lido por streaming DEFLATE estritamente em RAM e conferido pelo CRC32 `a038afed`, tamanho 401.068.032 e **SHA256 completo igual ao resultado do Shevery**: `7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951`.
- Na posição 0 do `ZZDATA4.BIN` PT-BR, os **primeiros 697.856 bytes** SHA256 `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad` são **idênticos byte a byte**, pela igualdade criptográfica do hash, ao `GLOBAL/ATTRIBUTES.BIN` do PAL original. Checksum EA `296ad9ed` igual ao ZDIR.
- Próximo recurso PT-BR inicia no **setor 341**; o espaço de 698.368 bytes da primeira entrada contém **512 bytes zero** entre o recurso original e o próximo. As condições de espaço do ensaio original são preservadas pela tradução.

## PRE564 — BMW sintética em RAM no layout PT-BR
- [42556240760](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42556240760): `AUDIT_OK`. Com o protótipo de motor BMW PRE502 em RAM (+5% artificial apenas para teste, nível 0→1), validou-se estrutura `ExpN/RefSpec/PtrN`, recurso de **698.004 bytes**, SHA256 `d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6`, EA checksum `4d05584a`.
- Num ZDIR PT-BR **simulado em memória**, somente bytes relativos **16,20,21,22,23** do registro 805 foram diferentes para representar novo tamanho e checksum; `archive=4`, `sector=0`, `total=0` preservados; SHA256 do registro hipotético `728e02041249ed029026fcdd7a92f254b60f1669f81ebad45e57f53574481735`.
- O leitor virtual em RAM recuperou o mesmo pacote sintético, com **364 bytes zero** restantes antes do próximo setor. Isto não executou o loader real da V48, nem alterou arquivos PT-BR.
- **Não confundir:** viabilidade estrutural de dados, checksum e espaço = **verificada**; aceitação do novo `engine/bmwm3gtr_upgrade_engine_pre499` pelo guest real = **NÃO comprovada**; FE/catalogo preço, compra/SetPackage, física e persistência = **NÃO comprovadas**.

## Próximos gates e segurança
1. Verificar execução do carregador guest `ZDIR/ZZDATA`/recurso VPAK e registro da nova coleção, primeiro sobre dados/cópias e saves **descartáveis**, sem modificar `MARCEK`.
2. Determinar a integração do novo nível ao inventário BMW e FECarPartInfo/catálogo, preço e checkout; só depois habilitar a função em versão isolada.
3. Não aplicar patches de deslocamento PAL original ao ZDIR PT-BR; PT-BR usa setor zero e índice 805. Não gerar V49 por antecipação, não instalar modificações no perfil principal.
4. Preservar origem PT-BR, V46/V47/V48 e assinatura, save `MARCEK`, Nitro PRE398, controle PG-9076, gráficos/resolução, cap FPS e proteções térmicas.

**Checkpoint final:** PRE561, PRE562 retry, PRE563 e PRE564 `AUDIT_OK`; original PT-BR do Drive e arquivos do telefone agora correlacionados por SHA256; simulação BMW sobre layout PT-BR confirmada apenas em RAM. Nenhum APK, ZIP, `ZDIR`, `ZZDATA4` ou save de jogo foi modificado.
