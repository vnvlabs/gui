﻿

%module VnVReader


%{
 #include "shared/Provenance.h"
 #include "shared/LibraryInfo.h"
 #include "PythonInterface.h"
 #include "INodes.h"
 
%}

%include <std_shared_ptr.i>
%include <stdint.i>

%shared_ptr(VnV::Nodes::DataBase)
%shared_ptr(VnV::Nodes::IDoubleNode)
%shared_ptr(VnV::Nodes::IIntegerNode)
%shared_ptr(VnV::Nodes::IFloatNode)
%shared_ptr(VnV::Nodes::IStringNode)
%shared_ptr(VnV::Nodes::ILongNode)
%shared_ptr(VnV::Nodes::IBoolNode)
%shared_ptr(VnV::Nodes::IJsonNode)
%shared_ptr(VnV::Nodes::IShapeNode)
%shared_ptr(VnV::Nodes::IMapNode)
%shared_ptr(VnV::Nodes::IArrayNode)
%shared_ptr(VnV::Nodes::IRootNode)
%shared_ptr(VnV::Nodes::IUnitTestNode)
%shared_ptr(VnV::Nodes::IUnitTestResultsNode)
%shared_ptr(VnV::Nodes::IUnitTestResultNode)
%shared_ptr(VnV::Nodes::ICommMap)
%shared_ptr(VnV::Nodes::IDataNode)
%shared_ptr(VnV::Nodes::ILogNode)
%shared_ptr(VnV::Nodes::IInjectionPointNode)
%shared_ptr(VnV::Nodes::ITestNode)
%shared_ptr(VnV::Nodes::IWorkflowNode)
%shared_ptr(VnV::Nodes::IInfoNode)
%shared_ptr(VnV::Nodes::ICommInfoNode)
%shared_ptr(VnV::Nodes::FetchRequest)
%shared_ptr(VnV::VnVProv)
%shared_ptr(VnV::ProvFile)

%exception { 
    try {
        $action
    } catch (VnV::VnVExceptionBase &e) {
        std::string s("VnV Exception: "), s2(e.what());
        s = s + s2;
        SWIG_exception(SWIG_RuntimeError, s.c_str());
    } catch (std::exception &e) {
        std::string s("std::exception: "), s2(e.what());
        s = s + s2;
        SWIG_exception(SWIG_RuntimeError, s.c_str());
    } catch (...) {
        SWIG_exception(SWIG_RuntimeError, "unknown exception");
    }
}

%include "std_string.i"
%include "std_vector.i"
%include "std_map.i"
%include "std_set.i"

%include "shared/LibraryInfo.h"
%include "shared/Provenance.h"
%include "INodes.h"
%include "PythonInterface.h"

namespace std {
    %template(charVector) vector<string>;
    %template(longSet) set<long>;
    %template(provVec) vector<VnV::ProvFile>; 
}


