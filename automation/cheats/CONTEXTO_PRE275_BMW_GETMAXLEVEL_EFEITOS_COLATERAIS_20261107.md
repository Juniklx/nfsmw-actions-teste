# NFSMW Android — PRE275: efeitos colaterais do caminho GetMaxLevel (2026-11-07)

## Contexto atual
- V37 segue última APK funcional testada no Galaxy S24 FE. Perfil MARCEK possui BMW M3 GTR normal, adicionada via save PRE260: usuário **conseguiu selecioná-la e dirigir**. Menu Tuning da BMW apresenta apenas Visual, Peças/Desempenho ocultos pela classificação HeroCar. Punto, dinheiro e Junkman preservados.
- PRE262–PRE274: identificadas estruturalmente `sub_82578988` (menu principal de tuning), `sub_8256F818` (geração de pacotes), `sub_823E5988` (consulta de níveis: candidata a `Physics::Upgrades::GetMaxLevel`), `sub_8256B440` (inicialização `TakeControl`). PRE271/PRE274 ensaiaram marcadores passivos desativados por padrão, **somente em memória**, sem build V38 ou teste dos pacotes reais no dispositivo.

## PRE275 — verificação executada
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42326048799 — **conclusão success**, `PRE275_STATUS AUDIT_OK`; execução reproduzível do scanner `automation/kaggle/pre275_bmw_getmaxlevel_side_effects_readonly.py`.
- Fonte: PRE99 autenticado SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`. Scanner de somente leitura encontrou três funções em shards PAL, hash de cada shard incluído no relatório.
- `sub_823E5988` (PAL `nfsmw_recomp.28.cpp`, SHA256 `11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad`): 8 operações de escrita guest no total. Duas **escritas U16 fora da pilha** em `REX_STORE_U16(ctx.r11.u32 + 18,...)` (linhas relativas 118 e 141) após `lhz r?,18(r11)`. Operações `addi`/`addis` consistentes com decremento de 1 módulo 2^16, mas propósito de *refcount* é **inferência**. Outra escrita usa temporário `ea` derivado de `r1-112`, provavelmente pilha; scanner a classifica como ambígua por sintaxe, **não** como efeito externo provado.
- `sub_8214B858` (PAL `nfsmw_recomp.50.cpp`, SHA256 `f20ec567de4c4637756977a71a6c85f3848b63ba639f037b819868328e3f7e9d`): 4 escritas guest, incluindo **uma U16** em `ctx.r11.u32+18` após leitura da mesma posição, consistente com decremento; outra escrita `ea` derivada de frame de pilha. Chamadas diretas `sub_82148718` e `sub_8214E9E0` ainda não auditadas recursivamente.
- `sub_8214EDA8` (PAL `nfsmw_recomp.83.cpp`, SHA256 `21e561eeae953888b7d645719dc6bd7077dfa040f3f06896b7bbe3ba3e7774d4`): **0 gravações guest diretas**, mas chama `sub_82145428` e `sub_82145C50` em ramos diferentes. Logo, não é apropriado declará-la livre de efeitos colaterais sem auditar as chamadas.
- **Decisão baseada em evidência:** a função `sub_823E5988` **não é pura**, possui gravações guest fora da pilha e chamadas com efeitos transitivos ainda não integralmente auditados. `extra_calls_safe_to_inject=false`: **não inserir sete novas chamadas de GetMaxLevel na entrada do tuning** sem prova posterior de ciclo de vida/compensação, e não ativar indiscriminadamente a PRE264.
- Relatório técnico sanitizado, ZIP JSON (sem saves e sem chave): https://drive.google.com/file/d/1y_sllKSXZGRDAiAL8TT3mdOEXKIqgrq3/view

## Próxima investigação
1. Analisar sem executar os **quatro callee auxiliares imediatos** de `sub_8214B858` e `sub_8214EDA8`: `sub_82148718`, `sub_8214E9E0`, `sub_82145428`, `sub_82145C50`, incluindo alterações em buffers e contadores de referência. Não assumir balanceamento automático.
2. Privilegiar **monitoramento passivo de chamadas já realizadas pelo jogo** (instrumentação PRE271), comparado ao marco PRE274 de entrada no tuning; reconhecer que o menu ainda oculto talvez não gere chamadas para a BMW.
3. Se necessário, estudar a estrutura original de atributos `pvehicle` e a tabela de níveis via dados offline ou monitoramento sem invocação; proteger categorias com zero pacotes e possíveis `GetSelectedPart()==nullptr` antes de habilitar tuning.
4. Nenhum patch de jogo, save, assinatura, build V38 ou APK produzido na PRE275. A V37, Punto, BMW, Junkman, shaders, física, 1920×1080, controle PG-9076 e limiares térmicos permanecem como antes. A futura V38 deverá ter `versionCode>=38`, pacote `io.github.nfsmwrecomp` e **mesmo** certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, nunca uma chave nova/debug.

## Contexto canônico
- `CONTEXTO_NFSMW.md` no Drive ainda terminava em PRE237 na conferência desta sessão. Esta nota PRE275 no GitHub registra evidências novas sem apagar o histórico de ~556 KB; consolidar no Drive **somente com backup e conciliação da série PRE238–275**.
