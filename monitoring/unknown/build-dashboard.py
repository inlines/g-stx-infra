from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
selector='gstx_unknown_games{job="igdb-sync",platform=~"${platform:regex}",region=~"${region:regex}"}'
healthy='(max(gstx_unknown_collection_success{job="igdb-sync"}) == 1) and (time() - max(gstx_unknown_last_success_timestamp_seconds{job="igdb-sync"}) < 900)'
expr=f'max by (platform,region) ({selector}) and on() ({healthy})'
panels=[]
def row(title,y):
 panels.append(dict(id=len(panels)+1,type='row',title=title,collapsed=False,panels=[],gridPos=dict(x=0,y=y,w=24,h=1)))
def panel(title,kind,y,h,expression,instant=False,**extra):
 p=dict(id=len(panels)+1,title=title,type=kind,datasource='Prometheus',gridPos=dict(x=0,y=y,w=24,h=h),targets=[dict(refId='A',expr=expression,legendFormat='{{platform}}[{{region}}]',format='time_series',instant=instant,range=not instant)],fieldConfig=dict(defaults=dict(unit='short',decimals=0,min=0,noValue='—'),overrides=[]))
 p.update(extra);panels.append(p);return p
row('1. Текущий остаток — игры без серийника выбранного региона',0)
panel('Unknown сейчас', 'table',1,6,expr,True,
 transformations=[dict(id='joinByField',options=dict(byField='Time',mode='outer')),dict(id='organize',options=dict(excludeByName={'Time':True}))],
 options=dict(showHeader=True,cellHeight='sm'),
 description='Столбцы PS3[JAP], PS3[PAL], PS3[USA], PS3[OTHER] и другие платформы. PAL=Европа, USA=Америка, JAP=Япония. Игра считается один раз внутри каждого региона. Региональные столбцы нельзя суммировать: Worldwide может относиться к нескольким группам.')
row('2. История остатка — даты по строкам, платформы и регионы по столбцам',7)
p=panel('Оставшиеся Unknown по датам','table',8,12,expr,
 transformations=[dict(id='joinByField',options=dict(byField='Time',mode='outer')),dict(id='sortBy',options=dict(sort=[dict(field='Time',desc=True)]))],
 options=dict(showHeader=True,cellHeight='sm'),
 description='Снимки значений с выбранным шагом; это не количество найденных кодов за день. Пустое значение означает отсутствие надёжного снимка, не ноль. История начинается после установки.')
p['targets'][0]['interval']='$sample';p['maxDataPoints']=1000
row('3. Изменение и график',20)
p=panel('Изменение за 24 часа: минус — Unknown стало меньше','table',21,5,f'({expr}) - on(platform,region) (max by(platform,region) ({selector} offset 1d) and on() ((max(gstx_unknown_collection_success{{job="igdb-sync"}} offset 1d) == 1) and (time()-86400-max(gstx_unknown_last_success_timestamp_seconds{{job="igdb-sync"}} offset 1d) < 900)))',True,
 transformations=[dict(id='joinByField',options=dict(byField='Time',mode='outer')),dict(id='organize',options=dict(excludeByName={'Time':True}))],options=dict(showHeader=True),description='Чистое изменение остатка, а не число найденных серийников: влияют новые игры, исправления и digital_only. Первые 24 часа значений сравнения нет.')