%pythoncode %{

import json
import numpy as np
import os


class classIterator :
         def __init__(self, obj):
           self.obj = obj
           self.iterData = []
           self.iterCounter = 0
           for name in dir(obj):
             if name.startswith("get"):
               self.iterData.append(name[3:])

         def __next__(self):
           if (self.iterCounter) < len(self.iterData):
              key = self.iterData[self.iterCounter]
              self.iterCounter += 1
              return [key,self.obj[key]]
           else:
              raise StopIteration

class mapclassIterator:
    def __init__(self,obj):
         self.obj = obj
         self.iterCounter = 0
         self.iterData = self.obj.keys();

    def __next__(self):
         if (self.iterCounter < len(self.iterData)):
           key = self.iterData[self.iterCounter]
           self.iterCounter += 1
           return key
         else:
           raise StopIteration

class listclassIterator :
         def __init__(self, obj):
           self.obj = obj
           self.iterCounter = 0

         def __next__(self):
           if (self.iterCounter) < len(self.obj):
                self.iterCounter += 1
                return self.obj[self.iterCounter - 1]

           else:
              raise StopIteration

class shapeClassIterator:
         def __init__(self, obj):
           self.obj = obj
           self.iterCounter = 0
           self.shape = json.loads(self.obj.getShapeJson())
           if len(self.shape)==0:
               raise TypeError("Cannot iterate a Scalar Shape class")
         

         def __next__(self):

           if (self.iterCounter) < self.shape[-1]:
                self.iterCounter += 1
                return self.obj[self.iterCounter - 1]

           else:
              raise StopIteration


dataBaseCastMap = {
    DataBase.DataType_Bool : "AsBoolNode",
    DataBase.DataType_Integer : "AsIntegerNode",
    DataBase.DataType_Float : "AsFloatNode",
    DataBase.DataType_Double : "AsDoubleNode",
    DataBase.DataType_String : "AsStringNode",
    DataBase.DataType_Long : "AsLongNode",
    DataBase.DataType_Shape : "AsShapeNode",
    DataBase.DataType_Json : "AsJsonNode",
    DataBase.DataType_Array : "AsArrayNode",
    DataBase.DataType_Map : "AsMapNode",
    DataBase.DataType_Log : "AsLogNode",
    DataBase.DataType_InjectionPoint : "AsInjectionPointNode",
    DataBase.DataType_Info : "AsInfoNode",
    DataBase.DataType_Workflow : "AsWorkflowNode",
    DataBase.DataType_CommInfo : "AsCommInfoNode",
    DataBase.DataType_Test : "AsTestNode",
    DataBase.DataType_UnitTest : "AsUnitTestNode",
    DataBase.DataType_Data : "AsDataNode",
    DataBase.DataType_Root : "AsRootNode"
}

type2Str = {
    DataBase.DataType_Bool : "Bool",
    DataBase.DataType_Integer : "Integer",
    DataBase.DataType_Float : "Float",
    DataBase.DataType_Double : "DoubleNode",
    DataBase.DataType_String : "StringNode",
    DataBase.DataType_Long : "Long",
    DataBase.DataType_Array : "Array",
    DataBase.DataType_Map : "Map",
    DataBase.DataType_Log : "Log",
    DataBase.DataType_InjectionPoint : "InjectionPoint",
    DataBase.DataType_Info : "Info",
    DataBase.DataType_Workflow : "Workflow",
    DataBase.DataType_CommInfo : "CommInfo",
    DataBase.DataType_Test : "Test",
    DataBase.DataType_Shape : "Shape",
    DataBase.DataType_UnitTest : "UnitTest",
    DataBase.DataType_Data : "DataNode",
    DataBase.DataType_Root : "RootNode"
}

def igetattr(obj, attr):
   if not hasattr(obj, attr): 
      res = []
      for a in dir(obj):
         if a.lower() == attr.lower():
            res.append(a)
      if len(res)==1:
         print("Warning: Case Insensitive Match -- You typed " + attr + " when you should have typed " + res[0])
         print("Warning: We are automatically using the correct value. Please fix to avoid issues in the future")
         return getattr(obj,res[0]) # Only one match so use it (case insensitive)
      elif len(res)>1:         
         raise KeyError("Key '" + attr + "' is ambiguous.: Did you mean: " + str(res))   
      raise KeyError("Key '" + attr + "' not Found.")
   return getattr(obj,attr)


def Read(filename,reader,config):

   if reader is None:
      raise RuntimeError("No Ready")
 
   return ReaderWrapper(filename,reader,config)


def castDataBase(obj) :
    return igetattr(obj, "get" + dataBaseCastMap[obj.getType()])(obj)

%}

%extend VnV::Nodes::DataBase {
  %pythoncode %{
     def cast(self):
         return castDataBase(self)

  %}
}


%define PY_GETATTR(Typename)
%extend Typename {
  %pythoncode %{

      def __str__(self):
           return str(self.getValue())

      def __json__(self):
         a = {}
         for i in self.keys():
            try:
               it = self.__getitem__(i)
               if hasattr(it,"cast"):
                  a[i] = it.cast().__json__()
               else:
                  try:
                     json.dumps(it)
                     a[i] = it
                  except:
                     pass
            except:
                  pass 

      def __getitem__(self,key):
         
         if key == "metaData" or key == "MetaData":
            return json.loads(self.getMetaData().asJson())

         if isinstance(key,str) and key[0] == "_":
            return str(self.getMetaData().get(key[1:]))

         res = igetattr(self,"get"+key)
         if res is not None:
            
            if hasattr(self,"isJson") and self.isJson():
              return json.loads(res())
            return res()

         print("Not a key {} {} ".format(key, self.__class__))
         raise KeyError("not a valid key")

      def __getType__(self):
         return "object"

      def __len__(self):
         count = 0
         for name in dir(self):
                if name.startswith('get'):
                     count+=1
         return count

      def __iter__(self):
        return classIterator(self)

      def values(self):
         res = []
         for name in self.keys():
              res.append(self.__getitem__(name))
         return res

      def keys(self):
         res = []
         for name in dir(self):
            if name.startswith('get'):
               res.append(name[3:])
         return res

      def __contains__(self,item):
         res = hasattr(self,"get" + item)
         if not res and hasattr(self,"get", item.capitalize()):
                print("We dont have {i} but we do have {rr}".format(ii=item, rr=item.captialize()))
         return res

   %}
}
%enddef

