#ifndef NODES_H
#define NODES_H

#include <assert.h>

#include <functional>
#include <iostream>
#include <list>
#include <map>
#include <memory>
#include <set>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

// TODO
#include "shared/Provenance.h"
#include "shared/exceptions.h"
#include "shared/nlohmann/json.hpp"

#define ID_NOT_INITIALIZED_YET -1000

#define GETTERSETTER(NAME, type)                          \
  void set##NAME(const type &NAME) { this->NAME = NAME; } \
  const type &get##NAME() { return this->NAME; }

namespace VnV
{

  namespace Nodes
  {

    enum class node_type
    {
      ROOT,
      POINT,
      START,
      ITER,
      END,
      LOG,
      WAITING,
      DONE
    };

    int Node_Type_To_Int(node_type t);
    node_type Node_Type_From_Int(int i);

    class IDN
    {
    public:
      long id;
      long streamId;
      node_type type;
      std::string stage;

      IDN(long a, long b, node_type c, std::string e) : id(a), streamId(b), type(c), stage(e) {}

      IDN() : id(-1), streamId(-1), type(node_type::ROOT), stage("") {}

      IDN(nlohmann::json &j)
      {
        id = j["id"].get<long>();
        streamId = j["streamId"].get<long>();
        stage = j["stage"].get<std::string>();
        type = Node_Type_From_Int(j["type"].get<int>());
      }
    };

    class VisitorLock
    {
    public:
      VisitorLock() {}
      virtual ~VisitorLock() {}
      virtual void lock() = 0;
      virtual void release() = 0;
    };

    class MetaDataWrapper
    {
      std::map<std::string, std::string> m;

    public:
      std::string const get(std::string key)
      {
        auto it = m.find(key);
        if (it != m.end())
        {
          return it->second;
        }
        throw INJECTION_EXCEPTION("Metadata key %s does not exist", key.c_str());
      }
      bool has(std::string key) const { return (m.find(key) != m.end()); }

      MetaDataWrapper &add(std::string key, std::string value)
      {
        m.insert(std::make_pair(key, value));
        return *this;
      }

      void fromJson(json &val)
      {
        m.clear();
        for (auto it : val.items())
        {
          m[it.key()] = it.value().get<std::string>();
        }
      }

      std::string asJson() const
      {
        nlohmann::json j = m;
        return j.dump();
      }

      json toJson() const { return m; }

      std::size_t size() const { return m.size(); }

      json getAsDataChild() const
      {

        json k = json::array();
        for (auto it : m)
        {
          json kj = json::object();
          kj["text"] = it.first + ": " + it.second;
          kj["icon"] = "feather icon-minus";
          k.push_back(kj);
        }

        json j = json::object();
        j["text"] = "Meta Data";
        j["icon"] = "feather icon-map";
        j["children"] = k;
        return j;
      }
    };

#define DTYPES           \
  X(Bool, bool)          \
  X(Integer, int)        \
  X(Float, float)        \
  X(Double, double)      \
  X(String, std::string) \
  X(Json, std::string)   \
  X(Long, long)          \
  X(Shape, std::shared_ptr<DataBase>)
#define STYPES      \
  X(Array)          \
  X(Map)            \
  X(Log)            \
  X(InjectionPoint) \
  X(Info)           \
  X(CommInfo)       \
  X(Test)           \
  X(UnitTest)       \
  X(Workflow)       \
  X(Data) X(UnitTestResult) X(UnitTestResults)
#define RTYPES X(Root)

#define X(x, y) class I##x##Node;
    DTYPES
#undef X
#define X(x) class I##x##Node;
    STYPES
    RTYPES
#undef X

    class DataBase
    {
    public:
      enum class DataType
      {
#define X(x, y) x,
        DTYPES
#undef X
#define X(x) x,
            STYPES
#undef X
                Root
      };

    private:
      DataType dataType;

    protected:
      IRootNode *_rootNode = nullptr;

      IRootNode *rootNode() { return _rootNode; }

      long id = ID_NOT_INITIALIZED_YET;

    public:
      DataBase(DataType type);
      virtual ~DataBase();

#define X(x, y) virtual std::shared_ptr<I##x##Node> getAs##x##Node(std::shared_ptr<DataBase> ptr);
      DTYPES
#undef X
#define X(x) virtual std::shared_ptr<I##x##Node> getAs##x##Node(std::shared_ptr<DataBase> ptr);
      STYPES
      RTYPES
#undef X

      virtual std::string getUsageType() { return getTypeStr(); }

      virtual long getId() { return id; }
      virtual const MetaDataWrapper &getMetaData() = 0;
      virtual long getStreamId() = 0;

