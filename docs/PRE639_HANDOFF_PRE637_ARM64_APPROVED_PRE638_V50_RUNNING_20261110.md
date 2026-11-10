# PRE639 — PRE637 ARM64 aprovada; PRE638 V50 em execução (2026-11-10)

## Evidências confirmadas

- PRE637: GitHub Actions [42745476208](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42745476208), `completed/success`, `PRE637_STATUS=AUDIT_OK` e `PRE637_PHASE=ARM64_NATIVE_LINK_AND_SYMBOLS_PASS`. JSON bruto preservado em [NFSMW_PRE637_V49_C3_ARM64_42745476208.zip](https://drive.google.com/file/d/1OSpWYHGWTTlURo9VDJ4HrLebsZ6B7hv8/view) (GitHub artifact 13731616880).
- Compilação **real** de `libmain.so` ARM64 em árvore temporária com a instrumentação C3 PRE635. Hash SHA-256 da ELF: `b8748dbf74f8fddb1bf3151801b50fe24e159c0f4d9fa6f84f0f675791d0cc9e`, 117.828.376 bytes. Quatro callbacks anteriores `NFSMW_PRE429_TRACE_ENTRY`, `NFSMW_PRE429_TRACE_LEVEL`, `NFSMW_PRE447_ROUTE`, `NFSMW_PRE622_ATTR_VALUE` exportados exatamente uma vez cada. Marcadores PRE194, PRE635 e Nitro PRE398 presentes.
- Fontes prévias: PRE194 SHA-256 `a01f25e531af783d37f70a3c3caa0f3e7a979d2bdbdd923abf7b2c6062d29d1e`; PRE635 SHA-256 `1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92`; reversão exata verificada. A auditoria não comprova equivalência binária com a biblioteca da V49 assinada.
- PRE637 **não gerou APK** nem tocou na chave de assinatura ou no save. Nenhum teste de execução do diagnóstico, correção C3 ou aumento de FPS ocorreu.

## Próxima etapa iniciada: PRE638 V50

- Script privado: `automation/kaggle/pre638_build_signed_v50_c3_two_request_diag.py`. Workflow `.github/workflows/nfsmw-pre638-v50-c3-signed-diagnostic.yml`. Gate fixo de fonte em `docs/PRE637_V49_C3_ARM64_NATIVE_RESULT.json` e fonte GitHub derivada da receita PRE626/V49.
- Execução GitHub Actions [42748358853](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42748358853), iniciada em 2026-11-10. Na última observação desta atualização, `in_progress`, com preflight PRE625 e PRE637 aprovados, ainda **sem APK V50 comprovada**.
- Se concluída, saída esperada: `NFSMW_V50_PRE638_C3_TWO_REQUEST_DIAGNOSTIC.apk`, `versionCode 50`, `applicationId io.github.nfsmwrecomp`, **mesmo certificado permanente** SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Asserções `apksigner`, AAPT, SHA dos ativos PAL/USA, ZIP, log C3, quatro callbacks e Nitro devem passar. Falha em qualquer gate impede marcar release validada.
- Preservar APK V49 instalada e testada; V50 **não deve ser instalada** antes de concluir assinatura/integridade. Não modificar `.p12`, credenciais ou saves, não desinstalar V49. O registro V49 de 60 FPS e irregularidade de apresentação 8/24–25 ms no SurfaceFlinger continua separado do C3.
- Este experimento **não corrige a duplicidade C3**: somente coleta metadata de dois pedidos quando o guarda `copia_duplicada` dispara; mantém `ApagarEnlaces` e `return false`. Não remover salvaguardas nem usar como aumento comprovado de FPS.
- No teste eventual V50 no Galaxy S24 FE, verificar abertura, 1920x1080 internos, opções gráficas, shaders, física, controle touch/iPega PG-9076, Nitro e saves; enviar `nfsmw.log` após reproduzir C3. Depois comparar os campos `offset_primera/offset_segunda`, `epoca_ahora/epoca_primera`, `mismos_comandos`, `subir` e quadros. Não burlar limites térmicos.
- Quando a PRE638 concluir, reler **o log e JSON reais** e atualizar este contexto com sucesso/erro e hash do APK somente se verificados. Não inferir conclusão por ter workflow em execução.

