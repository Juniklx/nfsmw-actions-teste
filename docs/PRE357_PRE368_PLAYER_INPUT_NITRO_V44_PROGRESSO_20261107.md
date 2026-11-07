# PRE357–PRE368 — verificação do caminho de input e V44 diagnóstica (2026-11-07)

## Estado de origem e objetivo
- V43 PRE352 assinada/instalada/testada no Galaxy S24 FE; PRE355 apontou slot Nitro 1 como **candidato**, mas sem referência independente ao jogador. O usuário consumiu o Nitro até zero e aguardou recarga até 100%, e checkpoints amostrados não devem ser confundidos com valores finais.
- PRE344, com quatro carros (jogador+3 IA) confirmou quatro destinos Nitro numa corrida. A função `sub_82424AF0` é multi-instância; **não forçar stores globais**.

## PRE357 — localização do caminho nativo do controle
- Workflow read-only: run `42425715809`, artifact `13594523981`, `AUDIT_OK`.
- Snapshot PRE99 autenticado SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`.
- 46 fontes nativas relacionadas a entrada auditadas, 11.092 linhas, 13 fontes com correspondências, 190 ocorrências textuais.
- `nativo/sdk/src/input/sdl/sdl_input_driver.cpp` trata eventos SDL do gamepad e converte botões em `X_INPUT_GAMEPAD_*`; `nativo/sdk/src/kernel/xam/xam_input.cpp` conecta chamadas do jogo à camada host. **Não conclui botão de Nitro**.

## PRE359/PRE361 — Xam Input e driver SDL
- PRE359 run `42425869079`, `AUDIT_OK`, artifact `13595207525`; auditoria ampliada PRE361 run `42426056579`, artifact `13594713836`, `AUDIT_OK`.
- Em `xam_input.cpp` linhas 95–116: `XamInputGetState_entry` aceita `user_index`, trata `XINPUT_FLAG_ANY_USER` redirecionando a usuário zero, delega a `input_system()->GetState(actual_user_index,input_state)`.
- Em `sdl_input_driver.cpp` linhas 533–559: eventos `SDL_EVENT_GAMEPAD_BUTTON_DOWN` e `UP` são encaminhados para `OnControllerDeviceButtonChangedLocked`; mapeamento para XInput nas linhas 656–725. A ponte pode atender controle físico, mas **não se deve pressupor que todo input de Nitro entre por esse caminho**.

## PRE362 — ponto de instrumentação independente da memória guest
- Run `42426195916`, artifact `13595088364`, `AUDIT_OK`: 20 arquivos de entrada SDK examinados, 16 com matches.
- `nativo/sdk/src/input/input_system.cpp`, original SHA256 `ee84079f668806af48f3a739d53213523c77c55ed202eebe8c3110c474c7432a`.
- `InputSystem::GetState` linhas 247–283: agrega estados nativos dos dispositivos atribuídos ao usuário, usando `GetDeviceState`, `active_devices_.Observe` e `MergeInto`; só depois copia `merged` para `*out_state`. Este objeto nativo pode ser observado **sem acessar memória guest adicional**.
- Esta observação identifica sinais de entrada do usuário 0, **não associa semanticamente o veículo do jogador à instância Nitro**.

## PRE364/PRE365 — sonda passiva de transições XInput
- Fonte de staging `automation/kaggle/pre364_xinput_user0_passive_staging.py`, marcador `NFSMW_PRE364_XINPUT_USER0`.
- PRE365 run `42426480964`, artifact `13594659520`, `AUDIT_OK`. Código fonte PRE99 original verificado por SHA; staging virtual em memória e reversão exata confirmadas. Hash da fonte staged `739640d76964f6d1270ae9bd311ea03171b97f349f5383d4cbf71e24a537474e`.
- Monitor apenas para `user_index==0` e `out_state` válido, registra até 256 **mudanças** de `buttons` e cruzamentos de limiar de gatilhos (32), não todo frame. Bytes do XInput já existem no host; nenhuma leitura guest, alteração do state copy ou stores do Nitro.
- `nitro_button_verified=false`, `owner_verified=false` são invariantes. A confirmação do botão de Nitro exige teste contextual real.

## PRE367/PRE368 — V44 diagnóstica em compilação
- Builder `automation/kaggle/pre367_build_signed_v44_nitro_input_correlation_passive.py`, derivado do construtor V43 PRE352; workflow `.github/workflows/nfsmw-pre367-v44-nitro-input-correlation-passive.yml`.
- `versionCode=44`, pacote `io.github.nfsmwrecomp`, nome planejado `NFSMW_V44_PRE367_NITRO_INPUT_CORRELATION_PASSIVE.apk`.
- Usa mesma chave permanente com certificado SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Requer marcadores `NFSMW_PRE316_NITRO_CYCLE`, `NFSMW_PRE336_NITRO_DIVERSITY`, `NFSMW_PRE348_NITRO_SLOT_VALUES` e `NFSMW_PRE364_XINPUT_USER0` no libmain do APK assinado.
- Workflow run `42426649208`, job `128566254456`. **Na última verificação ao redigir esta seção, a build estava `in_progress`**, sem reivindicar APK assinada ou publicada antes do relatório e do artifact.
- Nenhum cheat Nitro, Speedbreaker ou dinheiro foi ativado. V43 e versões anteriores permanecem preservadas.

## Critérios para teste futuro V44
1. Confirmar assinatura permanente/versionCode/ELF/Drive por relatório e hashes antes de instalar a V44 **sobre a V43 sem desinstalar**, guardando backup `MARCEK`.
2. Em exploração livre, pressionar e soltar Nitro em ciclos conhecidos; comparar PRE364 (input 0) a PRE348 (slots Nitro). Repetir com corrida contendo IA e períodos sem acionar Nitro. Não presumir que botão `B` ou outro é Nitro até demonstrar no log.
3. Sinais de botão são **evidência de causalidade temporal, não, isoladamente, prova de identidade estrutural do player car**. Para cheat player-only, exigir referência independente verificável e caso negativo IA; default OFF/fail-closed.
4. Preservar resolução interna 1920×1080, objetivo FPS 120 (as últimas inicializações ainda registraram cap 60, a investigar separadamente), shaders, efeitos, física, controle PG-9076/touch e proteções térmicas. Não alterar save nem chave.

## Limitação
A auditoria e a canary PRE365 não constituem link ARM64 nem teste em telefone. A V44 é exclusivamente diagnóstico, e nenhum ganho FPS ou cheat funcional foi comprovado nesta etapa.