      virtual bool getopen() = 0;
      virtual void setopen(bool value) = 0;

      virtual std::string getNameInternal() = 0;

      virtual DataType getType();
      virtual std::string getName();

      virtual std::string getDisplayName() { return getName(); }
      virtual std::string getValueDisplay() { return getDisplayName(); }
      virtual std::string getTypeStr();

      static DataBase::DataType getDataTypeFromString(std::string s);

      virtual void open(bool value) { setopen(value); }

      virtual bool check(DataType type);

      virtual void setRootNode(long id, IRootNode *rootNode)
      {
        this->_rootNode = rootNode;
        this->id = id;
      }

      virtual json toJson() { return getId(); }
      virtual std::string toString() { return toJson().dump(); }

      std::string getDataChildren(int fileId, int level) { return getDataChildren_(fileId, level).dump(); }

      virtual json getDataChildren_(int fileId, int level)
      {
        json a = json::array();
        if (getMetaData().size() > 0)
        {
          a.push_back(getMetaData().getAsDataChild());
        }
        return a;
      }

      virtual std::string icon() { return "folder"; }

      virtual json getAsDataChild(int fileId, int level)
      {
        json j = json::object();

        j["text"] = getDisplayName();
        j["icon"] = "feather icon-" + icon();

        if (level > 0)
        {
          j["children"] = getDataChildren_(fileId, level - 1);
        }
        else
        {
          j["children"] = getDataChildren_(fileId, level - 1).size() > 0;
        }

        j["li_attr"] = json::object();
        j["li_attr"]["nodeId"] = getId();
        j["li_attr"]["fileId"] = fileId;
        return j;
      }
    };

#define X(X, x)                                                           \
  class I##X##Node : public DataBase                                      \
  {                                                                       \
  public:                                                                 \
    I##X##Node();                                                         \
    virtual const std::vector<std::size_t> &getShape() = 0;               \
    virtual x getValueByShape(const std::vector<std::size_t> &shape) = 0; \
    virtual x getValueByIndex(const std::size_t ind) = 0;                 \
    std::string valueToString(x ind);                                     \
    virtual x getScalarValue() = 0;                                       \
    virtual int getNumElements() = 0;                                     \
    json toJson() override;                                               \
    virtual ~I##X##Node();                                                \
    virtual std::string getShapeJson()                                    \
    {                                                                     \
      nlohmann::json j = this->getShape();                                \
      return j.dump();                                                    \
    }                                                                     \
    virtual std::string getDisplayName() override                         \
    {                                                                     \
      if (getShape().size() == 0)                                         \
      {                                                                   \
        return valueToString(getScalarValue());                           \
      }                                                                   \
      return getName() + ": Shape " + getShapeJson();                     \
    }                                                                     \
    virtual void add(const x &s) = 0;                                     \
    virtual std::string getValueDisplay()                                 \
    {                                                                     \
      if (getShape().size() == 0)                                         \
      {                                                                   \
        return valueToString(getScalarValue());                           \
      }                                                                   \
      else                                                                \
      {                                                                   \
        return getShapeJson();                                            \
      }                                                                   \
    }                                                                     \
    virtual json getDataChildren_(int fileId, int level) override         \
    {                                                                     \
                                                                          \
      json ch = DataBase::getDataChildren_(fileId, level);                \
      {                                                                   \
        json j = json::object();                                          \
        if (getShape().size() == 0)                                       \
        {                                                                 \
          j["text"] = "Value: " + valueToString(getScalarValue());        \
        }                                                                 \
        else                                                              \
        {                                                                 \
          j["text"] = "Shape: " + getShapeJson();                         \
        }                                                                 \
        j["icon"] = "feather icon-minus";                                 \
        ch.push_back(j);                                                  \
      }                                                                   \
      return ch;                                                          \
    }                                                                     \
  };
    DTYPES
#undef X

    // ArrayNode is an array of DataNodes.
    class IArrayNode : public DataBase
    {
    public:
      IArrayNode();
      virtual std::shared_ptr<DataBase> get(std::size_t idx) = 0;
      virtual std::size_t size() = 0;
      virtual void add(std::shared_ptr<DataBase> data) = 0;
      virtual ~IArrayNode();

      void iter(std::function<void(std::shared_ptr<DataBase>)> &lambda);
      virtual std::string icon() { return "list"; }

      virtual std::string getValueDisplay() override  { return std::to_string(size()) +" elements"; }

