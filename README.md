## Zabbix Domain & SSL Expiry Checker

Ещё одна попытка реализации на Python мониторинга сроков действия **доменов и SSL-сертификатов** через Zabbix Agent и библиотеку Python-whois.

### Требования
* Python (3.11)
* Python-whois (0.9.5)
* Zabbix v.5 / v.6

### Скрипты
1. `domain_discovery.py`

Читает файл со списком доменов (по одному в строке) и формирует JSON для Low-Level Discovery (LLD).

**Пример файла:** 
`/etc/zabbix/scripts/domains.txt`
~~~
example.com
mydomain.ru
google.com
my.example.com
~~~
**Проверка вручную:**
`python3 /путь/до/domain_discovery.py /путь/до/domains.txt`

2. `domain_check.py`

Проверяет конкретный домен и возвращает `JSON` с количеством дней до окончания регистрации домена (через whois) и SSL-сертификата (через TLS).

**Пример запуска:**
`python3 /путь/до/domain_check.py example.com`

**Пример ответа:**
~~~
{
  "domain_days": 83,
  "ssl_days": 45
}
~~~

### Интеграция с Zabbix Agent
В примерах ниже, используется путь до Python из виртуального окружения (venv).
При необходимости, замените его на свой (например, /usr/bin/python3) или настройте шебанг в скриптах и разместите их в любой директории, доступной агенту.

Также, в заивисимости от ситуации, вместо Zabbix Agent можно использовать Type: `External Check` при настройке правил Discovery rule *(не тестировалось).*

1. В конфиг агента: `/etc/zabbix/zabbix_agentd.d/domain.conf` добавить:
~~~
UserParameter=domain.check[*],/opt/domains/venv/bin/python3 /opt/domains/venv/domain_check.py $1
UserParameter=domain.discovery[*],/opt/domains/venv/bin/python3 /opt/domains/venv/domain_discovery.py $1
~~~
2. Перезапустить агент: `systemctl restart zabbix-agent`

### Настройка в Zabbix (Web)
Рекомендуется сразу, весь процесс настройки, выполнять на уровне Templates.

**Discovery rule:**
- Name: `Domain Discovery`
- Type: `Agent`
- Key: `domain.discovery[/opt/domains/domains.txt]`
- Update interval: `1h` *(опционально)*
- Keep lost resources period: `3h` *(опционально)*

**Item prototypes:**
- Name: `Domain check: {#DOMAIN}`
- Type: `Agent`
- Key: `domain.check[{#DOMAIN}]`
- Type of information: `Text`
- Update interval / history storage period: `10h / 1d` *(опционально)*

**Dependent item** (for Domains):
- Name: `Domain expiry: {#DOMAIN} (days)`
- Type: `Dependent item`
- Key: `domain.expiry[{#DOMAIN}]`
- Type of information: `Numeric (unsigned)`
- History storage period / Trend storage period: `7d / 30d` *(опционально)*
- **Preprocessing:**
  - Name: `JSONPath`
  - Parameters: `$.domain_days`

**Dependent item** (for ssl):
- Name: `SSL expiry: {#DOMAIN} (days)`
- Type: `Dependent item`
- Key: `ssl.expiry[{#DOMAIN}]`
- Type of information: `Numeric (unsigned)`
- History storage period / Trend storage period: `7d / 30d` *(опционально)*
- **Preprocessing:**
  - Name: `JSONPath`
  - Parameters: `$.ssl_days`

`Trigger prototypes` можно организовать в таком виде (сработает 2 раза - за 15 и за 30 дней):
~~~
{Template Domain Expiry:domain.check[{#DOMAIN}].last().domain_days}<15
{Template Domain Expiry:domain.check[{#DOMAIN}].last().ssl_days}<15

{Template Domain Expiry:domain.check[{#DOMAIN}].last().domain_days}<30
{Template Domain Expiry:domain.check[{#DOMAIN}].last().ssl_days}<30
~~~
**Опционально:** период можно вынести в `Template macros`, далее, в прототипе триггера указывать уже его.

**В качестве примечания и примера:**
1. После настройки и "обнаружения" элементов (в соответствии со списком доменов), рекомендуется проверить активные триггеры и при необходимости отключить те, что связаны с SSL, если для некоторых доменов/поддоменов сертификаты отсутствуют или не используются. Тоже самое касается и поддоменов - например, у поддомена будет такой же срок истечения, что и у основного домена (т.е. нет смысла вести по нему статистику).
2. Если при проверке возникла ошибка (не удалось получить WHOIS или др.), скрипт возвращает код 0. Можно настроить триггер на значение `0`, а также, дополнительно, использовать `nodata()`, чтобы понимать, когда данные не приходят совсем (например, агент не отвечает или проблемы с сетью).
3. Для Zabbix v.6 реализован шаблон (директория templates), который можно импортировать напрямую и настроить под свои потребности.
