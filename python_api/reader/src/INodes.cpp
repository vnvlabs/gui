

#include "INodes.h"

#include <iostream>
#include <sstream>

#include "shared/exceptions.h"
#include "shared/nlohmann/json.hpp"

namespace VnV {
namespace Nodes {

bool DataBase::check(DataType type) { return type == getType(); }

std::string DataBase::getName() {
  std::string n = getNameInternal();
  return (n.empty()) ? std::to_string(getId()) : n;
}

DataBase::DataBase(DataType type) : dataType(type) {}

DataBase::DataType DataBase::getType() { return dataType; }

DataBase::DataType DataBase::getDataTypeFromString(std::string s) {
  if (s.compare("") == 0) {
  }
#define X(x, y)                  \
  else if (s.compare(#x) == 0) { \
    return DataType::x;          \
  }
  DTYPES
#undef X
#define X(x)                     \
  else if (s.compare(#x) == 0) { \
    return DataType::x;          \
  }
  STYPES
  RTYPES
#undef X
  throw INJECTION_EXCEPTION("Unknown Datatype %s", s.c_str());
}

std::string DataBase::getTypeStr() {
  switch (getType()) {
#define X(x, y)     \
  case DataType::x: \
    return #x;
    DTYPES
#undef X
#define X(x)        \
  case DataType::x: \
    return #x;
    STYPES
    RTYPES
#undef X
  default:
    return "Custom";
  }
  throw INJECTION_BUG_REPORT_("Impossible");
}

#define X(x, y)                                                                         \
  I##x##Node::I##x##Node() : DataBase(DataBase::DataType::x) {}                         \
  I##x##Node::~I##x##Node() {}                                                          \
  std::shared_ptr<I##x##Node> DataBase::getAs##x##Node(std::shared_ptr<DataBase> ptr) { \
    if (check(DataType::x)) return std::dynamic_pointer_cast<I##x##Node>(ptr);          \
    throw INJECTION_EXCEPTION("Invalid Cast to DataType::%s from %s ", #x, dataType);   \
  }
DTYPES
#undef X

std::string IStringNode::valueToString(std::string ind) { return ind; }

std::string IJsonNode::valueToString(std::string ind) { return ind; }
std::string IShapeNode::valueToString(std::shared_ptr<DataBase> ind) { return ind->toString(); }

template <typename T, typename V> json toJ(std::vector<std::size_t> curr, V* cls, const std::function<json(T)>& func) {
  auto& sh = cls->getShape();
  if (sh.size() == 0) return func(cls->getScalarValue());

  json jj = json::array();

  curr.push_back(0);
  for (int i = 0; i < sh[curr.size() - 1]; i++) {
    curr.back() = i;
    if (curr.size() == sh.size()) {
      jj.push_back(func(cls->getValueByShape(curr)));
    } else {
      jj.push_back(toJ(curr, cls, func));
    }
  }
  return jj;
}

json IStringNode::toJson() {
  return toJ<std::string, IStringNode>({}, this, [](std::string x) { return x; });
}
json IJsonNode::toJson() {
  return toJ<std::string, IJsonNode>({}, this, [](std::string x) { return json::parse(x); });
}

json IShapeNode::toJson() {
  return toJ<std::shared_ptr<DataBase>, IShapeNode>({}, this, [](std::shared_ptr<DataBase> x) { return x->toJson(); });
}

#define SDTYPES X(Bool, bool) X(Integer, int) X(Float, float) X(Double, double) X(Long, long)
#define X(x, y)                                                                \
  std::string I##x##Node::valueToString(y ind) { return std::to_string(ind); } \
  json I##x##Node::toJson() {                                                  \
    return toJ<y, I##x##Node>({}, this, [](y op) { return op; });              \
  }
SDTYPES
#undef X
#undef SDTYPES

#define X(x)                                                                            \
  I##x##Node::I##x##Node() : DataBase(DataBase::DataType::x) {}                         \
  I##x##Node::~I##x##Node() {}                                                          \
  std::shared_ptr<I##x##Node> DataBase::getAs##x##Node(std::shared_ptr<DataBase> ptr) { \
    if (check(DataType::x)) return std::dynamic_pointer_cast<I##x##Node>(ptr);          \
    throw INJECTION_EXCEPTION("Invalid Cast to DataType::%s -> %s", #x, dataType);      \
  }
STYPES
RTYPES
#undef X

DataBase::~DataBase() {}

void IArrayNode::iter(std::function<void(std::shared_ptr<DataBase>)>& lambda) {
  for (std::size_t i = 0; i < size(); i++) {
    lambda(get(i));
  }
}


json IWorkflowNode::getDataChildren_(int fileId, int level) {
  json j = DataBase::getDataChildren_(fileId, level);
  {
      json jj = json::object();
      jj["text"] ="Package: " + getPackage();
      jj["icon"] = "feather icon-package";
      j.push_back(jj);
   }
   {
      json jj = json::object();
      jj["text"] ="Info :" + getInfo().dump();
      jj["icon"] = "feather icon-info";
      j.push_back(jj);
   }
   {
      json jj = json::object();
      jj["text"] ="State: " + getState();
      jj["icon"] = "feather icon-minus";
      j.push_back(jj);
   }
   {

        json jj = json::object();
        jj["text"] = "Report";
        jj["children"] = json::array();
        jj["icon"] = "feather icon-list";
        for (auto it : listReports()) {
            auto r = getReport(it);
            if (r != nullptr) {
                int i = getReportFileId(it);
                auto a = r->getAsDataChild(i, level - 1);
                a["text"] = it;
                jj["children"].push_back(a);
            }
        }
        if (jj["children"].size() > 0 ) {
            j.push_back(jj);
        }
    }
  

  return j;
}

int Node_Type_To_Int(node_type t) {
  switch (t) {
  case node_type::ROOT:
    return 0;
  case node_type::POINT:
    return 1;
  case node_type::START:
    return 2;
  case node_type::ITER:
    return 3;
  case node_type::END:
    return 4;
  case node_type::LOG:
    return 5;
  case node_type::WAITING:
    return 6;
  case node_type::DONE:
    return 7;
  }
  throw INJECTION_BUG_REPORT_("unsupported node type in serialization");
}

node_type Node_Type_From_Int(int i) {
  switch (i) {
  case 0:
    return node_type::ROOT;
  case 1:
    return node_type::POINT;
  case 2:
    return node_type::START;
  case 3:
    return node_type::ITER;
  case 4:
    return node_type::END;
  case 5:
    return node_type::LOG;
  case 6:
    return node_type::WAITING;
  case 7:
    return node_type::DONE;
  }
  throw INJECTION_EXCEPTION("unrecognized int in node_type deserialization (%d)", i);
}


}  // namespace Nodes
}  // namespace VnV