      virtual json getDataChildren_(int fileId, int level) override
      {

        json ch = DataBase::getDataChildren_(fileId, level);
        for (int i = 0; i < size(); i++)
        {
          ch.push_back(get(i)->getAsDataChild(fileId, level - 1));
          ch.back()["text"] = std::to_string(i)+ ": " + get(i)->getValueDisplay();
          ch.back()["icon"] = "feather icon-minus";
          
        }
        return ch;
      }

      virtual json toJson() override
      {
        json j = json::array();
        for (int i = 0; i < size(); i++)
        {
          j[i] = get(i)->toJson();
        }

        return j;
      }

      void open(bool value) override
      {
        DataBase::open(value);

        // Open MP parallel for
        for (int i = 0; i < size(); i++)
        {
          get(i)->open(value);
        }
      }
    };

    class IMapNode : public DataBase
    {
    protected:
      template <typename T>
      bool convertToShapeNode(std::shared_ptr<DataBase> parent, std::shared_ptr<DataBase> child)
      {
        // Right now we only support collate for scalar values.

        std::shared_ptr<T> c = std::dynamic_pointer_cast<T>(child);

        if (c->getShape().size() > 0)
          return false;

        c->getScalarValue();

        // Right now we can only collate scalars.
        auto p = std::dynamic_pointer_cast<T>(parent);
        auto sh = p->getShape();

        if (sh.size() == 0)
        {
          p->setShape({2});
          p->add(c->getScalarValue());
          return true;
        }
        else if (sh.size() == 1)
        {
          p->setShape({sh[0] + 1});
          p->add(c->getScalarValue());
          return true;
        }
        return false;
      }

    public:
      IMapNode();
      virtual std::shared_ptr<DataBase> get(std::string key) = 0;
      virtual std::string icon() { return "map"; }

      virtual void insert(std::string key, std::shared_ptr<DataBase> val) = 0;

      virtual bool contains(std::string key) = 0;
      virtual std::vector<std::string> fetchkeys() = 0;
      virtual std::size_t size() = 0;

      virtual std::string getValueDisplay() override  { return std::to_string(size())  +" keys"; }

      virtual json getDataChildren_(int fileId, int level) override
      {
        json j = DataBase::getDataChildren_(fileId, level);
        json ch = json::array();
        for (auto it : fetchkeys())
        {
          ch.push_back(get(it)->getAsDataChild(fileId, level - 1));
          ch.back()["text"] = it + ": " + get(it)->getValueDisplay();
          ch.back()["icon"] = "feather icon-minus";

        }
        return ch;
      }

      virtual json toJson() override
      {
        json j = json::object();
        auto keys = fetchkeys();
        for (int i = 0; i < keys.size(); i++)
        {
          j[keys[i]] = get(keys[i])->toJson();
        }
        return j;
      }

      void open(bool value) override
      {
        DataBase::open(value);
        for (auto &it : fetchkeys())
        {
          get(it)->open(value);
        }
      }

      virtual ~IMapNode();
    };

    class IDataNode : public DataBase
    {
    public:
      IDataNode();
      virtual std::shared_ptr<IArrayNode> getLogs() = 0;
      virtual std::shared_ptr<IMapNode> getData() = 0;
      virtual long long getDataTypeKey() = 0;
      virtual bool getLocal() = 0;
      virtual ~IDataNode();
      virtual std::string icon() { return "database"; }

      virtual json getDataChildren_(int fileId, int level) override
      {

        json j = DataBase::getDataChildren_(fileId, level);
        if (getLogs()->size() > 0)
        {
          j.push_back(getLogs()->getAsDataChild(fileId, level - 1));
          j.back()["text"] = "Logs";
        }
        if (getData()->size() > 0)
        {
          j.push_back(getData()->getAsDataChild(fileId, level - 1));
          j.back()["text"] = "Data";
        }
        return j;
      }

      virtual std::string toString() override { return getData()->toString(); }

      virtual void open(bool value) override
      {
        DataBase::open(value);
        getLogs()->open(value);
        getData()->open(value);
      }
    };

    class IInfoNode : public DataBase
    {
    protected:
      virtual std::shared_ptr<VnV::VnVProv> getProvInternal() = 0;

    public:
      IInfoNode();
      virtual std::string getTitle() = 0;
      virtual long getStartTime() = 0;
      virtual long getEndTime() = 0;
      virtual std::string getWorkflow() = 0;
      virtual std::string getJobName() = 0;
      virtual std::string getFileStub() = 0;
      virtual std::string icon() { return "info"; }

