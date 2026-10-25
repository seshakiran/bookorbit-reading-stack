local f=assert(io.open(arg[1]));local s=f:read('*a');f:close()
local a=assert(s:find('function BookOrbitCatalog:promptSearch(',1,true))
local b=assert(s:find('\nfunction BookOrbitCatalog:filterSummary',a,true))
local shared={kindlefetch_import_api=1};local opts,received,shown
local TextEntry={open=function(o)opts=o end,searchBelow=function(recents)return function()return recents end end}
local MenuUI={rowsIn=function(w)return w end,row=function(_,o)return o end,group=function(_,rows)return rows end}
local catalog={client={server_url='https://books.example'},settings={catalog_recent_searches={'prior'}}}
local env={BookOrbitCatalog=catalog,require=function(n)
 if n=='pluginshare' then return shared elseif n=='bookorbit_text_entry' then return TextEntry elseif n=='bookorbit_menu_ui' then return MenuUI end
 error(n)
end,util={trim=function(v)return v:match('^%s*(.-)%s*$')end,partialMD5=function()return 'digest' end},
_=function(v)return v end,T=function(_,v)return v end,
UIManager={tickAfterNext=function(_,fn)fn()end,show=function(_,o)shown=o end},InfoMessage={new=function(_,o)return o end},
lfs={attributes=function(path)return path=='/imports/book.epub' and 'file' end},
BookOrbitStateManager={linkFile=function(digest,file_id,book_id,path)catalog.link={digest,file_id,book_id,path}end},
type=type,pcall=pcall,tonumber=tonumber,ipairs=ipairs,string=string}
local chunk;if setfenv then chunk=assert(loadstring(s:sub(a,b-1)));setfenv(chunk,env) else chunk=assert(load(s:sub(a,b-1),'catalog','t',env)) end;chunk()
function catalog:runSearch(p,q,scope)self.search={p,q,scope}end
function catalog:persistSetting(k,v)self.settings[k]=v end
local params={authorId=7}
shared.kindlefetch_search=function(q,ctx)received={q,ctx};return true end
catalog:promptSearch(params,'Author','initial')
assert(opts.value=='initial');opts.on_submit('Library query');assert(catalog.search[1]==params and catalog.search[3]=='Author')
local rows=opts.below({},500,400,true)[1];assert(#rows==2 and rows[1].action.kind=='submit' and rows[2].label=='Search Z-Library')
local page={opts=opts,entryText=function()return '  Octavia Butler  'end,close=function(self)self.closed=true end,refresh=function(self)self.refreshed=true end}
opts.on_action(page,{kind='kindlefetch-import'})
assert(page.closed and received[1]=='Octavia Butler' and received[2].kind=='bookorbit')
assert(received[2].server_url==catalog.client.server_url)
opts.on_action(page,{kind='clear-recents'});assert(#catalog.settings.catalog_recent_searches==0 and page.refreshed)
assert(#page.opts.below(page,500,400,true)[1]==2)
catalog.settings.catalog_recent_searches={'recent'};catalog:promptSearch(params,'Author');page.opts=opts;page.closed=false
opts.on_action(page,{kind='recent',index=1});assert(page.closed and catalog.search[2]=='recent')
shared.kindlefetch_import_api=nil;assert(#opts.below(page,500,400,true)[1]==1)
page.closed=false;opts.on_action(page,{kind='kindlefetch-import'});assert(not page.closed and shown.text:find('Enable Kindle Fetch',1,true))
shared.kindlefetch_import_api=1;shared.kindlefetch_search=function()error('controlled failure')end
opts.on_action(page,{kind='kindlefetch-import'});assert(shown.text:find('Could not open',1,true))
local detail={id=42,files={{id=99,format='epub'}}}
function catalog:runConnected(fn)fn()end
function catalog:fetch(_,fn)return fn()end
function catalog.client:catalogBook(id)assert(id==42);return detail end
function catalog:cacheBookDetail(d)assert(d==detail)end
function catalog:supportedFiles(d)return d.files end
function catalog:refreshOnDevice()self.on_device={};self.on_device_files={}end
function catalog:markStackDirty()self.dirty=true end
function catalog:openDownloadedFile(path)assert(self.link and self.on_device[42]==path);self.opened=path end
function catalog:showBookDetail(d)self.detail=d end
local job={book_id=42,path='/imports/book.epub',file_type='epub'}
received[2].on_imported(job);assert(catalog.opened==job.path and catalog.link[2]==99 and catalog.on_device_files[99]==job.path)
catalog.opened=nil;catalog.catalog_closed=true;received[2].on_imported(job);assert(not catalog.opened)
catalog.catalog_closed=false;received[2].on_imported({book_id=42,path='/missing',file_type='epub'});assert(catalog.detail==detail and not catalog.opened)
print('PASS: plugin 2.0 search/import context, native library/scoped/recent search, clear-recents, capability/error handling, persisted local-file link before open, closed/missing-file handling')
