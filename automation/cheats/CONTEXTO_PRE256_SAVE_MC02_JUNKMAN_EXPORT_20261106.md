# NFSMW Android — PRE256: save exportado MC02, layout Junkman e edição offline segura (2026-11-06)

## Evidência verificada em arquivo do usuário

- O usuário forneceu no chat um ZIP exportado pela **função própria do aplicativo** `nfsmw_partidas_2026-11-06_2052.zip`.
- **Privacidade:** o ZIP contém partidas pessoais; **não foi enviado ao GitHub nem ao Google Drive**. Somente um relatório técnico sem os bytes da carreira foi arquivado.
- ZIP 99.343 bytes, SHA-256 `88e1702bbc418c3f26f5607116f97258bcdec979862bcb61499a8766a70859a8`; 17 entradas; CRC do ZIP integralmente aprovado; manifest informa `motor=nativo` e `version=0.5.6`.
- 4 perfis; cada um com save `actual`, `anterior` e réplica nativa. Save 62.688 bytes, `MC02`, versão interna `0x10D`. **8/8 arquivos actual/anterior** passaram tamanho, MD5 e três CRCs EA; réplicas nativas idênticas ao respectivo `actual`.
- O perfil correspondente à compra observada em PRE253 tem **30.000** em `anterior`, **3.000** em `actual`, medido no campo big-endian do arquivo `0x4039`. Essa redução de 27.000 coincide com a compra confirmada pelo usuário e pelo logger da V37, sem provar que os demais 250 bytes alterados foram todos causados pela compra. O endereço de offset em disco `0x4039` não é endereço guest RAM.
- Referências técnicas públicas **consultadas**: `sprintstate/nfs-mw-save-editor`, arquivos `core/switch_format.py`, `core/junkman.py`, `core/checksums.py` e `token_catalog.json`. O adaptador de console **Xbox 360/nfsmw-nx**, não apenas o PC, descreve `OwnedMarkers[63]`, slots nativos de **12 bytes em 0x5739**, três campos big-endian de 32 bits (tipo/parâmetro/estado), `state=1` = ficha possuída.
- **No perfil da compra:** 3 slots com marcador `17` (saída da prisão) e os outros 60 slots zero, **nenhuma ficha Junkman tipo 1..7**. As 7 categorias publicamente documentadas são freios (1), motor (2), nitro (3), turbo (4), suspensão (5), pneus (6), transmissão (7). Respeitar os 3 marcadores existentes; capacidade livre **60 slots**. Não propor 10 unidades de cada categoria (70) com apenas 60 vagas.
- Alguns documentos **mais antigos** sobre o editor PC descrevem 59 slots em `0x5769`; a análise desta partida MC02 usa o código específico **atual do console** e verificação direta dos bytes; não transplantar offsets incorretos.
- V37 contém strings e métodos de importação `Partidas.importar`, `importarConSelector`, `botonImportar` e backup `partidas_antes_de_importar.zip`, obtidos por inspeção somente leitura do APK. Não foi testada importação de cópia modificada nem persistência dos tokens no jogo.

## Editor offline experimental e testes

- Foi gerado localmente um script de leitura por padrão `nfsmw_junkman_editor_mc02.py`, 12 KB, para validar e, quando o usuário fornecer quantidades, criar **cópia ZIP separada** e nunca sobrescrever o original.
- Modelo: altera apenas slots dos tipos explicitamente solicitados, conserva tokens desconhecidos/não solicitados, usa vagas verdadeiramente vazias, limita pedidos de cada tipo a 0..10 por padrão, recusa exceder 63 slots, mantém `anterior` intacto e atualiza as duas cópias sincronizadas do `actual`.
- Recalcula MD5 do payload e três CRCs EA segundo o formato MC02. Testes **apenas em memória e ZIP temporário descartado** validaram CRC/MD5 após mudanças, idempotência, rejeição de contagens inválidas/70 slots, preservação dos 3 marcadores tipo 17, dinheiro 3000 preservado e somente duas entradas de conteúdo alteradas no ZIP de prévia.
- **Nenhum save modificado foi entregue ou aplicado no aparelho**; não há comprovação de que as fichas fabricadas no arquivo tenham sido reconhecidas pela tela de recompensas. Sem V38 construída e sem tocar em credenciais.
- Relatório completo, arquivado na pasta privada de logs do Drive: https://drive.google.com/file/d/1T3FNQCsRMU-Uy6PweQtNA7Y8RYbrv5OC/view

## Próxima ação decisória

Perguntar **quantas fichas Junkman o usuário quer por categoria**. Exemplo que cabe: 8 de cada categoria de desempenho = 56 fichas, preservando 3 de saída da prisão, 4 vagas remanescentes. Quando tiver a escolha, produzir cópia ZIP experimental com backup e SHA-256, orientar importação pelo próprio app **com o jogo fechado e save original preservado**, e coletar comprovação visual/log após jogo reconhecer. Se ocorrer erro, restaurar exportação original.

Depois do teste do save, planejar interface `Junkman` no Android, sem reduzir 1920×1080, shaders, física, FPS ou controle. A trilha da corrida Razor/BMW inicial é separada, sem patch construído. Eventual APK V38 requer versionCode >37 e certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