      virtual json getDataChildren_(int fileId, int level) override
      {
        double durr = (double)(getEndTime() - getStartTime());
        durr = durr / 1000;

        json j = DataBase::getDataChildren_(fileId, level);
        {
          json jj = json::object();
          jj["text"] = "Title: " + getTitle();
          jj["icon"] = "feather icon-italic";
          j.push_back(jj);
        }
        {
          json jj = json::object();
          jj["text"] = "Start Time (seconds since epoch): " + std::to_string(getStartTime() / 1000);
          jj["icon"] = "feather icon-watch";
          j.push_back(jj);
        }
        {
          json jj = json::object();
          jj["text"] = "Unix End Time (seconds since epoch): " + std::to_string(getEndTime() / 1000);
          jj["icon"] = "feather icon-watch";
          j.push_back(jj);
        }
        {
          json jj = json::object();
          jj["text"] = "Total Duration:" + std::to_string(durr) + " s";
          jj["icon"] = "feather icon-watch";
          j.push_back(jj);
        }
        {
          json jj = json::object();
          jj["text"] = "Workflow ID: " + getWorkflow();
          jj["icon"] = "feather icon-italic";
          j.push_back(jj);
        }
        {
          json jj = json::object();
          jj["text"] = "JobName: " + getJobName();
          jj["icon"] = "feather icon-italic";
          j.push_back(jj);
        }
        {
          json jj = json::object();
          jj["text"] = "FileStub: " + getFileStub();
          jj["icon"] = "feather icon-file";
          j.push_back(jj);
        }

        j.push_back(getProvInternal()->getDataChildren());
        j.back()["text"] = "Provenance";
        return j;
      }

      virtual void addInputFile(std::shared_ptr<ProvFile> pv)
      {
        getProv()->addInputFile(pv);
      }
      virtual void addOutputFile(std::shared_ptr<ProvFile> pv)
      {
        getProv()->addOutputFile(pv);
      }

      std::shared_ptr<VnV::VnVProv> getProv() { return getProvInternal(); }

      virtual ~IInfoNode();
    };

    class ICommMap
    {
    public:
      ICommMap() {}
      virtual void add(long id, const std::set<long> &comms) = 0;
      virtual nlohmann::json toJson(bool strip) const = 0;

      virtual bool commContainsProcessor(long commId, long proc) const = 0;
      virtual bool commContainsComm(long commParent, long commChild) const = 0;
      virtual std::set<long> commChain(long comm) const = 0;
      virtual bool commIsChild(long parentId, long childId) const = 0;
      virtual bool commIsSelf(long streamId, long proc) const = 0;
      virtual bool commsIntersect(long streamId, long comm) const = 0;

      virtual nlohmann::json listComms() const = 0;

      virtual ~ICommMap() {}

      virtual std::string getComms() const { return listComms().dump(); }
      virtual std::string toJsonStr(bool strip) const = 0;

      virtual json getAsDataChild(int fileId, int level) 
      {
        json j = json::object();
        j["text"] = "Communicators";
        j["icon"] = "feather icon-info";
    
        json a = json::array();
        auto comms = listComms();

        for (auto &it : comms.items() ) {
            json jj = json::object();
            jj["text"] = it.key() + ": " + it.value().dump();
            jj["icon"] = "feather icon-cpu";
            a.push_back(jj);
        }
        j["children"] = a;
        
        return j;
      }
    };

    class ICommInfoNode : public DataBase
    {
    protected:
      virtual std::shared_ptr<ICommMap> getCommMapInternal() = 0;

    public:
      ICommInfoNode();
      virtual int getWorldSize() = 0;

      virtual std::shared_ptr<const ICommMap> getCommMap() { return getCommMapInternal(); };

      virtual void add(long id, const std::set<long> &comms) { getCommMapInternal()->add(id, comms); }

      virtual std::string getNodeMap() = 0;
      virtual std::string getVersion() = 0;

      virtual std::string icon() { return "cpu"; }

      virtual json getDataChildren_(int fileId, int level) override
      {
        json j = DataBase::getDataChildren_(fileId, level);
        
        {
          json jj = json::object();
          jj["text"] = "#Processors " + std::to_string(getWorldSize());
          jj["icon"] = "feather icon-hash";
          j.push_back(jj);
        }
        {
          json jj = json::object();
          jj["text"] = "MPI Version: " + getVersion();
          jj["icon"] = "feather icon-info";
          j.push_back(jj);
        }
        {
          j.push_back(getCommMapInternal()->getAsDataChild(fileId, level - 1));
        }
        return j;
      }

      virtual ~ICommInfoNode();
    };

    class FetchRequest
    {
    public:
      std::string schema;
      long id;
      long jid;
      long expiry;
      std::string message;