// Make these have iterators and getattr:

PY_GETATTR(VnV::Nodes::IRootNode)
PY_GETATTR(VnV::Nodes::IUnitTestNode)
PY_GETATTR(VnV::Nodes::IDataNode)
PY_GETATTR(VnV::Nodes::ILogNode)
PY_GETATTR(VnV::Nodes::IInjectionPointNode)
PY_GETATTR(VnV::Nodes::ITestNode)
PY_GETATTR(VnV::Nodes::IInfoNode)
PY_GETATTR(VnV::Nodes::IWorkflowNode)
PY_GETATTR(VnV::Nodes::ICommInfoNode)

%define PY_GETATTRLIST(Typename)
%extend Typename {
  %pythoncode %{
      
      def __getitem__(self,key):
        if key == "metaData" or key == "MetaData":
            return json.loads(self.getMetaData().asJson())

        if isinstance(key,str) and key[0] == "_":
            return str(self.getMetaData().get(key[1:]))

        if isinstance(key,int) and abs(key) < self.size() :
          if (key < 0 ) :
             key = self.size() + key
          return castDataBase(self.get(key))

        elif isinstance(key,slice):
           sli = range(0,self.size())[slice]
           res = []
           for item in sli:
             res.append(self.__getitem__(item));
           return res

        elif isinstance(key,str):

           res = []
           for i in self:
             if i.getName() == key:
               res.append(i)
           if len(res) == 1:
              return res[0]
           elif len(res)>1:
              return res

        print("Not a key {} {} ".format(key, self.__class__))
        raise KeyError("not a valid key")

      def __len__(self):
        return self.size()

      def __iter__(self):
        return listclassIterator(self)

      def __getType__(self):
        return "array"

      def __str__(self):
          return self.toString()
   
      def __json__(self):
         return json.loads(self.toString())


   %}
}
%enddef

PY_GETATTRLIST(VnV::Nodes::IArrayNode)


%define PY_GETATTRMAP(Typename)
%extend Typename {
    %pythoncode %{

        def __getitem__(self,key):
            if key == "metaData" or key == "MetaData":
              return json.loads(self.getMetaData().asJson())
         
            if isinstance(key,str) and key[0] == "_":
               return str(self.getMetaData().get(key[1:]))

            
            if isinstance(key,str) and self.contains(key):
                return castDataBase(self.get(key))
            print("Not a key {} {} ".format(key, self.__class__))
            raise KeyError("not a valid key")

        def __len__(self):
            return self.size();

        def __iter__(self):
            return mapclassIterator(self)

        def __getType__(self):
            return "object"

        def values(self):
            res = []
            for name in self.keys():
                res.append(castDataBase(self.get(name)))
            return res

        def keys(self):
             res = []
             for name in self.fetchkeys():
                res.append(name)
             return res

        def __contains__(self,item):
             return self.contains(item)

        def __str__(self):
            return self.toString() 
    
        def __json__(self):
         return json.loads(self.toString())
          
   %}
}
%enddef
PY_GETATTRMAP(VnV::Nodes::IMapNode)


%define PY_GETATTRWORK(Typename)
%extend Typename {
    %pythoncode %{

        def __getitem__(self,key):

            if isinstance(key,str) and self.hasReport(key):
                return castDataBase(self.getReport(key))
            
            print("Not a key {} {} ".format(key, self.__class__))
            raise KeyError("not a valid key")

        def __len__(self):
            return self.size();

        def __iter__(self):
            return mapclassIterator(self)

        def __getType__(self):
            return "object"

        def values(self):
            res = []
            for name in self.keys():
                res.append(castDataBase(self.getReport(name)))
            return res

        def keys(self):
             res = []
             for name in self.listReports():
                res.append(name)
             return res

        def __contains__(self,item):
             return self.hasReport(item)

        def __str__(self):
            return str({ a : str(self.__getitem__(a)) for a in self.keys() })

        def __json__(self):
         return { a : self.__getitem__(a).__json__() for a in self.keys()()}
          
   %}
}
%enddef
PY_GETATTRWORK(VnV::Nodes::IWorkflowNode)



