import json
import types

from netCDF4 import Dataset, Dimension, Variable, Group
from numpy import  dtype


class NetCDFJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "__json__"):
            return o.__json__();

        if isinstance(o, Dataset) or isinstance(o,Dimension) or isinstance(o,Variable) or isinstance(o,Group):
            res = {}
            for k in dir(o):
                v = o.__getattribute__(k)
                if not k.startswith("_") and not callable(v):
                    res[k] = v

            if isinstance(o,Dimension):
                res['unlimited']  = o.isunlimited()
            if isinstance(o, Variable):
                res['data'] = o[:].tolist()

            return res

        if hasattr(o,'item'):
            return o.item()
        elif isinstance(o,dtype):
            return o.__str__()
        elif isinstance(o, bytes):
            return o.decode()

        return json.JSONEncoder.default(self, o)

def ncdump(dataset):
    return json.dumps(dataset,cls=NetCDFJsonEncoder)