      FetchRequest(std::string s, long id_, long jid_, long e, std::string m)
          : schema(s), id(id_), jid(jid_), expiry(e), message(m) {}
      std::string getSchema() { return schema; }
      long getExpiry() { return expiry; }
      long getId() { return id; }
      long getJID() { return jid; }
      std::string getMessage() { return message; }
    };

    class ITestNode : public DataBase
    {
    public:
      enum class TestNodeUsage
      {
        TEST,
        INTERNAL,
        ACTION,
        PACKAGE
      };
      static std::string getUsageString(TestNodeUsage u)
      {
        switch (u)
        {
        case TestNodeUsage::ACTION:
          return "Action";
        case TestNodeUsage::INTERNAL:
          return "Internal";
        case TestNodeUsage::TEST:
          return "Test";
        case TestNodeUsage::PACKAGE:
          return "Package";
        }
        // We should test this never happens
        assert(false && "Error: Forget to add toString condition int testNodeUsage");
        std::abort();
      }

      static TestNodeUsage getUsageFromString(std::string u)
      {
        if (u.compare("Action") == 0)
          return TestNodeUsage::ACTION;
        else if (u.compare("Internal") == 0)
          return TestNodeUsage::INTERNAL;
        else if (u.compare("Test") == 0)
          return TestNodeUsage::TEST;
        else if (u.compare("Package") == 0)
          return TestNodeUsage::PACKAGE;
        throw INJECTION_EXCEPTION("%s is not a valid string representation of any known enum in enum class TestNodeUsage ",
                                  u.c_str());
      }

    protected:
      std::shared_ptr<FetchRequest> fetch = nullptr;
      TestNodeUsage usage = TestNodeUsage::TEST;

    public:
      virtual std::string getUsageType() override { return getUsageString(getUsage()); }

      ITestNode();

      virtual std::shared_ptr<FetchRequest> getFetchRequest()
      {
        if (fetch != nullptr)
        {
          return fetch;
        }
        return nullptr;
      }

      virtual void resetFetchRequest() { fetch.reset(); }

      virtual void setFetchRequest(std::string schema, long id, long jid, long expiry, std::string message)
      {
        fetch.reset(new FetchRequest(schema, id, jid, expiry, message));
      }

      virtual TestNodeUsage getUsage() = 0;
      virtual std::string getPackage() = 0;
      virtual std::shared_ptr<IMapNode> getData() = 0;
      virtual std::shared_ptr<IArrayNode> getLogs() = 0;
      virtual bool isInternal() = 0;
      virtual ~ITestNode();
      virtual std::string icon() { return "check-square"; }

      virtual std::string getDisplayName() override
      {
        return getPackage() + ": " + getName();
      }

      virtual json getDataChildren_(int fileId, int level) override
      {

        json j = DataBase::getDataChildren_(fileId, level);
        if (getLogs()->size() > 0)
        {
          j.push_back(getLogs()->getAsDataChild(fileId, level - 1));
          j.back()["text"] = "Logs";
        }
        if (getData()->size() > 0)
        {
          j.push_back(getData()->getAsDataChild(fileId, level - 1));
          j.back()["text"] = "Data";
        }
        return j;
      }

      virtual void open(bool value) override
      {
        DataBase::open(value);
        getLogs()->open(value);
        getData()->open(value);
      }
    };

    class IWorkflowNode : public DataBase
    {
      std::string jobName;

    public:
      IWorkflowNode();
      virtual std::string getPackage() = 0;
      virtual json getInfo() = 0;
      virtual std::string getState() = 0;
      virtual ~IWorkflowNode();

      virtual std::string getInfoStr() { return getInfo().dump(); }

      virtual json getDataChildren_(int fileId, int level) override;
      virtual std::string icon() { return "navigation"; }

      virtual std::shared_ptr<IRootNode> getReport(std::string reportName) = 0;
      virtual bool hasReport(std::string reportName) = 0;
      virtual void setReport(std::string reportName, int fileId, std::shared_ptr<IRootNode> rootNode) = 0;
      virtual std::vector<std::string> listReports() = 0;
      virtual int getReportFileId(std::string reportName) = 0;
    };

    class IInjectionPointNode : public DataBase
    {
    public:
      IInjectionPointNode();
      virtual long getStartIndex() = 0;
      virtual long getEndIndex() = 0;

      virtual std::string getComm() = 0;
      virtual std::string getPackage() = 0;
      virtual std::shared_ptr<IArrayNode> getTests() = 0;
      virtual std::shared_ptr<IArrayNode> getLogs() = 0;
      virtual std::shared_ptr<ITestNode> getData() = 0;
      virtual ~IInjectionPointNode();