%define PY_GETATTRSHAPE(Typename)
%extend Typename {
  %pythoncode %{

      def recursive_pop(self, b):
        result = []
        for i in b:
          if isinstance(i,list):
             result.append(self.recursive_pop(i))
          else:
             result.append(self.valueIsJson(self.getValueByIndex(i)))
        return result

      def getValue(self):
         s,t,nps = self.shape()
         if len(s) == 0:
            return self.valueIsJson(self.getScalarValue())
         else:
            res = []
            for i in range(0,t):
               res.append(self.valueIsJson(self.getValueByIndex(i)))
            return np.asarray(res).reshape(s).tolist()   

      def shape(self):
         if not hasattr(self, "shapeval"):
            self.shapeval = json.loads(self.getShapeJson());
            self.tot = self.getNumElements()
            if len(self.shapeval) > 0:
               self.npshape = np.reshape(range(0,self.tot), tuple(self.shapeval) ) #array with values as correct index.
            else:
               self.npshape = None
         return self.shapeval, self.tot, self.npshape

      def valueIsJson(self, value):
         if self.getTypeStr() == "Json":
            return json.loads(value)
         return value
         
      def __getitem__(self,key):
        
        if isinstance(key,str):
           if  key.lower() == "metadata":
               return json.loads(self.getMetaData().asJson()) 
           elif key.lower() == "value":
               return self.getValue()
           elif key[0] == "_":
               return str(self.getMetaData().get(key[1:]))
           else:
               res = igetattr(self,"get"+key)
               if res is not None:
                  return res()
               raise KeyError("Unknown String Key " + key + " in " + str(self.__class__))   


        # Now we assume we have a slice of some kind.   
        try:
        
          s,t,nps = self.shape()
        
          if nps is None :
            if key == 0:
               return self.getValue();
          else:
            b = nps[key].tolist() # Slice the array

            # If b is a list, we need to extract the values recursivly.
            if (isinstance(b,list)):
               return np.ndarray(self.recursive_pop(b))
            else:
               return self.valueIsJson(self.getValueByIndex(b))
        
        except:
             pass

        raise KeyError("not a valid key " + str(key))

      def __len__(self):
         if self.getValue():
            return True
         return False 

      def __iter__(self):
        return shapeClassIterator(self)

      def __getType__(self):
        return "array"

      def __str__(self):
          return str(self.__json__())

      def __sub__(self, b):
         return self.getValue() - b

      def __rsub__(self, b):
        return b - self.getValue()

      def __add__(self, b):
        return self.getValue() + b

      def __radd(self, b):
        return b + self.getValue()

      def __mult__(self, b):
        return self.getValue()*b

      def __rmult__(self, b):
        return b* self.getValue()


      def __json__(self):
   
         s,t,nps = self.shape()
         if len(s) == 0:
            return json.loads(self.toString()) 
         else:
            res = []
            for i in range(0,t):
               a = self.valueIsJson(self.getValueByIndex(i))
               if hasattr(a,"cast") and hasattr(a.cast(),"__json__"):
                  res.append(a.cast().__json__())
               else:
                  res.append(a)
            return np.asarray(res).reshape(s).tolist()   
   %}
}
%enddef



PY_GETATTRSHAPE(VnV::Nodes::IDoubleNode)
PY_GETATTRSHAPE(VnV::Nodes::IIntegerNode)
PY_GETATTRSHAPE(VnV::Nodes::IFloatNode)
PY_GETATTRSHAPE(VnV::Nodes::IStringNode)
PY_GETATTRSHAPE(VnV::Nodes::ILongNode)
PY_GETATTRSHAPE(VnV::Nodes::IBoolNode)
PY_GETATTRSHAPE(VnV::Nodes::IJsonNode)
PY_GETATTRSHAPE(VnV::Nodes::IShapeNode)
