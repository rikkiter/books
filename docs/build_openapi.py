"""Generate the draft API contract and its Swagger UI viewer (stdlib only)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
S = {}
def ref(name): return {'$ref': '#/components/schemas/' + name}
def string(**kw): return {'type': 'string', **kw}
def enum(*values): return string(enum=list(values))
def integer(**kw): return {'type': 'integer', **kw}
def array(item): return {'type': 'array', 'items': item}
UUID = string(format='uuid')
TIME = string(format='date-time')
TEXT = string(minLength=1, maxLength=2000)
def model(name, props, required=None):
    S[name] = {'type': 'object', 'additionalProperties': False, 'properties': props,
               'required': list(props) if required is None else required}
def page(name):
    model(name+'Page', {'items': array(ref(name)), 'next_cursor': {'type': ['string','null']}})

model('Error', {'code': string(), 'message': string(), 'request_id': string(),
                'details': {'type': 'object', 'additionalProperties': True}}, ['code','message','request_id'])
model('User', {'id': UUID, 'display_name': string(), 'role': enum('user','operator','admin')})
model('ProfileUpdate', {'display_name': string(minLength=1,maxLength=100)})
model('YandexLogin', {'access_token': string(minLength=1, maxLength=8192, writeOnly=True, description='Именно OAuth access token Яндекса, не JWT LoginSDK, не authorization code и не токен нашего API. Backend вызывает GET https://login.yandex.ru/info?format=json с Authorization: OAuth <token>, проверяет id и client_id по серверному allowlist. Для Flutter — OAuth-режим LoginSDK. Подробности: yandex-id.md.')})
model('Tokens', {'access_token': string(description='Собственный JWT сервиса; не токен Яндекса.'), 'refresh_token': string(description='Собственный refresh token сервиса; не refresh token Яндекса.'), 'token_type': enum('Bearer'), 'expires_in': integer(minimum=1,maximum=900,description='Время жизни собственного access token в секундах.')})
model('Refresh', {'refresh_token': string(minLength=1)})
model('AddressInput', {'recipient': string(minLength=1,maxLength=100), 'phone': string(minLength=5,maxLength=30), 'city': string(minLength=1,maxLength=100), 'street_address': string(minLength=1,maxLength=300), 'comment': string(maxLength=500)}, ['recipient','phone','city','street_address'])
model('Address', {'id': UUID, **S['AddressInput']['properties']}, ['id','recipient','phone','city','street_address'])
model('BookInput', {'title': string(minLength=1,maxLength=300), 'authors': array(string(minLength=1,maxLength=200)), 'isbn': string(maxLength=20), 'publisher': string(maxLength=200), 'publication_year': integer(minimum=1400,maximum=2200), 'description': string(maxLength=10000), 'genres': array(string(maxLength=100)), 'cover_upload_id': UUID}, ['title','authors'])
model('Book', {'id': UUID, **{k:v for k,v in S['BookInput']['properties'].items() if k != 'cover_upload_id'}, 'cover_url': string(format='uri'), 'available_copies': integer(minimum=0), 'points_price': integer(minimum=1)}, ['id','title','authors','available_copies','points_price'])
model('BookUpdate', {**S['BookInput']['properties'], 'points_price': integer(minimum=1)}, [])
model('Copy', {'id': UUID, 'book_id': UUID, 'condition': enum('like_new','good','acceptable'), 'status': enum('available','reserved','in_delivery','transferred','withdrawn'), 'location': string(maxLength=300), 'source_submission_id': UUID}, ['id','book_id','condition','status','location'])
model('CopyInput', {'book_id': UUID, 'condition': S['Copy']['properties']['condition'], 'location': string(minLength=1,maxLength=300)}, ['book_id','condition','location'])
model('CopyUpdate', {'condition': S['Copy']['properties']['condition'], 'location': string(minLength=1,maxLength=300), 'withdrawn': {'type':'boolean'}}, [])
model('UploadInput', {'purpose': enum('submission_photo','book_cover'), 'content_type': enum('image/jpeg','image/png','image/webp'), 'size_bytes': integer(minimum=1, maximum=10485760)})
model('Upload', {'id': UUID, 'put_url': string(format='uri'), 'expires_at': TIME, 'required_headers': {'type':'object','additionalProperties':string()}, 'status': enum('pending','ready','rejected')})
model('UploadCompleted', {'id': UUID, 'status': enum('ready')})
model('SubmissionInput', {'photo_upload_ids': array(UUID), 'title_hint': string(maxLength=300), 'isbn_hint': string(maxLength=20)}, ['photo_upload_ids'])
S['SubmissionInput']['properties']['photo_upload_ids'].update(minItems=1,maxItems=6,uniqueItems=True)
model('Submission', {'id': UUID, 'status': enum('submitted','evaluated','accepted','handover_scheduled','handed_over','received','credited','cancelled','rejected'), 'photo_upload_ids': array(UUID), 'offered_points': integer(minimum=1), 'book_id': UUID, 'rejection_reason': string(), 'created_at': TIME}, ['id','status','photo_upload_ids','created_at'])
model('Evaluation', {'book_id': UUID, 'condition': S['Copy']['properties']['condition'], 'offered_points': integer(minimum=1), 'comment': string(maxLength=1000)}, ['book_id','condition','offered_points'])
model('HandoverInput', {'method': enum('courier','locker'), 'address_id': UUID, 'locker_id': string(minLength=1,maxLength=100)}, ['method'])
model('Handover', {'id': UUID, 'method': enum('courier','locker'), 'status': enum('scheduled','completed','cancelled'), 'address_snapshot': ref('AddressInput'), 'locker_id': string(), 'created_at': TIME}, ['id','method','status','created_at'])
model('HandoverConfirmation', {'location': string(minLength=1,maxLength=300), 'evidence_reference': string(minLength=1,maxLength=300)})
model('Inspection', {'condition': S['Copy']['properties']['condition'], 'location': string(minLength=1,maxLength=300)}, ['condition','location'])
model('Wallet', {'balance': integer(minimum=0)})
model('Transaction', {'id': UUID, 'amount': integer(), 'reason': enum('submission_credit','order_debit','order_refund'), 'submission_id': UUID, 'order_id': UUID, 'created_at': TIME}, ['id','amount','reason','created_at'])
model('OrderInput', {'book_id': UUID, 'address_id': UUID, 'expected_points_price': integer(minimum=1)})
model('Order', {'id': UUID, 'book_id': UUID, 'copy_id': UUID, 'points_spent': integer(minimum=1), 'status': enum('confirmed','shipped','delivered','cancelled'), 'address_snapshot': ref('AddressInput'), 'tracking_reference': string(), 'created_at': TIME}, ['id','book_id','copy_id','points_spent','status','address_snapshot','created_at'])
model('Reason', {'reason': string(minLength=1,maxLength=1000)})
model('Shipment', {'tracking_reference': string(minLength=1,maxLength=300)})
model('BookRequestInput', {'title': string(minLength=1,maxLength=300), 'authors': array(string(maxLength=200)), 'isbn': string(maxLength=20), 'comment': string(maxLength=1000)}, ['title'])
model('BookRequest', {'id': UUID, **S['BookRequestInput']['properties'], 'status': enum('submitted','purchasing','available','rejected'), 'book_id': UUID, 'decision_reason': string(), 'created_at': TIME}, ['id','title','status','created_at'])
model('Availability', {'book_id': UUID})
model('DeviceInput', {'platform': enum('ios','android'), 'push_token': string(minLength=1,maxLength=4096)})
model('Device', {'id': UUID, 'platform': enum('ios','android')})
for name in ['Book','Copy','Submission','Transaction','Order','BookRequest','Address']: page(name)

spec = {'openapi':'3.1.0','info': {'title':'Букшеринг MVP REST API','version':'0.1.0-draft', 'description':'Проект контракта, не реализованный backend. Обмен за баллы, одна книга в заказе. Книга — конкретное издание; Copy — физический экземпляр. Подписочный прокат вне этой версии. Допущения и переходы: api-design.md.'}, 'servers':[{'url':'/api/v1'}], 'security':[{'BearerAuth':[]}], 'paths':{}, 'components':{'schemas':S,'securitySchemes':{'BearerAuth':{'type':'http','scheme':'bearer','bearerFormat':'JWT'}}}}
def query(name, schema, description=''):
    return {'name':name,'in':'query','required':False,'schema':schema,'description':description}
PAGING=[query('limit',integer(minimum=1,maximum=100,default=20)),query('cursor',string(),'Непрозрачный курсор; фильтры между страницами менять нельзя.')]
def op(path, method, title, result=None, body=None, status=200, public=False, desc='', params=None, idem=False, tag=None):
    item={'operationId':method+'_'+re.sub(r'[^a-zA-Z0-9]+','_',path).strip('_'), 'summary':title,'tags':[tag or path.strip('/').split('/')[0]], 'description':desc, 'responses':{}}
    if public: item['security']=[]
    if path.startswith('/admin/'):
        item['description']='Только operator или admin; управление каталогом и экземплярами — только admin. '+desc
        item['x-roles']=['admin'] if '/books' in path or '/copies' in path else ['operator','admin']
    parameters=[{'name':n,'in':'path','required':True,'schema':UUID} for n in re.findall(r'\{(\w+)\}',path)]
    parameters += params or []
    if idem:
        parameters.append({'name':'Idempotency-Key','in':'header','required':True,'schema':string(minLength=8,maxLength=128), 'description':'Ключ действует 24 часа в пределах пользователя и операции. Повтор тела возвращает первоначальный результат; другое тело с тем же ключом — 409. Параллельные повторы выполняются один раз.'})
    if parameters:item['parameters']=parameters
    if body:item['requestBody']={'required':True,'content':{'application/json':{'schema':ref(body)}}}
    success={'description':'Успешно' if status != 204 else 'Выполнено; тело отсутствует'}
    if result:success['content']={'application/json':{'schema':ref(result)}}
    item['responses'][str(status)]=success
    codes=[400,422,429,500]
    if not public:codes += [401,403]
    if '{' in path:codes += [404]
    if method in ['post','patch','put','delete']:codes += [409]
    for code in codes:
        item['responses'][str(code)]={'description':{400:'Некорректный запрос',401:'Недействительная сессия / токен',403:'Недостаточно прав',404:'Ресурс отсутствует или не принадлежит пользователю',409:'Конфликт состояния / цены / баланса / идемпотентности',422:'Ошибка валидации',429:'Лимит запросов',500:'Внутренняя ошибка'}[code], 'content':{'application/json':{'schema':ref('Error')}}}
    spec['paths'].setdefault(path,{})[method]=item

op('/auth/yandex','post','Обменять OAuth-токен Яндекса на сессию сервиса','Tokens','YandexLogin',public=True,desc='Основной сценарий: Flutter получает OAuth-токен через LoginSDK и передаёт его по HTTPS. Backend вызывает GET https://login.yandex.ru/info?format=json с Authorization: OAuth <token>. Проверяет непустой id и client_id из серверного allowlist наших OAuth-приложений. Учётная запись связана уникальным (provider=yandex, provider_user_id=id); email/login не ключи идентификации. Пользователь создаётся только с ролью user. Provider-токен не хранится и не пишется в логи. Неверный токен — 400 INVALID_PROVIDER_TOKEN; чужой client_id — 400 PROVIDER_CLIENT_MISMATCH; сбой Яндекса — 503 IDENTITY_PROVIDER_UNAVAILABLE. Ответ: Cache-Control: no-store. JWT LoginSDK и code этот endpoint не принимает. React OAuth callback и cookie-сессии не спроектированы этим endpoint.')
spec['paths']['/auth/yandex']['post']['responses']['503']={'description':'Яндекс недоступен или ответил некорректно; не создавать локальную сессию. Повтор возможен позднее.', 'content':{'application/json':{'schema':ref('Error')}}}
spec['paths']['/auth/yandex']['post']['responses']['200']['headers']={'Cache-Control':{'description':'Ответ с токенами не кешируется.','schema':string(const='no-store')}}
op('/auth/refresh','post','Обновить сессию','Tokens','Refresh',public=True,desc='Ротация refresh token; повторное использование отозванного токена отзывает семейство сессии. Неверный токен — 400 INVALID_REFRESH_TOKEN.')
op('/auth/logout','post','Завершить сессию',body='Refresh',status=204,desc='Отозвать семейство refresh token текущего пользователя. Access token истекает не позднее 15 минут.')
op('/me','get','Мой профиль','User')
op('/me','patch','Изменить имя','User','ProfileUpdate')
op('/me/addresses','get','Адреса доставки','AddressPage',params=PAGING)
op('/me/addresses','post','Создать адрес','Address','AddressInput',201,idem=True)
op('/me/addresses/{address_id}','put','Заменить адрес','Address','AddressInput')
op('/me/addresses/{address_id}','delete','Удалить адрес',status=204,desc='Снимки адресов в оформленных заказах сохраняются.')
filters=PAGING+[query('q',string(maxLength=300)),query('genre',string()),query('available_only',{'type':'boolean','default':False})]
op('/books','get','Каталог изданий','BookPage',public=True,params=filters)
op('/books/{book_id}','get','Карточка издания','Book',public=True)
op('/recommendations','get','Рекомендации по предпочтениям и наличию','BookPage',params=PAGING)
op('/me/favorites','get','Понравившиеся книги','BookPage',params=PAGING)
op('/me/favorites/{book_id}','put','Добавить книгу в понравившиеся',status=204,desc='Повторный вызов не создаёт дубль.')
op('/me/favorites/{book_id}','delete','Удалить из понравившихся',status=204,desc='Повторный вызов для существующей книги возвращает 204.')
op('/uploads','post','Получить URL загрузки в MinIO','Upload','UploadInput',201,desc='book_cover доступен только admin. URL действует 10 минут; bucket закрытый. Привязка upload к владельцу обязательна.')
op('/uploads/{upload_id}/complete','post','Подтвердить загрузку','UploadCompleted',desc='Проверить объект, фактический размер, формат и возможность декодирования; удалить EXIF. Не полагаться только на Content-Type. Повтор для ready возвращает тот же результат.')
op('/submissions','post','Отправить книгу на оценку','Submission','SubmissionInput',201,idem=True,desc='Только ready-фото текущего пользователя с purpose=submission_photo. Один upload нельзя привязать к двум приёмкам.')
op('/submissions','get','Мои сдаваемые книги','SubmissionPage',params=PAGING)
op('/submissions/{submission_id}','get','Статус сдачи книги','Submission')
op('/submissions/{submission_id}/accept','post','Принять оценку','Submission',idem=True,desc='Только evaluated → accepted; цена оценки фиксируется.')
op('/submissions/{submission_id}/cancel','post','Отказаться от сдачи','Submission',body='Reason',idem=True,desc='Разрешено до handed_over; отменяется активная передача. Баллы не начисляются.')
op('/submissions/{submission_id}/handover','post','Назначить передачу','Handover','HandoverInput',201,idem=True,desc='Только accepted → handover_scheduled. Для courier обязателен address_id своего пользователя, для locker — locker_id. Одновременно только одна активная передача. Каталог постаматов и тарифы вне черновика.')
op('/wallet','get','Баланс баллов','Wallet')
op('/wallet/transactions','get','Журнал баллов','TransactionPage',params=PAGING)
op('/orders','post','Заказать один экземпляр книги','Order','OrderInput',201,idem=True,desc='Атомарно проверить expected_points_price, достаточность баланса и доступность, выбрать и зарезервировать один экземпляр, списать баллы и создать confirmed заказ. Адрес должен принадлежать пользователю. 409: PRICE_CHANGED / INSUFFICIENT_POINTS / BOOK_UNAVAILABLE. Передача client copy_id запрещена.')
op('/orders','get','Мои заказы','OrderPage',params=PAGING)
op('/orders/{order_id}','get','Заказ и статус доставки','Order')
op('/orders/{order_id}/cancel','post','Отменить заказ','Order','Reason',idem=True,desc='Только confirmed → cancelled. Одна транзакция: возврат баллов, освобождение экземпляра, отмена задания доставки. Повтор не создаёт дополнительный возврат.')
op('/book-requests','post','Запросить отсутствующую книгу','BookRequest','BookRequestInput',201,idem=True,desc='Заявка не списывает баллы и не создаёт заказ. Закупка выполняется оператором; сроки и лимиты пока не определены.')
op('/book-requests','get','Мои заявки на книги','BookRequestPage',params=PAGING)
op('/book-requests/{request_id}','get','Статус заявки','BookRequest')
op('/me/devices','post','Зарегистрировать устройство для push','Device','DeviceInput',201,desc='Upsert по push_token; токен принадлежит только текущему пользователю после регистрации.')
op('/me/devices/{device_id}','delete','Отключить push на устройстве',status=204)
op('/admin/books','post','Создать издание','Book','BookInput',201,idem=True)
op('/admin/books/{book_id}','patch','Изменить издание и цену','Book','BookUpdate')
op('/admin/copies','get','Физические экземпляры','CopyPage',params=PAGING+[query('book_id',UUID),query('status',S['Copy']['properties']['status'])])
op('/admin/copies','post','Добавить закупленный экземпляр','Copy','CopyInput',201,idem=True,desc='Для сдаваемых книг экземпляр создаётся только подтверждением передачи; начальный статус available.')
op('/admin/copies/{copy_id}','patch','Изменить состояние и местонахождение','Copy','CopyUpdate',desc='Вывести из фонда можно только available; произвольное редактирование reserved/in_delivery/transferred запрещено.')
op('/admin/submissions','get','Очередь приёмки','SubmissionPage',params=PAGING+[query('status',S['Submission']['properties']['status'])])
op('/admin/submissions/{submission_id}','get','Приёмка с фотографиями','Submission',desc='Фото доступны оператору по временным URL через отдельный endpoint.')
op('/admin/uploads/{upload_id}/download','get','Временная ссылка на фото','UploadDownload')
model('UploadDownload',{'url':string(format='uri'),'expires_at':TIME})
op('/admin/submissions/{submission_id}/evaluate','post','Оценить книгу','Submission','Evaluation',idem=True,desc='Только submitted → evaluated; до принятия оценки изменение через повторную оценку evaluated → evaluated разрешено с новым ключом.')
op('/admin/submissions/{submission_id}/reject','post','Отклонить книгу','Submission','Reason',idem=True,desc='submitted/evaluated/received → rejected. Для физически полученной книги создать операторскую задачу урегулирования возврата; баллы не начисляются. Условия возврата требуют уточнения.')
op('/admin/submissions/{submission_id}/confirm-handover','post','Подтвердить передачу курьеру / в постамат','Submission','HandoverConfirmation',idem=True,desc='handover_scheduled → handed_over; передача completed. Баллы не начисляются; доступный экземпляр не создаётся.')
op('/admin/submissions/{submission_id}/receive','post','Подтвердить получение на складе','Submission','HandoverConfirmation',idem=True,desc='handed_over → received. Баллы ещё не начисляются. Книга ожидает физической проверки.')
op('/admin/submissions/{submission_id}/approve-inspection','post','Принять книгу после проверки и начислить баллы','Submission','Inspection',idem=True,desc='received → credited. Одной транзакцией создать available Copy с фактическим состоянием и начислить согласованные offered_points. Уникальность начисления и экземпляра по submission_id обязательна. Менять согласованную оценку нельзя: при неприемлемом состоянии отклонить приёмку и урегулировать возврат.')
op('/admin/orders','get','Заказы для обработки','OrderPage',params=PAGING+[query('status',S['Order']['properties']['status'])])
op('/admin/orders/{order_id}/ship','post','Отметить передачу в доставку','Order','Shipment',idem=True,desc='confirmed → shipped, Copy reserved → in_delivery. Конкурирует с отменой через блокировку заказа; возможен только один переход.')
op('/admin/orders/{order_id}/deliver','post','Подтвердить доставку','Order',idem=True,desc='shipped → delivered; Copy → transferred. Подтверждение на основании факта доставки.')
op('/admin/book-requests','get','Заявки на закупку','BookRequestPage',params=PAGING+[query('status',S['BookRequest']['properties']['status'])])
op('/admin/book-requests/{request_id}/purchase','post','Начать закупку','BookRequest',idem=True,desc='submitted → purchasing; фактическая покупка выполняется вне API.')
op('/admin/book-requests/{request_id}/fulfill','post','Связать заявку с доступной книгой','BookRequest','Availability',idem=True,desc='submitted/purchasing → available. Требуется хотя бы один доступный экземпляр. Уведомить автора через outbox; автоматической брони или заказа нет.')
op('/admin/book-requests/{request_id}/reject','post','Отклонить заявку','BookRequest','Reason',idem=True,desc='submitted/purchasing → rejected; исключение из исходного обещания закупки, требует согласования.')
spec['tags']=[{'name':x,'description':d} for x,d in [('auth','Сессии'),('me','Профиль, адреса, понравившиеся, устройства'),('books','Каталог'),('recommendations','Рекомендации'),('uploads','Фотографии'),('submissions','Сдача книг'),('wallet','Баллы'),('orders','Заказы'),('book-requests','Заявки на закупку'),('admin','Операционные процессы')]]
# Structural checks; a full OpenAPI validator is still recommended in CI.
ids=set()
def walk(value):
    if isinstance(value,dict):
        if '$ref' in value:
            assert value['$ref'].startswith('#/components/schemas/')
            assert value['$ref'].split('/')[-1] in S, value['$ref']
        for v in value.values():walk(v)
    elif isinstance(value,list):
        for v in value:walk(v)
for path, methods in spec['paths'].items():
    for method, operation in methods.items():
        assert operation['operationId'] not in ids
        ids.add(operation['operationId'])
        assert set(re.findall(r'\{(\w+)\}',path)) == {p['name'] for p in operation.get('parameters',[]) if p['in']=='path'}
        assert any(k.startswith('2') for k in operation['responses'])
walk(spec)
ROOT.joinpath('openapi.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Embed the contract: the viewer works when opened as a file, no local API required.
payload=json.dumps(spec,ensure_ascii=False).replace('<','\\u003c')
html='''<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Букшеринг — Swagger UI</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
<style>body{margin:0} .notice{padding:16px;background:#fff3cd;font-family:system-ui}</style></head>
<body><div class="notice">Черновик контракта API. Backend ещё не реализован. Для интерфейса требуется интернет (Swagger UI CDN).</div>
<div id="swagger-ui"></div><script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({spec:SPEC,dom_id:'#swagger-ui',deepLinking:true,supportedSubmitMethods:[],validatorUrl:null});</script></body></html>'''
ROOT.joinpath('swagger.html').write_text(html.replace('spec:SPEC','spec:'+payload),encoding='utf-8')
print(f'Generated: {len(ids)} operations, {len(S)} schemas. References, path parameters and operation IDs checked.')