      virtual std::string getDisplayName() override
      {
        return getPackage() + ": " + getName();
      }

      virtual json getDataChildren_(int fileId, int level) override
      {
        json j = DataBase::getDataChildren_(fileId, level);
         {
          json jj = json::object();
          jj["text"] = "Communicator: " + getComm();
          jj["icon"] = "feather icon-cpu";
          j.push_back(jj);
        }
        
        if (getLogs()->size() > 0)
        {
          j.push_back(getLogs()->getAsDataChild(fileId, level - 1));
          j.back()["text"] = "Logs";
        }
        if (getData() != nullptr)
        {
          auto a = getData()->getAsDataChild(fileId, level - 1);
          if (a["children"].size() > 0 ) {
              a["text"] = "Internal Test Data";
              j.push_back(a);
          }
        }
        if (getTests()->size() > 0)
        {
          j.push_back(getTests()->getAsDataChild(fileId, level - 1));
          j.back()["text"] = "Tests";
        }
        return j;
      }
      virtual void open(bool value) override
      {
        DataBase::open(value);
        getLogs()->open(value);
        getData()->open(value);
        getTests()->open(value);
      }
    };

    class ILogNode : public DataBase
    {
    public:
      ILogNode();
      virtual std::string getPackage() = 0;
      virtual std::string getLevel() = 0;
      virtual std::string getMessage() = 0;
      virtual std::string getStage() = 0;
      virtual std::string getComm() = 0;
      virtual ~ILogNode();

      virtual std::string icon() override { return "info"; }

      virtual std::string getDisplayName() override
      {
        return "[" + getLevel() + "][" + getPackage() + "] " + getMessage();
      }

      virtual std::string getValueDisplay() { return getMessage(); }

      virtual json getDataChildren_(int fileId, int level) override
      {
        json j = DataBase::getDataChildren_(fileId, level);
        {
          json jj = json::object();
          jj["text"] = "Communicator: " + getComm();
          jj["icon"] = "feather icon-cpu";
          j.push_back(jj);
        }
        {
          json jj = json::object();
          jj["text"] = "Message: " + getMessage();
          jj["icon"] = "feather icon-message-circle";
          j.push_back(jj);
        }

        return j;
      }
    };

    class IUnitTestResultNode : public DataBase
    {
    public:
      IUnitTestResultNode();
      virtual std::string getDescription() = 0;
      virtual bool getResult() = 0;
      virtual ~IUnitTestResultNode();
      virtual std::string icon() { return "check-square"; }

      virtual json getDataChildren_(int fileId, int level) override
      {
        json j = DataBase::getDataChildren_(fileId, level);
        {
          json jj = json::object();
          jj["text"] = "Description: " + getDescription();
          jj["icon"] = "feather icon-message-circle";
          j.push_back(jj);
        }
        {
          json jj = json::object();
          jj["text"] = "Result: " + std::to_string(getResult());
          jj["icon"] = getResult() ? "feather icon-check-square" : "feather icon-x-square";
          j.push_back(jj);
        }
        return j;
      }
    };

    class IUnitTestResultsNode : public DataBase
    {
    public:
      IUnitTestResultsNode();
      virtual std::shared_ptr<IUnitTestResultNode> get(std::string key) = 0;
      virtual bool contains(std::string key) = 0;
      virtual std::vector<std::string> fetchkeys() = 0;
      virtual ~IUnitTestResultsNode();

      virtual json getDataChildren_(int fileId, int level) override
      {
        json j = DataBase::getDataChildren_(fileId, level);
        if (fetchkeys().size() > 0)
        {
          for (auto it : fetchkeys())
          {
            auto git = get(it);

            json jj = json::object();
            if (git->getResult())
            {
              jj["text"] = "[PASS] " + git->getName() + ": " + git->getDescription();
              jj["icon"] = "feather icon-check-square";
            }
            else
            {
              jj["text"] = "[FAIL] " + git->getName() + ": " + git->getDescription();
              jj["icon"] = "feather icon-x-square";
            }
            j.push_back(jj);
          }
        }
        return j;
      }

      void open(bool value) override
      {
        DataBase::open(value);
        for (auto &it : fetchkeys())
        {
          get(it)->open(value);
        }
      }
    };

    class IUnitTestNode : public DataBase
    {
    public:
      IUnitTestNode();
      virtual std::string getPackage() = 0;
      virtual std::shared_ptr<IMapNode> getData() = 0;
      virtual std::shared_ptr<IArrayNode> getLogs() = 0;
      virtual std::shared_ptr<IUnitTestResultsNode> getResults() = 0;
      virtual ~IUnitTestNode();

