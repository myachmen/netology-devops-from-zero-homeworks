# Terraform CI/CD: подготовка №156, НЕ АКТИВИРОВАНО

Протокол APH/1.1. Разрешение №156 охватывает только feature-код и offline tests.
**Этот документ не разрешает запускать Terraform, workflow или менять credentials/IAM.**

## Состояние и источники

- Исходная ветка: `diplom-yandexcloud`, base `6c80ea5f1e099c3199c2896562c23bebda04117b`.
- Новая ветка: `feature/diploma-terraform-cicd`. В существующие ветки изменений нет.
- [Анализ №155](https://github.com/myachmen/ai-project-context/blob/63318a6b3484fdf0e15768c09c38a134bb5007f5/netology-diploma/exchange/result.md)
  повторно используется как REUSED_HISTORICAL: два roots, S3 locking, provider lock,
  14 managed resources по №153. Это не свежая проверка state, drift, прав или health.
- [Оригинал Нетологии](https://github.com/netology-code/devops-diplom-yandexcloud/blob/cd2a878c96cf9852c5226be6f9bba4d221cfe634/README.md):
  CI-альтернатива требует автоматического запуска **и применения** при любом коммите
  в main и скриншотов pipeline. Подготовительный шаблон/plan-only это не выполняет.
- Implementation main `654d7f6386f11f4976043197dba047f296483606` не содержит
  `terraform/infrastructure`. До активации потребуется отдельно утверждённый перенос.

## Почему публикация инертна

Исполняемого YAML в `.github/workflows/` не добавлено. Шаблон расположен в
`ci/terraform/terraform-infrastructure.yml.inert`: GitHub не обнаруживает его как
workflow. Дополнительно оба jobs имеют `if: false && ...`, а runner требует
`TF_CI_ACTIVATION=OWNER_APPROVED_EXISTING_NOOP`; в шаблоне стоит другое значение.
Нет manual dispatch, pull_request_target, release/tag trigger или reusable entry.
Не создавать PR в №156. Даже случайное копирование шаблона без правок оставляет
jobs выключенными. Тесты блокировки не запускают Terraform и не обращаются в сеть.

Три изменения активации (перенос в workflow directory, снятие обоих false gates,
изменение activation marker) **запрещены до отдельного разрешения владельца**.
Marker — дополнительная проверка от ошибки, не секрет и не security boundary от
злоумышленника с write-доступом к trusted main.

## Будущая архитектура

PR → изолированные static checks без Secrets. Trusted push main → fmt → init →
validate → refreshed saved plan → private JSON → policy → apply того же saved plan.
Главный workflow trigger не имеет paths-фильтра: иначе не покрывается «любой commit».
PR paths ограничены инфраструктурой и защитным кодом. Bootstrap никогда не входит
в routine apply; `-recursive` format запускается только внутри infrastructure.

`run_infrastructure.py` — будущая foreground-обвязка, не запускать её в №156.
До subprocess/network/temp credentials проверяются activation/event/repo/ref/SHA
и наличие необходимых inputs. Перед apply повторно проверяется текущий main SHA.
Backend/lock SHA256 закреплены по исходным байтам. Terraform CLI pin **1.15.7**,
provider из committed lock **0.238.0**, required HCL `>=1.5.0`, provider `~>0.170`.
Последнее ограничение допускает 0.238.0; само по себе это не конфликт.
Перед активацией отдельно согласовать lower bound и backend feature compatibility.
Actions checkout/setup-terraform закреплены по полным проверенным SHA.

## State, locking и очередь

Сохраняются существующий S3 backend, default workspace, endpoint и state key из
`terraform/infrastructure/backend.tf`. Bootstrap, migration/reconfigure/upgrade,
новые workspaces и fallback на local state не допускаются. Backend и lockfile
fingerprints меняются только после отдельного review.

HCL `use_lockfile=true`; всем writers нужен нативный S3 lock. Минимум backend:
list нужного prefix, Get/Put state, Get/Put/Delete `.tflock`; Delete самого state
не требуется. Точное соответствие Yandex bucket policy и conditional locking
ещё UNKNOWN. Историческое чтение №153 не подтверждает runner write/lock права.

Concurrency group один для backend/default, `cancel-in-progress:false`:
не отменять активный apply. В шаблоне используется стандартная очередь с одним
pending run: следующий push может заменить pending. Поэтому **до первого запуска
заморозить другие main merges и local writers**. Перед постоянным auto apply
владелец должен выбрать проверенную расширенную очередь (`queue:max`, если её
поддерживают актуальные GitHub/schema/linter), либо другой способ сохранить commits.
Даже расширенная очередь не гарантирует Git commit order. Stale SHA → STOP.
Не считать этот черновик доказательством применения каждого concurrent main commit.
Concurrency действует только в одном repo; S3 lock нужен и для внешних writers.
Блокировки plan/apply не являются непрерывной транзакцией; stale/error → STOP,
никогда не применять force-unlock автоматически.

## Два credential planes и input contract (значений здесь нет)

| Назначение | Будущий GitHub input | Использование |
|---|---|---|
| Provider API | Secret `TF_YC_SERVICE_ACCOUNT_KEY_JSON` | Existing approved Terraform SA authorized JSON, temp0600, `YC_SERVICE_ACCOUNT_KEY_FILE` |
| Backend | Secrets `TF_S3_ACCESS_KEY_ID`, `TF_S3_SECRET_ACCESS_KEY` | Existing approved static pair, process-local AWS access/secret env |
| Provider IDs | Variables `TF_CLOUD_ID`, `TF_FOLDER_ID` | Именно `TF_VAR_cloud_id`, `TF_VAR_folder_id`, как требует HCL |
| Admin network | Variable `TF_ADMIN_CIDR` | `TF_VAR_admin_cidr`, точно утверждённое значение |
| SSH metadata | Variable `TF_SSH_PUBLIC_KEY` | Тот же существующий однострочный ED25519 public key, temp public file; `TF_VAR_ssh_public_key_path` |

Новые inputs должны совпасть с текущей инфраструктурой. Не копировать whole
`~/.aws`, private SSH key, admin kubeconfig, build/image-puller key или app Secrets.
Public key не секрет, но публиковать его значение в коде/логах не требуется.
Другой алгоритм ключа требует явно согласованного изменения строгого contract.
Реальный подходящий API key, S3 pair и effective права **UNKNOWN**, не читались.
Не создавать Secrets/Variables, не извлекать credentials и не выполнять IAM grants в №156.

Кандидат capabilities для будущего review: compute.editor; alb.editor и
vpc.publicAdmin для public ALB; vpc.privateAdmin/vpc.publicAdmin плюс
vpc.securityGroups.admin для нужных сетевых ресурсов. Доступ ограничить folder/
bucket-prefix, исключить IAM/SA key management/bootstrap. Это не доказанный
минимальный effective policy. Проверить реальные provider references и отдельные
read/plan/lock/write права до активации; folder editor/admin по умолчанию не выдавать.

## Политика первого existing-infrastructure запуска

`plan_policy.py` принимает private show JSON строго версии format1.2 / CLI1.15.7.
Политика требует complete/non-errored plan, точный набор 14 адресов из кода,
непустые IDs в prior state, тот же набор planned state, все resource actions
строго `[no-op]`, совпадение before/after/state values, отсутствие drift/deferred/
imports/moves/unknowns и изменений outputs. Update, create, delete, обе replacement
последовательности, неизвестный action/верхнеуровневая схема → DENY.
Новые check blocks/schema также требуют review. Никаких флагов отключения policy.

14 адресов — code-derived baseline, не доказательство live ID/lineage. Перед первым
plan отдельно подтвердить доверенный backend, lineage/serial/identity и актуальность
состава. Первый реальный JSON может потребовать schema reconciliation: **STOP,
не ослаблять parser автоматически**. Синтетические fixtures не доказывают совместимость
с фактическим plan. Новые provider capabilities/action blocks тоже STOP.

Любой VM update может вызвать остановку из-за allow_stopping_for_update, даже если
delete отсутствует. Единственный control-plane/etcd делает это критичным. Поэтому
расширение на in-place updates не допускается текущим кодом и требует отдельной
политики/тестов/разрешения. Пустой state после teardown не должен создать платные VM.

## Логи, ошибки и ограничение гарантий

Private temporary directory0700, files0600, umask077; raw provider key, plan,
show JSON/stdout/stderr не идут в GitHub logs/artifacts/cache/outputs. На выходе
только фиксированные категории и число ресурсов. Не использовать TF_LOG,
CLI argument overrides, shell tracing, upload-artifact или Terraform wrapper.
JSON duplicate keys/NaN, malformed input и исключения не печатают содержимое.
Контроллер чистит свои temp-файлы; `.terraform` остаётся только на одноразовом runner.

Plan exit0/2 допустимы, exit1 — STOP; policy всё равно запрещает любой non-noop.
Apply получает тот же saved plan: интерактивное подтверждение не нужно, `-auto-approve`
не нужен. Политика не даёт нового разрешения владельца. Run timeout45мин,
отдельные команды ограничены; нет retries, rollback, repair, второго apply.
Error/timeout после write → UNKNOWN, сначала отдельное согласованное reconciliation.
Raw logs автоматически не публикуются для troubleshooting. Не добавлять слепой rerun.

No-op exit0 не доказывает здоровье Kubernetes/ALB/monitoring и восстановление с нуля.
Нужны отдельно разрешённые postchecks и evidence. Защитный код не удержит владельца
trusted workflow от его изменения, не заменяет review, scoped IAM и backups.

## Порядок будущих согласований

1. Утвердить перенос в main: отдельная feature от **актуального main**, выборочный
   перенос только Terraform root/dependencies и CI/tests/runbook; сохранить учебные
   Materials, README, историю. Не merge всей diplom-yandexcloud вслепую, не force.
   Повторно проверить существующие workflows/triggers перед любым push/PR.
2. Утвердить точный набор Secrets/Variables, existing identity, scoped rights,
   public-key contract, CLI/backend/schema и очередь. Настройка — отдельное разрешение.
3. Отдельно разрешить один контролируемый **plan-only** run с fresh identity/backend/
   state gate и lock writes. Текущий runner включает apply, поэтому для plan-only
   нужен reviewed отдельный режим/черновик; не запускать его «для проверки».
4. Review sanitized plan summary и private plan допустимым защищённым способом.
   Затем отдельное прямое разрешение **первого apply** на exact candidate SHA/ожидание.
5. Отдельно активировать template/jobs/marker и согласованный main commit.
   Новая activation run делает fresh plan и применяет только его, в том же job,
   если точно совпала no-op policy. При новом diff STOP; старый plan не переносится
   через незащищённый artifact. Freeze других writers на первую демонстрацию.
6. Проверить eventpush/main → fmt/validate/plan/policy/apply, approved postchecks,
   собрать run/SHA/version/sanitized results/screenshots. Manual dispatch/plan-only
   не считать закрытием требования. Для автоматической работы после первого запуска
   отдельно согласовать разрешённый класс будущих изменений и очередь: постоянный
   per-run manual approval не соответствует полностью unattended варианту.
7. Перед будущим teardown **отдельно отключить** privileged auto apply/freeze main
   по согласованному плану. Новый commit после destroy иначе может вернуть расходы.
   Никогда не добавлять автоматический destroy ради демонстрации.

**Один следующий безопасный шаг:** review опубликованной feature без исполнения,
согласовать точный способ интеграции и identity/input contract. Не переходить
к активации из-за успешных offline tests.

## Offline verification (можно в №156)

```sh
python3 -m unittest discover -s tests -p 'test_terraform_*.py' -v
```

Дополнительно разрешены Python syntax parsing, YAML/text validation шаблона и
actionlint с отключёнными внешними shellcheck/pyflakes. **Не запускать runner,
Terraform CLI, GitHub workflows, SSH или cloud probes.** Fixtures синтетические,
не копировать реальный state/plan для тестов.

Первичные ссылки для будущего review:
- https://developer.hashicorp.com/terraform/language/backend/s3
- https://developer.hashicorp.com/terraform/cli/commands/apply
- https://developer.hashicorp.com/terraform/cli/commands/show
- https://yandex.cloud/en/docs/terraform/authentication
- https://yandex.cloud/en/docs/compute/security/
- https://yandex.cloud/en/docs/vpc/security/
- https://yandex.cloud/en/docs/application-load-balancer/security/
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