p['fieldConfig']['defaults'].pop('min')
panel('Динамика Unknown','timeseries',26,9,expr,options=dict(legend=dict(displayMode='table',placement='right',calcs=['lastNotNull']),tooltip=dict(mode='multi')),description='Те же региональные значения; пропуски сбора не соединяются ложными нулями.')
row('4. Состояние сбора и правила подсчёта',35)
panel('Последний сбор: 1 — успешно, 0 — ошибка','stat',36,3,'max(gstx_unknown_collection_success{job="igdb-sync"})',True)
panel('Возраст последнего успешного снимка, секунды','stat',39,3,'time()-max(gstx_unknown_last_success_timestamp_seconds{job="igdb-sync"})',True)
panels.append(dict(id=len(panels)+1,type='text',title='Как читать дашборд',gridPos=dict(x=0,y=42,w=24,h=7),options=dict(mode='markdown',content='''**Единица — игра в регионе на выбранной платформе.** Чужой региональный серийник не закрывает пропуск. При наличии релиза нужного региона используются только его серийники. Worldwide используется, только если такого регионального релиза нет. OTHER объединяет остальные регионы, включая Worldwide, как фильтр каталога.

Отбор соответствует видимости каталога без поиска, жанровых и мультиплеерных фильтров: активная платформа, не digital_only на уровне игры/платформы, допустимый тип игры, хотя бы один датированный неотменённый релиз на платформе. Существующее правило каталога не исключает будущие даты. Пустые и пробельные серийники не считаются заполнением.

**Совпадает с обновлённым Unknown** при стандартных фильтрах. Числитель — игры без регионального серийника; знаменатель — все подходящие игры с релизом в этой группе. При поиске, жанровых или мультиплеерных фильтрах сайт считает выбранную подвыборку, а мониторинг — всю платформу.

Сбор каждые 5 минут, запрос только для чтения с таймаутом. Ошибка сбора скрывает актуальные значения; старые данные не превращаются в нули. После 15 минут без нового снимка значения считаются устаревшими. Хранение Prometheus по умолчанию 90 дней с лимитом блоков 2 GB (лимит размера может сократить период); прошлые значения не восстанавливаются задним числом.''')))
# Main view: remaining counts and trend. The date matrix stays available on demand.
current=next(p for p in panels if p['title']=='Unknown сейчас')
current.update(type='bargauge',gridPos=dict(x=0,y=1,w=24,h=8),transformations=[],options=dict(orientation='horizontal',displayMode='basic',showUnfilled=True,reduceOptions=dict(calcs=['lastNotNull'],fields='',values=False)))
trend=next(p for p in panels if p['title']=='Динамика Unknown')
trend['gridPos']=dict(x=0,y=10,w=24,h=12)
trend['options']['legend']['calcs']=['lastNotNull','diff']
trend['fieldConfig']['defaults']['custom']=dict(drawStyle='line',lineInterpolation='stepAfter',spanNulls=False,fillOpacity=8)
delta=next(p for p in panels if p['title'].startswith('Изменение за 24'))
delta.update(type='stat',title='Изменение за 7 дней: минус — Unknown стало меньше',gridPos=dict(x=0,y=22,w=12,h=7),transformations=[],options=dict(reduceOptions=dict(calcs=['lastNotNull'],fields='',values=False),textMode='value_and_name',colorMode='value',graphMode='none'))
delta['targets'][0]['expr']=delta['targets'][0]['expr'].replace('offset 1d','offset 7d').replace('86400','604800')
delta['description']='Чистое изменение остатка за неделю. Пока нет снимка недельной давности, сравнение пустое.'
import copy
monthly=copy.deepcopy(delta);monthly['id']=51;monthly['title']='Изменение за 30 дней: минус — Unknown стало меньше';monthly['gridPos']['x']=12
monthly['targets'][0]['expr']=monthly['targets'][0]['expr'].replace('offset 7d','offset 30d').replace('604800','2592000')
monthly['description']='Чистое изменение остатка за 30 дней. Пока нет снимка месячной давности, сравнение пустое.'
history=next(p for p in panels if p['title']=='Оставшиеся Unknown по датам')
history['gridPos']=dict(x=0,y=31,w=24,h=10)
denominator=dict(id=50,title='Всего игр с релизом в регионе — знаменатель',type='table',datasource='Prometheus',gridPos=dict(x=0,y=41,w=24,h=6),targets=[dict(refId='A',expr=expr.replace('gstx_unknown_games','gstx_region_games'),legendFormat='{{platform}}[{{region}}]',format='time_series',instant=True,range=False)],fieldConfig=dict(defaults=dict(unit='none',decimals=0),overrides=[]),transformations=[dict(id='joinByField',options=dict(byField='Time',mode='outer')),dict(id='organize',options=dict(excludeByName={'Time':True}))],options=dict(showHeader=True))
status=[p for p in panels if p['type'] in ('stat','text') and p is not delta]
for i,p in enumerate(status):p['gridPos']['y']=32+i*4
panels=[dict(id=60,type='row',title='1. Сколько осталось Unknown',collapsed=False,panels=[],gridPos=dict(x=0,y=0,w=24,h=1)),current,
 dict(id=61,type='row',title='2. Динамика остатка — неделя и месяц',collapsed=False,panels=[],gridPos=dict(x=0,y=9,w=24,h=1)),trend,delta,monthly,
 dict(id=62,type='row',title='3. Подробная таблица по датам и знаменатели',collapsed=True,panels=[history,denominator],gridPos=dict(x=0,y=30,w=24,h=1)),
 dict(id=63,type='row',title='4. Состояние сбора и правила',collapsed=False,panels=[],gridPos=dict(x=0,y=31,w=24,h=1)),*status]
for p in [current,trend,delta,monthly,history,*status]:
 if 'fieldConfig' in p:p['fieldConfig']['defaults']['unit']='none'
def variable(name,label,query):
 return dict(name=name,label=label,type='query',datasource='Prometheus',query=query,refresh=1,multi=True,includeAll=True,allValue='.*',current=dict(text='All',value='$__all'),sort=1)
d=dict(uid='gstx-unknown-serials',title='Game StockX - Unknown серийники',schemaVersion=39,version=1,editable=True,tags=['gstx','unknown','serials'],timezone='browser',refresh='5m',time={'from':'now-30d','to':'now'},panels=panels,templating=dict(list=[variable('platform','Платформы','label_values(gstx_unknown_games, platform)'),variable('region','Регионы','label_values(gstx_unknown_games, region)'),dict(name='sample',label='Шаг истории',type='custom',query='5m,1h,1d',current=dict(text='1d',value='1d'),options=[dict(text=x,value=x,selected=x=='1d') for x in ['5m','1h','1d']])]))
(ROOT/'grafana/provisioning/dashboards/unknown_serials.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