      virtual std::string getDisplayName() override
      {
        return getPackage() + ":" + getName();
      }

      virtual std::string icon() override { return "play"; }

      virtual json getDataChildren_(int fileId, int level) override
      {
        json j = DataBase::getDataChildren_(fileId, level);
        if (getResults()->fetchkeys().size() > 0)
        {
          j.push_back(getResults()->getAsDataChild(fileId, level - 1));
        }
        if (getLogs()->size() > 0)
        {
          j.push_back(getLogs()->getAsDataChild(fileId, level - 1));
        }
        if (getData()->size() > 0)
        {
          j.push_back(getData()->getAsDataChild(fileId, level - 1));
        }
        return j;
      }

      void open(bool value) override
      {
        DataBase::open(value);
        getData()->open(value);
        getLogs()->open(value);
        getResults()->open(value);
      }
    };

    class VnVSpec
    {
      nlohmann::json spec;

      std::string getter(std::string r, std::string key) const
      {
        try
        {
          return spec[r][key]["docs"]["template"].get<std::string>();
        }
        catch (std::exception &e)
        {
          throw INJECTION_EXCEPTION("Template Specification Error: %s:%s/docs does not exist or is not a string ",
                                    r.c_str(), key.c_str());
        }
      }

    public:
      VnVSpec(const nlohmann::json &j) : spec(j) {}

      template <typename T>
      VnVSpec(const T &j) : spec(nlohmann::json::parse(j.dump())){};

      VnVSpec() {}
      void set(const nlohmann::json &s) { spec = s; }

      std::string get() { return spec.dump(); }

      std::string intro()
      {
        try
        {
          return spec["Introduction"]["docs"]["template"].get<std::string>();
        }
        catch (std::exception &e)
        {
          throw INJECTION_EXCEPTION_("No introduction available");
        }
      }

      std::string conclusion()
      {
        try
        {
          return spec["Conclusion"]["docs"]["template"].get<std::string>();
        }
        catch (std::exception &e)
        {
          throw INJECTION_EXCEPTION_("No conclusion available");
        }
      }

      std::string injectionPoint(std::string package, std::string name) const
      {
        return getter("InjectionPoints", package + ":" + name);
      }

      std::string dataType(std::string key) const { return getter("DataTypes", key); }
      std::string test(std::string package, std::string name) const { return getter("Tests", package + ":" + name); }

      std::string file(std::string package, std::string name) const { return getter("Files", package + ":" + name); }

      std::string action(std::string package, std::string name) const { return getter("Actions", package + ":" + name); }

      std::string package(std::string package) const { return getter("Options", package); }

      nlohmann::json unitTest(std::string package, std::string name) const
      {
        return spec["UnitTests"][package + ":" + name];
      }

      std::string code(std::string package, std::string name) const { return getter("CodeBlocks", package + ":" + name); }
    };

    class IRootNode : public DataBase
    {
      std::weak_ptr<IRootNode> rootNode_;
      long idCounter = 0;

    protected:
      virtual void registerNodeInternal(std::shared_ptr<DataBase> ptr) = 0;
      virtual std::shared_ptr<DataBase> findById_Internal(long id) = 0;

    public:
      IRootNode();

      virtual std::shared_ptr<DataBase> findById(long id, bool throwOnNull = true)
      {
        try
        {
          if (id == rootNode()->getId())
          {
            return rootNode_.lock();
          }

          auto a = findById_Internal(id);
          if (a == nullptr && throwOnNull)
          {
            throw INJECTION_EXCEPTION_("Could not find element with that id");
          }
          return a;
        }
        catch (...)
        {
          return nullptr;
        }
      }

      WalkerWrapper getWalker(std::string config);

      void registerNode(std::shared_ptr<DataBase> ptr)
      {
        if (ptr->getType() == DataBase::DataType::Root)
        {
          rootNode_ = ptr->getAsRootNode(ptr);
          ptr->setRootNode(idCounter++, ptr->getAsRootNode(ptr).get());
        }
        else
        {
          ptr->setRootNode(idCounter++, rootNode());
        }
        registerNodeInternal(ptr);
      }

      virtual void addIDN(long id, long streamId, node_type type, long index, std::string stage) = 0;
      void join()
      {
        auto a = getThread();
        if (a != nullptr)
        {
          a->join();
        }
      }
      virtual std::thread *getThread() { return NULL; };

