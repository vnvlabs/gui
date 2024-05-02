#include <queue>
#include <mutex>
#include <atomic>
#include <fstream>
#include <stack>
#include <unistd.h>
#include <chrono>
#include <functional>
#include <list>
#include <string>
#include <thread>

#include "IReader.h"
#include "INodes.h"
#include "shared/DistUtils.h"

using namespace VnV::Nodes;

#define STREAM_READER_NO_MORE_VALUES -19999

#define INITMEMBER(name, Type)      \
  if (name == nullptr) {            \
    name.reset(new Type());         \
    rootNode()->registerNode(name); \
    name->setname(#name);           \
  }


namespace {
  
    constexpr const char* extension = ".fs";

    template <typename T> class Optional {
      std::unique_ptr<T> v = nullptr;
      Optional(const T& val) { v = std::make_unique<T>(val); }
    };

    template <typename T> class ThreadsafeQueue {
      std::queue<T> queue_;
      mutable std::mutex mutex_;

      // Moved out of public interface to prevent races between this
      // and pop().
      bool empty() const { return queue_.empty(); }

    public:
      ThreadsafeQueue() = default;
      ThreadsafeQueue(const ThreadsafeQueue<T>&) = delete;
      ThreadsafeQueue& operator=(const ThreadsafeQueue<T>&) = delete;

      ThreadsafeQueue(ThreadsafeQueue<T>&& other) {
        std::lock_guard<std::mutex> lock(mutex_);
        queue_ = std::move(other.queue_);
      }

      virtual ~ThreadsafeQueue() {}

      unsigned long size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.size();
      }

      T pop() {
        std::lock_guard<std::mutex> lock(mutex_);
        T tmp = queue_.front();
        queue_.pop();
        return tmp;
      }

      void push(const T& item) {
        std::lock_guard<std::mutex> lock(mutex_);
        queue_.push(item);
      }
    };

    class InMemory {
    public:
      template <typename T> class DataBaseImpl : public T {
      private:
        MetaDataWrapper metadata;
        bool open_;
        long streamId;
        std::string name;

      public:
        DataBaseImpl() : T() {}

        GETTERSETTER(streamId, long);
        GETTERSETTER(name, std::string);
        GETTERSETTER(metadata, MetaDataWrapper);

        virtual const MetaDataWrapper& getMetaData() override { return metadata; };
        virtual std::string getNameInternal() override { return name; }
        virtual bool getopen() override { return open_; };
        virtual void setopen(bool value) override { open_ = value; }
        virtual long getStreamId() override { return streamId; }
      };


      class CommMap : public ICommMap {
        
        class Comm;
        typedef std::shared_ptr<Comm> Comm_ptr;

        class Comm {
          void getAllChildren(std::set<long>& data, std::map<long, Comm_ptr>& result) {
            for (auto& it : children) {
              if (data.find(it.first) == data.end()) {
                it.second->getAllChildren(data, result);
                data.insert(it.first);
                result.erase(it.first);
              }
            }
          }

        public:
          long id;
          std::set<long> procs;
          std::map<long, Comm_ptr> children;
          std::map<long, Comm_ptr> parents;

          Comm(std::set<long> procs_, long id_) : procs(procs_), id(id_) {}

          bool isRoot() { return parents.size() == 0; }

          std::map<long, Comm_ptr>& getChildren() { return children; }

          void getAllChildren(std::map<long, Comm_ptr>& data) {
            for (auto& it : children) {
              if (data.find(it.first) == data.end()) {
                it.second->getAllChildren(data);
                data.insert(it);
              }
            }
          }

          void getDirectChildren(bool strip, std::map<long, Comm_ptr>& data) {
            if (!strip) {
              getAllChildren(data);
            } else {
              // A direct child is any child that is not also a child of one of  my
              // children.
              std::set<long> grandChildren;
              for (auto& it : children) {
                // If we havnt found this as a grand child already
                if (grandChildren.find(it.first) == grandChildren.end()) {
                  // add it to my list of all direct children.
                  data.insert(it);
                  // Now add all its children -- it will be removed if found as a
                  // grand child.
                  it.second->getAllChildren(grandChildren, data);
                }
              }
            }
          }

          std::map<long, Comm_ptr>& getParents() { return parents; }

          void getAllParents(std::map<long, Comm_ptr>& data) {
            for (auto& it : parents) {
              if (data.find(it.first) == data.end()) {
                data.insert(it);
                it.second->getAllParents(data);
              }
            }
          }

          std::map<long, Comm_ptr> commChain() {
            std::map<long, Comm_ptr> m;
            getAllParents(m);
            getAllChildren(m);
            return m;
          }

          nlohmann::json getParentChain() {
            nlohmann::json j = nlohmann::json::array();
            std::map<long, Comm_ptr> m;
            getAllParents(m);
            for (auto it : m) {
              j.push_back(it.first);
            }
            return j;
          }

          bool is_parent(long id) {
            std::map<long, Comm_ptr> m;
            getAllParents(m);
            return m.find(id) != m.end();
          }

          bool is_child(long id) {
            for (auto& it : children) {
              if (id == it.first) {
                return true;
              }
            }
            return false;
          }

          nlohmann::json getChildChain() {
            nlohmann::json j = nlohmann::json::array();
            std::map<long, Comm_ptr> m;
            getAllChildren(m);
            for (auto it : m) {
              j.push_back(it.first);
            }
            return j;
        }

          void toJson(bool strip, nlohmann::json& j, std::set<long>& done) {
            if (done.find(id) == done.end()) {
              done.insert(id);
              nlohmann::json node = nlohmann::json::object();
              node["id"] = id;
              node["group"] = procs.size();
              node["parents"] = getParentChain();
              node["children"] = getChildChain();
              j["nodes"].push_back(node);

              std::map<long, Comm_ptr> ch;
              getDirectChildren(strip, ch);

              for (auto& it : ch) {
                nlohmann::json link = nlohmann::json::object();
                link["target"] = it.first;
                link["source"] = id;
                link["value"] = it.second->procs.size();
                j["links"].push_back(link);

                it.second->toJson(strip, j, done);
              }
            }
          }
        };

        std::map<long, Comm_ptr> nodes;

        void addChild(Comm_ptr ptr1, Comm_ptr ptr2) {
          // A Comm is my child if I contain all of its processors.
          // That can only be true if it is smaller than me.
          int sizeDiff = ptr1->procs.size() - ptr2->procs.size();

          Comm_ptr parent, child;

          if (sizeDiff == 0) {
            return;  // Cant be child if same size. (assume unique)
          } else if (sizeDiff < 0) {
            parent = ptr2;
            child = ptr1;
          } else {
            child = ptr2;
            parent = ptr1;
          }

          auto child_it = child->procs.begin();
          auto parent_it = parent->procs.begin();

          while (child_it != child->procs.end() && parent_it != parent->procs.end()) {
            if (*parent_it == *child_it) {
              ++parent_it;
              ++child_it;  // Found this one. so move on to next for both.
            } else if (*parent_it < *child_it) {
              ++parent_it;  // parent is less -- this is ok, parent can have elements
                            // not in child.
            } else {
              return;  // parent is greater -- Not ok, this means child_it is not in
                      // parent --> not child.
            }
          }

          if (child_it == child->procs.end()) {
            child->parents.insert(std::make_pair(parent->id, parent));

            parent->children.insert(std::make_pair(child->id, child));

          } else {
            return;  // We ran out of parent elements to check so it wqasnt there.
          }
        }

      public:
        CommMap() : ICommMap() {}

        void add(long id, const std::set<long>& comms) {
          Comm_ptr p = std::make_shared<Comm>(comms, id);
          for (auto& it : nodes) {
            addChild(p, it.second);
          }
          nodes.insert(std::make_pair(p->id, p));
        }

        std::set<long> commChain(long comm) const override {
          std::set<long> r;
          auto n = nodes.find(comm);
          if (n != nodes.end()) {
            for (auto it : n->second->commChain()) {
              r.insert(it.first);
            }
          }
          return r;
        }

        bool commContainsProcessor(long commId, long proc) const override {
          auto n = nodes.find(commId);
          if (n != nodes.end()) {            
            return n->second->procs.find(proc) != n->second->procs.end();
          }
          return false;
        }

        bool commIsSelf(long commId, long proc) const {
          auto n = nodes.find(commId);
          if (n != nodes.end()) {
            return (n->second->procs.size() == 1 && *n->second->procs.begin() == proc);
          }
          return false;
        }

        bool commsIntersect(long streamId, long comm) const {
          auto child = nodes.find(streamId);
          auto parent = nodes.find(comm);
          if (child == nodes.end() && parent != nodes.end()) {
            auto child_it = child->second->procs.begin();
            auto parent_it = parent->second->procs.begin();

            while (child_it != child->second->procs.end() && parent_it != parent->second->procs.end()) {
              if (*parent_it < *child_it) {
                ++parent_it;
              } else if (*child_it < *parent_it) {
                ++child_it;
              } else {
                return true;
              }
            }
          }
          return false;
        }

        bool commContainsComm(long commId, long childId) const override {
          if (commId == childId) return true;

          auto n = nodes.find(commId);
          auto c = nodes.find(childId);

          // parent is smaller than child.
          if (n->second->procs.size() < c->second->procs.size()) {
            return false;
          }
          return c->second->is_parent(commId);
        }

        bool commIsChild(long parentId, long childId) const { return nodes.find(parentId)->second->is_child(childId); }

        nlohmann::json listComms() const override {
          json j = json::object();
          for (auto& it : nodes) {
            j[std::to_string(it.first)] = it.second->procs;
          }
          return j;
        }

        nlohmann::json toJson(bool strip) const {
          nlohmann::json j = R"({"nodes":[],"links":[]})"_json;
          std::set<long> done;
          for (auto& it : nodes) {
            it.second->toJson(strip, j, done);
          }
          return j;
        }

        std::string toJsonStr(bool strip) const override { return toJson(strip).dump(); }

        ~CommMap() {}
    };


      class ArrayNode : public DataBaseImpl<IArrayNode> {
        std::vector<std::shared_ptr<DataBase>> vec;

      public:
        ArrayNode() : DataBaseImpl<IArrayNode>() {}

        virtual std::shared_ptr<DataBase> get(std::size_t idx) override {
          return (idx < vec.size()) ? (vec[idx]) : nullptr;
        }

        virtual std::size_t size() override { return vec.size(); };

        virtual void add(std::shared_ptr<DataBase> data) override { vec.push_back(data); }
      };

      class MapNode : public DataBaseImpl<IMapNode> {
        std::map<std::string, std::shared_ptr<DataBase>> map;

      public:
        MapNode() : DataBaseImpl<IMapNode>() {}

        virtual void insert(std::string key, std::shared_ptr<DataBase> val) {
          auto parent = map.find(key);
          if (parent == map.end()) {
            map[key] = val;
          } else {
            auto metadata = val->getMetaData();
            std::string collate = metadata.has("collate") ? metadata.get("collate") : "shape";

            // If replace then we just override it.
            if (collate.compare("replace") == 0) {
              map[key] = val;
            } else {
              auto exist = parent->second;
              if (exist->getType() != DataType::Array) {
                // Not an array -- so convert it (we collate ids of same type.)
                auto a = std::make_shared<ArrayNode>();
                rootNode()->registerNode(a);

                a->setname(key);
                std::cout << a->toJson().dump() << std::endl;

                a->add(exist);
                std::cout << a->toJson().dump() << std::endl;

                a->add(val);
                std::cout << a->toJson().dump() << std::endl;

                map[key] = a;
              } else {
                std::cout << exist->getAsArrayNode(exist)->toJson().dump() << std::endl;

                exist->getAsArrayNode(exist)->add(val);
              }
            }
          }
        }

        virtual std::shared_ptr<DataBase> get(std::string key) override {
          auto it = map.find(key);
          return (it == map.end()) ? nullptr : (it->second);
        }

        virtual bool contains(std::string key) override { return map.find(key) != map.end(); }

        virtual std::vector<std::string> fetchkeys() override {
          std::vector<std::string> v;
          for (auto it = map.begin(); it != map.end(); ++it) {
            v.push_back(it->first);
          }
          return v;
        }

        virtual std::size_t size() override { return map.size(); };

        virtual ~MapNode(){};
      };

      #define X(x, y)                                                                                                 \
        class x##Node : public DataBaseImpl<I##x##Node> {                                                             \
          std::vector<std::size_t> shape;                                                                             \
          std::vector<y> value;                                                                                       \
                                                                                                                      \
        public:                                                                                                      \
          x##Node() : DataBaseImpl<I##x##Node>() {}                                                                   \
                                                                                                                      \
          const std::vector<std::size_t>& getShape() override { return shape; }                                       \
                                                                                                                      \
          y getValueByShape(const std::vector<std::size_t>& rshape) override {                                        \
            if (shape.size() == 0) {                                                                                  \
              return value[0];                                                                                        \
            }                                                                                                         \
            if (rshape.size() != shape.size())                                                                        \
              throw INJECTION_EXCEPTION("%s: Invalid Shape Size %d (should be %d)", #x, rshape.size(), shape.size()); \
                                                                                                                      \
            std::size_t mult = 1;                                                                                     \
            int index = 0;                                                                                            \
            for (int i = shape.size() - 1; i >= 0; i--) {                                                             \
              index += rshape[i] * mult;                                                                              \
              mult *= shape[i];                                                                                       \
            }                                                                                                         \
            return getValueByIndex(index);                                                                            \
          }                                                                                                           \
          void add(const y& v) { value.push_back(v); }                                                                \
          y getValueByIndex(const size_t ind) override { return value[ind]; }                                         \
                                                                                                                      \
          y getScalarValue() override {                                                                               \
            if (shape.size() == 0)                                                                                    \
              return value[0];                                                                                        \
            else                                                                                                      \
              throw INJECTION_EXCEPTION("%s: No shape provided to non scalar shape tensor object", #x);               \
          }                                                                                                           \
                                                                                                                      \
          int getNumElements() override { return value.size(); }                                                      \
          virtual ~x##Node() {}                                                                                       \
          virtual void setShape(const std::vector<std::size_t>& s) { shape = s; }                                     \
          virtual void setValue(const std::vector<y>& s) { value = s; }                                               \
        };
        DTYPES
      #undef X

      class InfoNode : public DataBaseImpl<IInfoNode> {
        long start = 0;
        long end = 0;
        std::string title;
        std::string workflow;
        std::string jobName;
        std::string fileStub;
        std::shared_ptr<VnV::VnVProv> prov = nullptr;

        virtual std::shared_ptr<VnV::VnVProv> getProvInternal() { return prov; };

      public:
        InfoNode() : DataBaseImpl<IInfoNode>() {}
        virtual std::string getTitle() override { return title; }
        virtual long getStartTime() override { return start; }
        virtual long getEndTime() override { return end; }
        virtual std::string getWorkflow() override { return workflow; }
        virtual std::string getJobName() override { return jobName; }
        virtual std::string getFileStub() override { return fileStub; }
        

        GETTERSETTER(workflow, std::string)
        GETTERSETTER(jobName, std::string)
        GETTERSETTER(fileStub, std::string)
        GETTERSETTER(start, long)
        GETTERSETTER(end, long)
        GETTERSETTER(title, std::string)
        GETTERSETTER(prov, std::shared_ptr<VnV::VnVProv>)

        virtual ~InfoNode() {}
      };

      class CommInfoNode : public DataBaseImpl<ICommInfoNode> {
        std::shared_ptr<CommMap> commMap;
        int worldSize;
        json nodeMap;
        std::string version;

      protected:
        virtual std::shared_ptr<ICommMap> getCommMapInternal() override { return commMap; }

      public:
        CommInfoNode() : DataBaseImpl<ICommInfoNode>(), commMap(new CommMap()) {}

        virtual int getWorldSize() override { return worldSize; }
        virtual std::string getNodeMap() override { return nodeMap.dump(); }
        virtual std::string getVersion() override { return version; }

        GETTERSETTER(worldSize, int);
        GETTERSETTER(nodeMap, json);
        GETTERSETTER(version, std::string);

        virtual ~CommInfoNode(){};
      };

      class WorkflowNode : public DataBaseImpl<IWorkflowNode> {
        std::string package = "";
        std::string state = "";
        json info;
        std::map<std::string, std::shared_ptr<IRootNode>> rootNodes;
        std::map<std::string, int> fileIds;

      public:
        WorkflowNode() : DataBaseImpl<IWorkflowNode>() {}
        virtual std::string getPackage() override { return package; }
        virtual std::string getState() override { return state; }
        virtual json getInfo() override { return info; }

        GETTERSETTER(package, std::string);
        GETTERSETTER(state, std::string);
        GETTERSETTER(info, json);

        virtual std::shared_ptr<IRootNode> getReport(std::string reportName) override {
          auto it = rootNodes.find(reportName);
          if (it != rootNodes.end()) {
            return it->second;
          }
          return nullptr;
        }

        virtual bool hasReport(std::string reportName) override { return rootNodes.find(reportName) != rootNodes.end(); }

        virtual void setReport(std::string reportName, int fileId, std::shared_ptr<IRootNode> rootNode) override {
          fileIds[reportName] = fileId;
          rootNodes[reportName] = rootNode;
        }

        virtual std::vector<std::string> listReports() override {
          std::vector<std::string> ret;
          for (auto& it : rootNodes) {
            ret.push_back(it.first);
          }
          return ret;
        }

        virtual int getReportFileId(std::string reportName) {
          auto it = fileIds.find(reportName);
          if (it != fileIds.end()) {
            return it->second;
          }
          return -100;
        }
      };

      class TestNode : public DataBaseImpl<ITestNode> {
        long uid;
        ITestNode::TestNodeUsage usage;
        std::string package;
        std::shared_ptr<MapNode> data = nullptr;
        std::shared_ptr<ArrayNode> logs = nullptr;
        bool result;
        bool internal;

      public:
        TestNode() : DataBaseImpl<ITestNode>() {}
        virtual std::string getPackage() override { return package; }
        virtual std::shared_ptr<IMapNode> getData() override {
          INITMEMBER(data, MapNode)
          return data;
        }
        virtual std::shared_ptr<IArrayNode> getLogs() override {
          INITMEMBER(logs, ArrayNode)
          return logs;
        }

        virtual ITestNode::TestNodeUsage getUsage() override { return usage; }
        virtual bool isInternal() override { return internal; }

        GETTERSETTER(uid, long);
        GETTERSETTER(result, bool);
        GETTERSETTER(internal, bool);
        GETTERSETTER(usage, ITestNode::TestNodeUsage);
        GETTERSETTER(package, std::string);
        GETTERSETTER(data, std::shared_ptr<MapNode>)
        GETTERSETTER(logs, std::shared_ptr<ArrayNode>)
      };

      class InjectionPointNode : public DataBaseImpl<IInjectionPointNode> {
        std::shared_ptr<ArrayNode> logs;
        std::shared_ptr<ArrayNode> tests;
        std::shared_ptr<TestNode> internal;
        std::string package;

        long startIndex = -1;
        long endIndex = -1;
        long long commId;

        bool isIter = false;  // internal property to help with parsing.
        bool isOpen = false;  // internal property to help with paresing

      public:
        GETTERSETTER(package, std::string)
        GETTERSETTER(commId, long long)
        GETTERSETTER(internal, std::shared_ptr<TestNode>)
        GETTERSETTER(startIndex, long)
        GETTERSETTER(endIndex, long)
        GETTERSETTER(isIter, bool)
        GETTERSETTER(isOpen, bool)

        InjectionPointNode() : DataBaseImpl<IInjectionPointNode>() {}

        virtual std::string getPackage() override { return package; }

        virtual std::shared_ptr<IArrayNode> getTests() override {
          INITMEMBER(tests, ArrayNode)
          return tests;
        }

        virtual std::shared_ptr<ITestNode> getData() override {
          INITMEMBER(internal, TestNode)
          return internal;
        }

        virtual std::shared_ptr<IArrayNode> getLogs() override {
          INITMEMBER(logs, ArrayNode);
          return logs;
        }

        virtual std::string getComm() override { return std::to_string(commId); }

        virtual long getStartIndex() override { return startIndex; }
        virtual long getEndIndex() override { return endIndex; }
        
        std::shared_ptr<TestNode> getTestByUID(long uid) {
          for (int i = 0; i < getTests()->size(); i++) {
            auto t = std::dynamic_pointer_cast<TestNode>(getTests()->get(i));
            if (t->getuid() == uid) {
              return t;
            }
          }
          return nullptr;
        }

        virtual ~InjectionPointNode() {}
      };

      class LogNode : public DataBaseImpl<ILogNode> {
        std::string package, level, stage, message, comm;
        int identity;

      public:
        GETTERSETTER(package, std::string)
        GETTERSETTER(level, std::string)
        GETTERSETTER(stage, std::string)
        GETTERSETTER(message, std::string)
        GETTERSETTER(comm, std::string)
        GETTERSETTER(identity, int)

        LogNode() : DataBaseImpl<ILogNode>() {}
        virtual std::string getPackage() override { return package; }
        virtual std::string getLevel() override { return level; }
        virtual std::string getMessage() override { return message; }
        virtual std::string getComm() override { return comm; }
        virtual std::string getStage() override { return stage; }
        virtual ~LogNode() {}
      };

      class DataNode : public DataBaseImpl<IDataNode> {
        bool local;
        long long key;
        std::shared_ptr<ArrayNode> logs;
        std::string package;
        std::shared_ptr<MapNode> children;

      public:
        GETTERSETTER(local, bool)
        GETTERSETTER(key, long long)
        GETTERSETTER(package, std::string)

        DataNode() : DataBaseImpl<IDataNode>() {}

        virtual bool getLocal() override { return local; }
        virtual long long getDataTypeKey() override { return key; }

        virtual std::shared_ptr<IMapNode> getData() override {
          INITMEMBER(children, MapNode)
          return children;
        }

        virtual std::shared_ptr<IArrayNode> getLogs() override {
          INITMEMBER(logs, ArrayNode);
          return logs;
        };

        virtual ~DataNode() {}
      };

      class UnitTestResultNode : public DataBaseImpl<IUnitTestResultNode> {
        std::string desc;
        bool result;

      public:
        GETTERSETTER(desc, std::string)
        GETTERSETTER(result, bool)

        UnitTestResultNode() : DataBaseImpl<IUnitTestResultNode>() {}
        virtual std::string getDescription() override { return desc; }
        virtual bool getResult() override { return result; }
        virtual ~UnitTestResultNode() {}
      };

      class UnitTestResultsNode : public DataBaseImpl<IUnitTestResultsNode> {
        std::shared_ptr<MapNode> m;

        auto getM() {
          INITMEMBER(m, MapNode)
          return m;
        }

      public:
        UnitTestResultsNode() : DataBaseImpl<IUnitTestResultsNode>() {}

        virtual std::shared_ptr<IUnitTestResultNode> get(std::string key) {
          if (m->contains(key)) {
            auto a = getM()->get(key);
            if (a->getType() == DataType::Array) {
                auto b = a->getAsArrayNode(a)->get(0);
                return b->getAsUnitTestResultNode(b);
            } else if (a->getType() == DataType::UnitTestResult) {
                return a->getAsUnitTestResultNode(a);
            } else {
                
            }
          }
          throw INJECTION_EXCEPTION("Unit Test Results Node: Key %s does not exist", key.c_str());
        };

        void insert(std::string name, std::shared_ptr<IUnitTestResultNode> value) { getM()->insert(name, value); }

        virtual bool contains(std::string key) { return getM()->contains(key); }

        virtual std::vector<std::string> fetchkeys() { return getM()->fetchkeys(); };

        virtual ~UnitTestResultsNode(){};
      };

      class UnitTestNode : public DataBaseImpl<IUnitTestNode> {
        std::string package;
        std::shared_ptr<ArrayNode> logs;
        std::shared_ptr<MapNode> children;
        std::shared_ptr<UnitTestResultsNode> resultsMap;
        std::map<std::string, std::string> testTemplate;

      public:
        GETTERSETTER(package, std::string)

        UnitTestNode() : DataBaseImpl<IUnitTestNode>() {}

        virtual std::string getPackage() override { return package; }

        virtual std::shared_ptr<IMapNode> getData() override {
          INITMEMBER(children, MapNode);
          return children;
        }

        virtual std::shared_ptr<IArrayNode> getLogs() override {
          INITMEMBER(logs, ArrayNode)
          return logs;
        };

        virtual std::shared_ptr<IUnitTestResultsNode> getResults() override {
          INITMEMBER(resultsMap, UnitTestResultsNode)
          return resultsMap;
        }
      };

     class RootNode : public DataBaseImpl<IRootNode> {
        long lowerId, upperId;
        std::atomic<bool> _processing = ATOMIC_VAR_INIT(true);
        std::string reportDirectory;

        std::shared_ptr<VnVSpec> spec;
        std::shared_ptr<ArrayNode> children;
        std::shared_ptr<ArrayNode> unitTests;
        std::shared_ptr<MapNode> actions;
        std::shared_ptr<MapNode> packages;
        std::shared_ptr<InfoNode> infoNode;
        std::shared_ptr<CommInfoNode> commInfo;
        std::shared_ptr<WorkflowNode> workflowNode;
        std::shared_ptr<ArrayNode> logs;

        std::shared_ptr<TestNode> initialization;

        std::map<long, std::list<IDN>> nodes;
        std::map<long, std::shared_ptr<DataBase>> idMap;

      public:
        GETTERSETTER(lowerId, long);
        GETTERSETTER(upperId, long);
        GETTERSETTER(infoNode, std::shared_ptr<InfoNode>)
        GETTERSETTER(workflowNode, std::shared_ptr<WorkflowNode>)
        GETTERSETTER(initialization, std::shared_ptr<TestNode>)
        GETTERSETTER(reportDirectory,std::string)

        RootNode() : DataBaseImpl<IRootNode>(), spec(new VnVSpec()) {}

        void setspec(const json& s) { spec->set(s); }

        void setProcessing(bool value) { _processing.store(value, std::memory_order_relaxed); }

        virtual std::shared_ptr<IMapNode> getPackages() override { INITMEMBER(packages, MapNode) return packages; }
        virtual std::shared_ptr<IMapNode> getActions() override { INITMEMBER(actions, MapNode) return actions; }
        virtual std::shared_ptr<IArrayNode> getChildren() override { INITMEMBER(children, ArrayNode) return children; }
        virtual std::shared_ptr<ITestNode> getInitialization() override {
          INITMEMBER(initialization, TestNode) return initialization;
        }
        virtual std::shared_ptr<IArrayNode> getUnitTests() override { INITMEMBER(unitTests, ArrayNode) return unitTests; }
        virtual std::shared_ptr<IArrayNode> getLogs() override { INITMEMBER(logs, ArrayNode) return logs; }
        virtual std::shared_ptr<IInfoNode> getInfoNode() override { INITMEMBER(infoNode, InfoNode) return infoNode; }
        virtual std::shared_ptr<IWorkflowNode> getWorkflowNode() override {
          INITMEMBER(workflowNode, WorkflowNode) return workflowNode;
        }
        virtual std::shared_ptr<ICommInfoNode> getCommInfoNode() override {
          INITMEMBER(commInfo, CommInfoNode) return commInfo;
        }

        virtual std::string getReportDirectory() override {
            return reportDirectory;
        }

        void cache_persist(bool clearCache) {}

        void markReaderThread() {}

        virtual bool processing() const override { return _processing.load(); }

        virtual std::shared_ptr<DataBase> findById_Internal(long id) override {
          auto it = idMap.find(id);
          if (it != idMap.end()) {
            return it->second;
          }
          throw INJECTION_EXCEPTION("Invalid Id %s", id);
        }

        virtual void registerNodeInternal(std::shared_ptr<DataBase> ptr) { idMap[ptr->getId()] = ptr; }

        virtual std::map<long, std::list<IDN>>& getNodes() override { return nodes; }


        virtual std::string getInjectionPointJson(){
            json j = json::object;
            j["type"] = "root";

            for (auto & ind : nodes) {
              long index = ind.first;
              for (auto & idn : index.second) {
                 
              }
            }
        }

        void addIDN(long id, long streamId, node_type type, long index, std::string stage) override {
          std::cout << "ADDING " << id << " with stream Id  " << streamId << std::endl;
          auto it = nodes.find(index);
          if (it == nodes.end()) {
            nodes[index] = std::list<IDN>();
            nodes[index].push_back(IDN(id, streamId, type, stage));
          } else {
            (it->second).push_back(IDN(id, streamId, type, stage));
          }
        }

        virtual const VnVSpec& getVnVSpec() { return *spec; }
      };
  };

    class JsonFileIterator : public Iterator<json> {
      long sId;
      std::ifstream ifs;
      std::streamoff p = 0;
      VnV::DistUtils::LockFile lockfile;

      json nextCurr;
      long nextValue = -1;

      std::string currJson;

    // What do we want to do--
    // We want to prefetch json.
    #define QUEUESIZE 100
      ThreadsafeQueue<json> jsonQueue;
      std::atomic<bool> _fetching = ATOMIC_VAR_INIT(true);

      std::thread fetcher;

      void fetchThread() {
        while (_fetching.load()) {
          ifs.seekg(p);
          std::string currline;
          lockfile.lock();

          while (std::getline(ifs, currline)) {
            while (jsonQueue.size() > QUEUESIZE) {
              std::this_thread::yield();  // System can go do something else if it wants.
            }

            jsonQueue.push(json::parse(currline));

            if (ifs.tellg() == -1) {
              p += currline.size();
            } else {
              p = ifs.tellg();
            }
          }
          ifs.clear();
        }
      }
      void launchThread() { fetcher = std::thread(&JsonFileIterator::fetchThread, this); }
      void killThread() {
        _fetching.store(false);
        if (fetcher.joinable()) {
          fetcher.join();
        }
      }

      void getLine_() {
        auto s = jsonQueue.size();

        // Attempt to catch race conditions

        if (s == 0) {
          nextValue = STREAM_READER_NO_MORE_VALUES;
          nextCurr = json::object();

        } else {
          try {
            auto j = jsonQueue.pop();
            nextCurr = j[1];
            nextValue = j[0].get<long>();

          } catch (std::exception& e) {
            nextValue = STREAM_READER_NO_MORE_VALUES;
            nextCurr = json::object();
          }
        }
      }

      void getLine(json& current, long& currentValue) override {
        current = nextCurr;
        currentValue = nextValue;
        getLine_();
        return;
      }

    public:
      JsonFileIterator(long streamId_, std::string filename_) : sId(streamId_), ifs(filename_), lockfile(filename_) {
        if (!ifs.good()) {
          throw INJECTION_EXCEPTION("Could not open file %s", filename_.c_str());
        }
        launchThread();
        getLine_();
      }

      bool hasNext() override {
        if (nextValue == STREAM_READER_NO_MORE_VALUES) {
          getLine_();
        }
        return nextValue != STREAM_READER_NO_MORE_VALUES;
      }

      long streamId() const override { return sId; }

      ~JsonFileIterator() {
        killThread();
        ifs.close();
        lockfile.close();
      }
    };

    class MultiFileStreamIterator : public MultiStreamIterator<JsonFileIterator, json> {
      std::set<std::string> loadedFiles;
      std::string filestub;
      std::string response_stub = "";

    public:
      MultiFileStreamIterator(std::string fstub) : MultiStreamIterator<JsonFileIterator, json>(), filestub(fstub) {}

      virtual void respond(long id, long jid, const json& response) override {
        
        // Respond to a file request in a format that will be understood by rhe Json Stream that is
        std::string s = VnV::DistUtils::join({filestub, "__response__", std::to_string(jid) + "_" + std::to_string(id)}, 0777, true, true);
        std::ofstream ofs(s + ".responding");
        ofs << response.dump();
        ofs.close();
        VnV::DistUtils::mv(s + ".responding", s + ".complete");
      
      }

      std::string getFileStub() { return filestub; }

      bool allstreamsread = false;
      void updateStreams() override {
        if (allstreamsread) return;

        try {
          std::vector<std::string> files = VnV::DistUtils::listFilesInDirectory(filestub);
          std::string ext = extension;
          for (auto& it : files) {
            if (loadedFiles.find(it) == loadedFiles.end()) {
              loadedFiles.insert(it);
              try {
                if (it.compare("__done__") == 0) {
                  allstreamsread = true;
                }
                if (it.compare(".") == 0 || it.compare("..") == 0 || it.size() <= ext.size()) {
                  continue;
                }
                if (it.substr(it.size() - ext.size()).compare(ext) != 0) {
                  continue;
                }
                std::cout << it << " is what i am reading" << std::endl;
                long id = std::atol(it.substr(0, it.size() - ext.size()).c_str());
                std::string fname = VnV::DistUtils::join({filestub, it}, 0777, false);
                std::cout << "EVEN CLOSE " << fname <<  std::endl;
                add(std::make_shared<JsonFileIterator>(id, fname));

              } catch (std::exception& e) {
              }
            }
          }
        } catch (std::exception& e) {
          throw INJECTION_EXCEPTION_("Not A Directory");
        }
      }
    };



    using InMemoryParser = VnV::Nodes::StreamParserTemplate<InMemory>;
    template <typename N> using InMemoryParserVisitor = InMemoryParser::ParserVisitor<N>;
    template <typename N> using NoLockInMemoryParserVisitor = InMemoryParser::NoLockParserVisitor<N>;
    template <typename T, typename V> using InMemoryRootNodeWithThread = InMemoryParser::RootNodeWithThread<T, V>;

}

  

std::shared_ptr<VnV::Nodes::IRootNode> VnV::Nodes::getEngineReader(std::string filename, bool async, bool lock) {
  auto stream = std::make_shared<MultiFileStreamIterator>(filename);
  auto pv = lock ? std::make_shared<InMemoryParserVisitor<json>>() : std::make_shared<NoLockInMemoryParserVisitor<json>>();
  return InMemoryRootNodeWithThread<MultiFileStreamIterator, json>::parse(async, stream, pv);
}


