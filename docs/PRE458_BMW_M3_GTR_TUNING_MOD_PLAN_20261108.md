# NFSMW PRE458 — BMW M3 GTR: desenvolvimento de tunagem de desempenho

**Estado:** mod em desenvolvimento, sem APK nova e sem alterações de saves. Base V48 PRE452, logs reais PRE455, leitura PAL PRE456. Alvo observado: BMW M3 GTR de carreira `type=41`; Fiat Punto `type=74` é controle, **não** doador automático de peças.

## Problema confirmado
- BMW: Motor 0, Transmissão 0, Suspensão 0, Nitro 3, Pneus 0, Freios 0, Indução 0.
- Punto: Motor 4, Transmissão 4, Suspensão 3, Nitro 3, Pneus 3, Freios 4, Indução 3.
- Todas as 16 consultas V48 PRE447_ROUTE registraram `reason=2`; o retorno é valor derivado do lookup e não é contagem comprovada de peças válidas para compra.
- PRE456 comprovou três subcaminhos de aquisição do valor na rota 2; não confirmou no aparelho qual subcaminho selecionado para a BMW.

## Objetivo de engenharia
Habilitar ajustes de desempenho via **peças reais e dados aplicáveis à BMW M3 GTR**, inicialmente as seis categorias que retornam zero. Preservar Nitro PRE398 e não modificar ajustes de física globais. O menu de tuning fino durante corrida, se necessário, exige uma etapa própria após instalação válida das peças.

## Regras de implementação
1. **Fonte de dados:** inventariar o backup autenticado PRE99 e localizar os perfis de upgrade/atributos e registros válidos para o modelo BMW. Não reaproveitar contagens ou IDs do Punto sem prova de compatibilidade.
2. **Validação encadeada:** categoria -> ID de peça real -> modelo/variante compatível -> preço/textos válidos -> efeito físico -> compra/garagem -> persistência. `candidate_count > 0` sozinho é insuficiente.
3. **Feature flag OFF por padrão:** nenhuma mudança para o jogo original ou outros carros. Para ligar, exigir identificação robusta da variante BMW e catálogo auditado.
4. **Fail-closed:** não produzir itens `Option title`, `20/20`, `999.999.999`; não forçar `0->4`, não fabricar atributos nem injetar compras.
5. **Testes sem save real:** guardar e verificar cópia do `MARCEK`. Experimentos de compra/salvamento apenas em perfil descartável; testar recarga e desativação da mod antes de aceitar dados persistidos. Não garantir que save com peças novas possa voltar à versão original.
6. **Regressões:** preservar assinatura permanente, pacote `io.github.nfsmwrecomp`, V46/V47/V48, Nitro PRE398, shaders, resolução interna 1920x1080, controle PG-9076, física dos outros carros e proteção térmica.

## Gates
| Gate | Entrega | Condição |
|---|---|---|
| PRE458 | Inventário PRE99 + testes sintéticos fail-closed | Auditoria acionada; validar relatório real |
| PRE459 | Provar nós e IDs de performance compatíveis com BMW e semântica do salvamento | Obrigatório |
| PRE460 | Staging reversível da mod OFF, verificação ARM64 e regressões | Sem APK |
| PRE461 | Primeiro APK experimental assinada com incremento de versão | Somente depois dos gates anteriores |
| PRE462 | Testar BMW em perfil descartável e Punto como controle | Sem afetar MARCEK |

A simples presença de arquivos de carro não prova que sejam dados úteis ou completos; a PRE458 pode retornar nenhum candidato legítimo. Se não existirem dados aplicáveis na fonte Xbox 360, pesquisar um overlay novo **com dados próprios e compatíveis**, e não usar diretamente scripts de mods de PC.

## Referências externas (não equivalem a prova no Android)
- https://www.nfs-cars.com/need-for-speed-most-wanted/7/files/view/17949/
- https://www.youtube.com/watch?v=hswEieclgj0
- https://nfs.fandom.com/wiki/Need_for_Speed%3A_Most_Wanted/Performance_Tuning
