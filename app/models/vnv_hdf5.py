import json

from h5py import File, Group, Dataset, AttributeManager, Reference
from h5py._hl.base import _RegionProxy
from h5py._hl.dims import DimensionManager, DimensionProxy
from h5py.h5f import FileID
from h5py.h5g import GroupID
from numpy import dtype

class HDF5JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "__json__"):
            return o.__json__();

        if isinstance(o, File) or isinstance(o,Group) or isinstance(o,Dataset):
            res = {}
            for k in dir(o):
                try:
                    v = o.__getattribute__(k)
                    if not k.startswith("_") and not callable(v) and not k in ["parent",'file','id','ref','regionref']:
                        res[k] = v
                except:
                    pass

            if hasattr(o,'items'):
                res["children"] = {
                    key : value for key,value in o.items()
                }

            #if isinstance(o,Dataset):
             #   res["data"] = o[()].tolist()

            return res


        if isinstance(o, AttributeManager):
            return {
                key:value for key,value in o.items()
            }
        if isinstance(o, DimensionManager):
            return [ a for a in o]

        if isinstance(o, DimensionProxy):
            res = {}
            try:
                for a,b in o.items():
                    try:
                        res[a]=b
                    except:
                        pass
            except:
                pass
            return res

        if isinstance(o, _RegionProxy) or isinstance(o,GroupID) or  isinstance(o, Reference) or isinstance(o, FileID) :
            return None

        if hasattr(o, 'item'):
            return o.item()
        elif isinstance(o, dtype):
            return o.__str__()
        elif isinstance(o, bytes):
            return o.decode()

        try:
            return json.JSONEncoder.default(self, o)
        except Exception as e:
            return str(o)

def h5dump(dataset):
    return json.dumps(dataset, cls=HDF5JsonEncoder)


#fname = "/home/ben/source/vnvlabs.com/vnvlabs/applications/moose/examples/ex01_inputfile/h5.h5"
#a = File(fname, mode='r')
#b = json.loads(h5dump(a))
#print(b)
