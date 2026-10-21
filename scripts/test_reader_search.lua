-- Exercise the actual patched BookOrbit search dialog with mocked reader widgets.
local file=assert(io.open(assert(arg[1], 'pass the patched catalog path'),'r'))
local source=file:read('*a');file:close()
local start=assert(source:find("function BookOrbitCatalog:promptSearch(",1,true))
local finish=assert(source:find("\nfunction BookOrbitCatalog:filterSummary",start,true))
local fragment=source:sub(start,finish-1)
local shared,shown,closed={kindlefetch_import_api=1},{},{}
local InputDialog={new=function(_,opts)
 opts.getInputText=function(self)return self.input or "" end
 opts.onShowKeyboard=function(self)self.keyboard=true end
 return opts
end}
local Catalog={client={server_url="https://books.example/api/v1"},settings={catalog_recent_searches={"earlier"}}}
local searches,externals={},{}
function Catalog:runSearch(params,q,scope) searches[#searches+1]={params=params,q=q,scope=scope} end
function Catalog:showRecentSearches(params,scope) self.recent_params=params;self.recent_scope=scope end
local env={BookOrbitCatalog=Catalog,InputDialog=InputDialog,
 UIManager={show=function(_,widget)shown[#shown+1]=widget end,close=function(_,widget)closed[#closed+1]=widget end},
 InfoMessage={new=function(_,opts)return opts end},
 util={trim=function(text)return text:match("^%s*(.-)%s*$")end,partialMD5=function()return "local-digest" end},
 _=function(text)return text end,
 require=function(name)assert(name=="pluginshare");return shared end,
 type=type,pcall=pcall,tonumber=tonumber,ipairs=ipairs,string=string,
 lfs={attributes=function(path)return path=="/imports/book.epub" and "file" or nil end},
 BookOrbitStateManager={linkFile=function(digest,file_id,book_id,path)Catalog.link={digest,file_id,book_id,path}end},
}
local chunk
if setfenv then chunk=assert(loadstring(fragment));setfenv(chunk,env)
else chunk=assert(load(fragment,"BookOrbit search","t",env)) end
chunk()
local params={authorId=9};local scope="An author"
local received_context
shared.kindlefetch_search=function(q,context)externals[#externals+1]=q;received_context=context;return true end
Catalog:promptSearch(params,scope)
local dialog=shown[#shown]
assert(dialog.keyboard and dialog.buttons[1][3].is_enter_default)
assert(dialog.buttons[1][3].text=="Search library" and dialog.buttons[2][1].text=="Search Z-Library")
dialog.input="  Ursula Le Guin  "
dialog.buttons[1][3].callback()
assert(#searches==1 and searches[1].params==params and searches[1].scope==scope and searches[1].q=="Ursula Le Guin")
assert(#externals==0 and closed[#closed]==dialog)
Catalog:promptSearch(params,scope);dialog=shown[#shown];dialog.input="  Octavia Butler  "
dialog.buttons[2][1].callback()
assert(#externals==1 and externals[1]=="Octavia Butler" and #searches==1)
assert(closed[#closed]==dialog) -- The catalog itself stays underneath.
assert(received_context.kind=="bookorbit" and received_context.server_url==Catalog.client.server_url and type(received_context.on_imported)=="function")
local detail={id=42,files={{id=99,format="epub"}}}
function Catalog:runConnected(fn)fn()end
function Catalog:fetch(_,fn)return fn()end
function Catalog.client:catalogBook(id)assert(id==42);return detail end
function Catalog:cacheBookDetail(value)assert(value==detail)end
function Catalog:supportedFiles(value)return value.files end
function Catalog:refreshOnDevice()self.on_device={};self.on_device_files={}end
function Catalog:markStackDirty()self.dirty=true end
function Catalog:openDownloadedFile(path)self.opened=path end
function Catalog:showBookDetail(value)self.shown_detail=value end
received_context.on_imported({book_id=42,path="/imports/book.epub",file_type="epub"})
assert(Catalog.link[2]==99 and Catalog.link[3]==42 and Catalog.link[4]=="/imports/book.epub")
assert(Catalog.on_device[42]=="/imports/book.epub" and Catalog.on_device_files[99]=="/imports/book.epub")
assert(Catalog.opened=="/imports/book.epub" and Catalog.dirty)
Catalog.opened=nil
received_context.on_imported({book_id=42,path="/missing.epub",file_type="epub"})
assert(not Catalog.opened and Catalog.shown_detail==detail)
Catalog.catalog_closed=true
received_context.on_imported({book_id=42,path="/imports/book.epub",file_type="epub"})
assert(not Catalog.opened) -- Don't steal focus after the catalog was closed.
Catalog.catalog_closed=false
Catalog:promptSearch(params,scope);dialog=shown[#shown];dialog.input="   "
local count=#closed;dialog.buttons[1][3].callback();dialog.buttons[2][1].callback()
assert(#closed==count and #searches==1 and #externals==1)
dialog.buttons[1][2].callback();assert(Catalog.recent_params==params and Catalog.recent_scope==scope)
shared.kindlefetch_import_api=nil
Catalog:promptSearch({},nil);dialog=shown[#shown];assert(not dialog.buttons[2][1].enabled)
shared.kindlefetch_import_api=1
shared.kindlefetch_search=nil
Catalog:promptSearch({},nil);dialog=shown[#shown];dialog.input="An author"
assert(not dialog.buttons[2][1].enabled)
count=#closed;dialog.buttons[2][1].callback();assert(#closed==count and shown[#shown].text:find("Enable Kindle Fetch",1,true))
shared.kindlefetch_search=function()error("test failure")end
Catalog:promptSearch({},nil);dialog=shown[#shown];dialog.input="A title"
dialog.buttons[2][1].callback();assert(shown[#shown].text:find("Could not open Z-Library",1,true))
print("PASS: BookOrbit library/recent searches preserved; Z-Library query handoff, blank/missing/error handling, import-before-open context, persistent local-file link, no second transfer, missing-file handling, dashboard retained")
