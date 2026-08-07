# MiniShop

Демонстрационное микросервисное приложение — полигон для тестирования OpenClaw
как AIOps-агента (развёртывание, мониторинг, автоматическое расследование и
устранение инцидентов).

## Легенда

Упрощённый интернет-магазин: пользователь смотрит каталог товаров, кладёт
товары в корзину, оформляет заказ. Заказ резервирует остаток на складе и
публикует событие, по которому асинхронно отправляется уведомление.
Обычный e-commerce-флоу с естественными точками отказа — то, что нужно для
воспроизведения инцидентов.

## Архитектура

```
web-bff  --->  catalog   (товары, категории, остатки)
   |     --->  order     (оформление заказа, резервирование, расчёт цены)
   |     --->  notification (health/ready для admin-страницы)
   |
 order  --->  catalog (резервирование остатка)
 order  --->  Redis Stream "order.events"  --->  notification (consumer)

catalog, order, notification --> общий Postgres (схемы catalog / orders / notifications)
```

| Сервис | Роль |
|---|---|
| `web-bff` | Веб-интерфейс (FastAPI + Jinja2): каталог, корзина, статус заказа, `/admin` |
| `catalog` | CRUD категорий/товаров, остатки, атомарное резервирование |
| `order` | Оформление заказа, расчёт суммы, оркестрация вызова catalog, публикация событий |
| `notification` | Consumer Redis Stream, "отправка" уведомлений (запись в БД) |

Подробности по структуре БД, ресурсам k8s и распределению по нодам Timeweb
Cloud — см. обсуждение в истории разработки; схема БД описана в
`db/init/001_schemas.sql` и Alembic-миграциях каждого сервиса.

## Локальный запуск

```bash
cp .env.example .env
docker compose up -d --build
python scripts/seed_data.py
```

Веб-интерфейс: http://localhost:8080 · admin/health: http://localhost:8080/admin

## Деплой в Kubernetes (Timeweb Cloud)

```bash
kubectl apply -k k8s/overlays/prod
```

Манифесты в `k8s/overlays/prod` используют placeholder-теги `:local` — они
предназначены для локального `kubectl apply -k` на тестовом кластере с
образами, собранными через `docker compose build`. GitHub Actions
(`.github/workflows/ci-cd.yml`) перегенерирует
`k8s/overlays/prod/kustomization.yaml` на лету, подставляя GitHub Container
Registry (`ghcr.io/<owner>/<repo>`) и SHA коммита, и применяет манифесты в
неймспейс `minishop` после каждого пуша в `main`.

Требуется:
- Secret `KUBECONFIG_B64` в Settings → Secrets and variables → Actions —
  base64 от kubeconfig кластера (`base64 -w0 kubeconfig.yaml`, на Windows
  `[Convert]::ToBase64String([IO.File]::ReadAllBytes("kubeconfig.yaml"))`)
- Первый деплой создаст 4 приватных пакета в GHCR
  (`github.com/<owner>/demo-app-aiops/pkgs/container/...`) — сделайте их
  публичными (Package settings → Change visibility → Public) или настройте
  `imagePullSecrets` в кластере, иначе `kubectl` не сможет их скачать
- `ingress-nginx` установлен в кластере (`kubectl apply -f
  k8s/cluster-addons/ingress-nginx.yaml` — Timeweb Cloud не ставит его по
  умолчанию). Сервис контроллера — `NodePort` (без платного облачного
  LoadBalancer): узнать порт — `kubectl -n ingress-nginx get svc
  ingress-nginx-controller`, зайти — `http://<external-ip любой
  worker-ноды>:<nodePort>/` с Host-заголовком из `k8s/base/web-bff/ingress.yaml`
  (сейчас там `<ip>.nip.io` — wildcard DNS, резолвится сам, без покупки домена)
- Кластер имеет StorageClass — наш k0s-кластер на Timeweb Cloud его не
  предоставляет из коробки (`kubectl get storageclass` → пусто), поэтому
  `k8s/cluster-addons/local-path-provisioner.yaml` (Rancher
  local-path-provisioner) нужно применить один раз вручную:
  `kubectl apply -f k8s/cluster-addons/local-path-provisioner.yaml`.
  `k8s/base/postgres/statefulset.yaml` явно указывает
  `storageClassName: local-path`
