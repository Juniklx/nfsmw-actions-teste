# NFSMW Android — planejamento PRE254 Junkman + BMW/Razor (2026-11-06)

## Pedido atual
Usuário quer **alterar a quantidade de peças Junkman** no projeto Android. Em mensagem imediatamente anterior, também solicitou **manter a BMW M3 GTR inicial / poder vencer a primeira corrida contra Razor**. Essas são frentes distintas e não há patch funcional demonstrado para nenhuma.

## Evidências existentes do projeto
- V37 instrumentada, assinada com certificado permanente original; testes físicos PRE251–253. PRE253B confirmou débito do primeiro carro `30.000 -> 3.000`, gasto `27.000` no `site=8` PAL (`sub_82564D80`). Isto **não demonstra** estrutura de inventário Junkman nem dinâmica da corrida de Razor.
- `nfsmw.log` PRE252/PRE253 mostrou mecanismo de save em `/data/user/0/io.github.nfsmwrecomp/files/nativo/usuario/.../454107D9/00000001/NAME`, com payload `NAME` de **62.688 bytes**. O caminho é privado do aplicativo, portanto não prometer acesso direto via gerenciador de arquivos Android. Não editar o save ativo a quente.
- A PRE254 está configurada no GitHub Actions para varredura **somente leitura** do PRE99 autenticado, investigando texto relacionado a `Junkman`, inventário, `Razor`, BMW e a vizinhança do débito já observado. O resultado da PRE254 não deve ser considerado aprovado até relatório JSON `AUDIT_OK`.

## Referência externa — PC v1.3, NÃO provada para Xbox 360 Android
- Código e documentação pública revisados em `https://github.com/sprintstate/nfs-mw-save-editor`, especialmente `docs/JUNKMAN_OFFSETS.md`.
- Editor **PC v1.3** representa as recompensas por *slots* de ficha, somando tipos iguais para obter quantidade, e diferencia **7 categorias de performance**: freios, motor, nitro, turbo, suspensão, pneus e transmissão.
- Os offsets, `Type_ID`, limites de 59 slots, checksums, endianness e formatos de save do PC **não podem ser copiados cegamente** para o jogo original Xbox 360 recompilado.
- Fichas de recompensa não equivalem a peças já instaladas em veículos. Projeto deve oferecer quantidade disponível **por categoria**, não necessariamente substituir parâmetros de física nem desbloquear automaticamente equipamento instalado.

## Abordagem segura pretendida
1. Verificar a representação real de inventário no código e no save da edição Xbox 360 executada pela V37. Caso a varredura textual não encontre símbolos, isso é esperado em C++ recompilado de PPC nomeado por endereços: será necessária análise diferencial de save próprio/autorizado ou instrumentação passiva.
2. Planejar uma opção **Junkman** que leia a quantidade atual e permita ajustar quantidade desejada **se e somente se** tipo, estrutura, limites e persistência forem demonstrados.
3. Não criar fichas em slots inexistentes, editar material privado do usuário sem backup, burlar integridade de save, nem escrever em ponteiros guest de tradução desconhecida.
4. Para a investigação do prólogo/Razor, separar `chegar primeiro na corrida` de `não perder a BMW e manter progressão da carreira`: são comportamentos diferentes. A história padrão contém sabotagem e perda do veículo, logo um simples patch de vitória pode deixar progresso inconsistente.
5. Primeiro realizar auditoria read-only, depois protótipo isolado, depois build sob autorização explícita: futura versão >37, mesmo pacote e certificado original. Preservar saves, V35–V37, 1920×1080, cap atual 60 FPS, SDL/input PG-9076/touch, shaders/gráficos/física e limites térmicos.

## Pendências
- Identificar estrutura real da contagem Junkman na edição PAL e seu save.
- Identificar como o prólogo determina falha de motor, resultado da corrida e propriedade da BMW sem alterar progressão irreversivelmente.
- Registrar apenas evidência verificada no `CONTEXTO_NFSMW.md` canônico, após backup. Não proclamar cheats de Junkman ou BMW implementados.