      virtual std::map<long, std::list<IDN>> &getNodes() = 0;
      virtual std::shared_ptr<IArrayNode> getChildren() = 0;
      virtual std::shared_ptr<IArrayNode> getUnitTests() = 0;
      virtual std::shared_ptr<IInfoNode> getInfoNode() = 0;
      virtual std::shared_ptr<ICommInfoNode> getCommInfoNode() = 0;
      virtual std::shared_ptr<IMapNode> getPackages() = 0;
      virtual std::shared_ptr<IWorkflowNode> getWorkflowNode() = 0;
      virtual std::shared_ptr<IArrayNode> getLogs() = 0;
      virtual std::shared_ptr<ITestNode> getInitialization() = 0;
      virtual std::string getReportDirectory() = 0;

      virtual long getEndTime()
      {
        auto a = getInfoNode();
        if (a != nullptr)
        {
          auto end = a->getEndTime();
          if (end <= 0)
          {
            return std::chrono::duration_cast<std::chrono::milliseconds>(
                       std::chrono::system_clock::now().time_since_epoch())
                .count();
          }
          return end;
        }
        return 0;
      }
      virtual std::string icon() { return "home"; }

      virtual json getDataChildren_(int fileId, int level) override
      {
        json j = DataBase::getDataChildren_(fileId, level);

        j.push_back(getInfoNode()->getAsDataChild(fileId, level - 1));

        j.push_back(getCommInfoNode()->getAsDataChild(fileId, level-1));

        if (getPackages()->size() > 0)
        {
          j.push_back(getPackages()->getAsDataChild(fileId, level - 1));
        }

        if (getActions()->size() > 0)
        {
          j.push_back(getActions()->getAsDataChild(fileId, level - 1));
        }

        if (getUnitTests()->size() > 0)
        {
          j.push_back(getUnitTests()->getAsDataChild(fileId, level - 1));
        }

        if (getChildren()->size() > 0)
        {
          j.push_back(getChildren()->getAsDataChild(fileId, level - 1));
        }

        if (getLogs()->size() > 0)
        {
          j.push_back(getLogs()->getAsDataChild(fileId, level - 1));
        }

        j.push_back(getWorkflowNode()->getAsDataChild(fileId, level - 1));

        json jj = json::object();
        jj["text"] = "Injection Points";
        jj["icon"] = "feather icon-folder";
        json ch = json::array();
        for (auto it : getNodes())
        {
          for (auto itt : it.second)
          {
            if (itt.type == node_type::START || itt.type == node_type::POINT || itt.type == node_type::LOG)
            {
              ch.push_back(findById(itt.id)->getAsDataChild(fileId, 0));
            }
          }
        }
        jj["children"] = ch;
        j.push_back(jj);

        return j;
      }

      virtual std::shared_ptr<ITestNode> getPackage(std::string package)
      {
        auto a = getPackages()->get(package);
        return a->getAsTestNode(a);
      }

      virtual std::shared_ptr<ITestNode> getAction(std::string package)
      {
        auto a = getActions()->get(package);
        return a->getAsTestNode(a);
      }

      virtual void lock() = 0;

      virtual std::shared_ptr<IMapNode> getActions() = 0;

      virtual void release() = 0;

      virtual bool hasId(long id) { return findById(id) != NULL; }

      virtual const VnVSpec &getVnVSpec() = 0;

      virtual bool processing() const = 0;

      virtual void respond(long id, long jid, const std::string &response) = 0;

      virtual void persist() {};

      virtual void kill() {};

      
    std::string getTree(long processor) {
      
      auto nodes = getNodes();
      auto commMap = getCommInfoNode()->getCommMap();
      
      json root = json::object();
      root["id"] = -1;
      root["children"] = json::array();
      
      auto ptr = "/children"_json_ptr;
      
      for (auto &ind : nodes) {
        auto index = ind.first; 
        for (auto &idn : ind.second) {
            if (commMap->commContainsProcessor(idn.streamId, processor)) {
               
               if (it.type == node_type::END) {
                  ptr.pop_back(); // pop the children element
                  ptr.pop_back(); // pop the list element
               } else if (it.type == node_type::START) {
                  
                  //Add the element
                  json newpoint = json::object();
                  newpoint["id"] = it.id;
                  newpoint["children"] = json::array();
                  root.at(ptr).push_back(newpoint);
                  
                  //Append to the stack
                  ptr.push_back(std::to_string(root.at(ptr).size()));
                  ptr.push_back("children");                  
               } else {
                throw "Unsupported node type in IDN list";
               }
          }
        }
      }
      return root.dump();

    }



      virtual ~IRootNode();
    };

    std::shared_ptr<Nodes::IRootNode> getEngineReader(std::string filename, bool async, bool lock);

  } // namespace Nodes

} // namespace VnV
#endif // NODES_H
