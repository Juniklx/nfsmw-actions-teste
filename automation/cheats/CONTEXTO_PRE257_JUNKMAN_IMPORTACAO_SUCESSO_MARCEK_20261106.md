# NFSMW Android — PRE257: usuário confirma êxito na importação Junkman (2026-11-06)

## Fonte da evidência
- Após fornecer exportação pelo recurso nativo do app e receber o arquivo experimental `NFSMW_MARCEK_JUNKMAN_8_CADA_EXPERIMENTAL_20261106.zip`, o usuário respondeu explicitamente: **"Deu certo!"**.
- Evidência de confirmação **por relato do usuário**, em aparelho Android, da aplicação do ZIP experimental. Não há captura de tela, dump do save reexportado ou registro pós-reinicialização neste momento; portanto não atribuir durabilidade através de reinícios sem um teste específico.

## O que continha o experimento PRE256
- Apenas o perfil **MARCEK** foi editado; outros três perfis e os arquivos `anterior` foram preservados.
- Foram incluídas **8 fichas para cada uma das sete categorias** de upgrades de desempenho Junkman (freios, motor, nitro, turbo, suspensão, pneus e transmissão), totalizando **56 fichas**, ocupando slots previamente vazios de `OwnedMarkers[63]`.
- As **3 fichas de tipo 17** do perfil MARCEK foram preservadas; restaram **4 slots vazios**.
- Saldo em MARCEK permaneceu **3.000** após compra do carro por 27.000.
- Integridade MC02 antes da entrega: comprimento 62.688 bytes, 3 CRCs EA e MD5 de payload validados em uma cópia, sem modificar ZIP exportado original. O arquivo experimental ZIP foi gerado como cópia independente e passou pelo teste CRC do ZIP.
- Formato já investigado PRE256: MC02 console original, array de 63 marcadores de 12 bytes a partir de 0x5739, cada um incluindo tipo/parâmetro/estado (big-endian). Os IDs e categorias vieram de referência externa com adaptador Xbox360 `sprintstate/nfs-mw-save-editor`, e foram conferidos contra a estrutura do save exportado do usuário.
- **Confirmação funcional limitada:** sucesso relatado na importação/uso. O formato do save e a edição offline funcionaram nessa sessão; não extrapolar que outros perfis, outras versões, outros mods e alterações sem limite sejam seguros ou comprovados.

## Próximos passos
1. Opcionalmente confirmar que as **8 fichas por categoria permanecem após fechar e abrir o jogo**, e/ou reexportar o save para comprovar persistência. Não exigir novo teste para reconhecer o resultado já relatado.
2. Manter o backup ZIP original e o ZIP modificado, com hashes, sem sobrescrever save ativo por patches diretos.
3. Consolidar interface opcional de edição offline por perfil e categoria, com limites de capacidade e verificações MC02, sem credenciais de assinatura nem nova compilação até autorização.
4. Separar trilha `BMV M3 GTR / corrida contra Razor` e economia em runtime. Não afirmar patch Razor funcional ou cheat de dinheiro infinito.
5. Atualizar o `CONTEXTO_NFSMW.md` canônico do Drive, preservando backup, com evidências PRE256/PRE257.
6. Nenhuma nova APK compilada; última é V37 diagnóstica com execução real e sondas. Preservar assinatura permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, `io.github.nfsmwrecomp`, V35–V37, save, gráficos, input, cap de FPS e proteções térmicas.
