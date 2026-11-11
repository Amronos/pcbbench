"""IPC client for the canonical Backplane KiCad project (no SWIG)."""
import sys,uuid,importlib,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'build/bindings'))
import pynng
from google.protobuf import symbol_database,json_format,empty_pb2
from common import envelope_pb2 as env
from common.commands import project_commands_pb2 as project,editor_commands_pb2 as editor,library_commands_pb2 as library
from common.types import base_types_pb2 as base
from common.types import enums_pb2 as enums
from common.types import library_types_pb2 as libtypes
for k,v in vars(libtypes).items():
 if k.isupper():setattr(base,k,v)
for k,v in vars(enums).items():
 if k.isupper():setattr(base,k,v)
from schematic import schematic_types_pb2 as sch,schematic_commands_pb2 as schcmd
from board import board_types_pb2 as pcb,board_commands_pb2 as pcbcmd
from backplane import sketch_route_pb2 as route
ROOT=pathlib.Path(__file__).resolve().parents[1]
DESIGN=ROOT/'boards/rp2350-connect'
class Client:
 def __init__(self):
  sockets=list(pathlib.Path('/run/user/1000/backplane/kicad').glob('*/api.sock'))
  assert len(sockets)==1,sockets
  self.socket=pynng.Req0(dial='ipc://'+str(sockets[0]),send_timeout=180000,recv_timeout=180000);self.token=''
 def call(self,command):
  r=env.ApiRequest();r.header.client_name='works.backplane.rp2350-connect';r.header.kicad_token=self.token;r.message.Pack(command)
  self.socket.send(r.SerializeToString());res=env.ApiResponse.FromString(self.socket.recv());self.token=res.header.kicad_token
  if res.status.status!=env.AS_OK:raise RuntimeError(str(res.status))
  cls=symbol_database.Default().GetSymbol(res.message.TypeName());obj=cls();res.message.Unpack(obj);return obj
 def open(self,kind):
  ext='kicad_sch' if kind==base.DOCTYPE_SCHEMATIC else 'kicad_pcb'
  try:return self.call(project.OpenDocument(type=kind,path=str(DESIGN/('rp2350-connect.'+ext)))).document
  except RuntimeError as e:
   if 'already open' in str(e):return base.DocumentSpecifier(type=kind,board_filename='rp2350-connect.kicad_pcb') if kind==base.DOCTYPE_PCB else base.DocumentSpecifier(type=kind)
   raise
 def get(self,doc,types=[]):
  res=self.call(editor.GetItems(header=base.ItemHeader(document=doc),types=types));return [unpack(a) for a in res.items]
 def create(self,doc,items):
  r=editor.CreateItems(header=base.ItemHeader(document=doc))
  for i in items:r.items.add().Pack(i)
  res=self.call(r)
  for x in res.created_items:
   if x.status.code!=editor.ISC_OK:raise RuntimeError(str(x.status))
  return [unpack(x.item) for x in res.created_items]
 def update(self,doc,items):
  r=editor.UpdateItems(header=base.ItemHeader(document=doc))
  for i in items:r.items.add().Pack(i)
  res=self.call(r)
  for x in res.updated_items:
   if x.status.code!=editor.ISC_OK:raise RuntimeError(str(x.status))
  return [unpack(x.item) for x in res.updated_items]
 def begin(self,doc):return self.call(editor.BeginCommit(header=base.ItemHeader(document=doc))).id
 def end(self,doc,cid,message):self.call(editor.EndCommit(header=base.ItemHeader(document=doc),id=cid,action=editor.CMA_COMMIT,message=message))
 def save(self,doc):self.call(project.SaveDocument(document=doc))
 def lib(self,kind,libid):
  lib,name=libid.split(':',1)
  r=self.call(library.GetItemsFromLibrary(type=kind,item_ids=[base.LibraryIdentifier(library_nickname=lib,entry_name=name)]))
  assert len(r.items)==1,libid
  return unpack(r.items[0])
def unpack(a):
 cls=symbol_database.Default().GetSymbol(a.TypeName());r=cls();a.Unpack(r);return r
def uid():return base.KIID(value=str(uuid.uuid4()))
def xy(x,y):return base.Vector2(x_nm=round(x*1e6),y_nm=round(y*1e6))
def txt(t,x,y,size=1.0):
 return base.Text(text=t,position=xy(x,y),attributes=base.TextAttributes(size=xy(size,size),stroke_width=base.Distance(value_nm=round(size*0.15e6)),horizontal_alignment=base.HA_LEFT,vertical_alignment=base.VA_CENTER,line_spacing=1,visible=True,keep_upright=True))
if __name__=='__main__':
 c=Client();d=c.open(base.DOCTYPE_SCHEMATIC)
 print('SCH',d)
 for lib in ['MCU_RaspberryPi:RP2350A','Regulator_Switching:MCP1640x-xCHY','RF_Module:ESP32-C3-WROOM-02','LED:SK6812MINI','74xGxx:74AHCT1G125','Connector:USB_C_Receptacle_USB2.0_16P','Connector:Micro_SD_Card_Det']:
  try:
   s=c.lib(base.LT_SYMBOL,lib);print('\n',lib,s.footprint_field.text.text)
   for child in s.items:
    if child.item.Is(sch.SchematicPin.DESCRIPTOR):
     p=unpack(child.item);print(p.number,p.name,(p.position.x_nm/1e6,p.position.y_nm/1e6),p.orientation)
  except Exception as e:print(lib,e)
