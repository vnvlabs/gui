#ifndef READER_HEADER_ONE
#define READER_HEADER_ONE

#include "INodes.h"
#include "shared/constants.h"

using namespace VnV::Constants;

namespace VnV {
  namespace Nodes {
    

class JsonElement {
 public:
  long id;
  json data;
  JsonElement(long i, const json& d) : id(i), data(d) {}
};

template <typename V> class Iterator {
 private:
  std::pair<V, long> current;

  std::stack<std::shared_ptr<DataBase>> stack;
  bool peaked = false;
  bool donedone = false;

  virtual void getLine(V& currentJson, long& currentValue) = 0;

 public:
  Iterator(){};
  virtual long streamId() const = 0;
  virtual bool hasNext() = 0;

  virtual bool start_stream_reader() { return true; };
  virtual void stop_stream_reader(){};

  virtual bool isDone() { return donedone; };

  virtual std::pair<V, long> next() {
    pullLine(false);
    return current;
  }

  void pullLine(bool peek) {
    if (!peaked && hasNext()) {
      getLine(current.first, current.second);

      if (!current.first.contains(JSD::node)) {
        throw INJECTION_EXCEPTION("Stream sent info without node %s", current.first.dump().c_str());
      }
      if ((current.first)[JSD::node].template get<std::string>() == JSN::done) {
        donedone = true;
      }
    }
    peaked = peek;
  }

  virtual long peekId() {
    pullLine(true);
    return current.second;
  };

  virtual void respond(long id, long jid, const json& response) {
    throw INJECTION_EXCEPTION_("This reader does not implement the respond function.");
  }

  virtual ~Iterator(){};

  virtual void push(std::shared_ptr<DataBase> d) { stack.push(d); }
  virtual std::shared_ptr<DataBase> pop() {
    if (stack.size() > 0) {
      auto s = stack.top();
      stack.pop();
      return s;
    }
    return nullptr;
  }
  virtual std::shared_ptr<DataBase> top() {
    if (stack.size() > 0) {
      return stack.top();
    }
    return nullptr;
  }
};

template <typename T, typename V> class MultiStreamIterator : public Iterator<V> {
  std::list<std::shared_ptr<T>> instreams;
  typename std::list<std::shared_ptr<T>>::iterator min;

  virtual void getLine(V& current, long& cid) override {
    min = std::min_element(instreams.begin(), instreams.end(),
                           [](const std::shared_ptr<T>& x, const std::shared_ptr<T>& y) {
                             if (x->isDone() && y->isDone())
                               return (x->peekId() < y->peekId());
                             else if (x->isDone())
                               return false;
                             else if (y->isDone())
                               return true;

                             return (x->peekId() < y->peekId());
                           });

    auto p = (*min)->next();
    current = p.first;
    cid = p.second;
  }

 public:
  MultiStreamIterator() : Iterator<V>(){};

  std::list<std::shared_ptr<T>>& getInputStreams() { return instreams; }

  virtual void add(std::shared_ptr<T> iter) { instreams.push_back(iter); }

  virtual bool isDone() override{
    updateStreams();

    if (instreams.size() == 0) {
      return false;
    }

    for (auto it : instreams) {
      if (!it->isDone()) {
        return false;
      }
    }
    return true;
  }

  virtual bool hasNext() override {
    updateStreams();
    for (auto it : instreams) {
      if (it->hasNext()) {
        return true;
      }
    }
    return false;
  }

  virtual void updateStreams() {}

  virtual long streamId() const override { return (*min)->streamId(); }

  virtual long peekId() override {
    this->pullLine(true);
    return (*min)->peekId();
  }

  void push(std::shared_ptr<DataBase> d) override { (*min)->push(d); }

  std::shared_ptr<DataBase> pop() override { return (*min)->pop(); }

  std::shared_ptr<DataBase> top() override { return (*min)->top(); }
};

template <class DB> class StreamParserTemplate {
 public:
  template <class T> class ParserVisitor : public VisitorLock {
   public:
    std::shared_ptr<Iterator<T>> jstream;
    typename DB::RootNode* _rootInternal;

    typename DB::RootNode* rootInternal() { return _rootInternal; }

    virtual std::pair<long, std::set<long>> visitCommNode(const T& j) {
      std::pair<long, std::set<long>> res;

      for (auto it : j[JSD::commList].items()) {
        res.second.insert(it.value().template get<long>());
      }

      res.first = j[JSD::comm].template get<long>();

      return res;
    }

    template <typename A> std::shared_ptr<A> mks_str(std::string noName = "") {
      std::shared_ptr<A> base_ptr;
      base_ptr.reset(new A());
      rootInternal()->registerNode(base_ptr);
      base_ptr->setname(noName);
      std::cout << "SETTING STREAM ID " << jstream->streamId() << std::endl;
      base_ptr->setstreamId(jstream->streamId());
      return base_ptr;
    }

    template <typename A> std::shared_ptr<A> mks(const T& j) {
      auto a = mks_str<A>(j[JSD::name].template get<std::string>());
      if (j.contains(JSD::meta)) {
        MetaDataWrapper m;
        for (auto it : j[JSD::meta].items()) {
          m.add(it.key(), it.value().template get<std::string>());
        }
        a->setmetadata(m);
      }
      return a;
    }

    template <typename A, typename V> std::shared_ptr<A> visitShapeNode(const T& j) {
      std::shared_ptr<A> n = mks<A>(j);

      auto shapej = j.contains(JSD::shape) ? j[JSD::shape] : json::object();
      std::size_t shapeSize = shapej.size();

      std::vector<std::size_t> shape;
      std::vector<V> value;

      shape.reserve(shapeSize);
      for (auto it : shapej.items()) {
        shape.push_back(it.value().template get<std::size_t>());
      }

      // Set the scalar value.
      if (shapeSize == 0) {
        value.reserve(1);
        value.push_back(j[JSD::value].template get<V>());
      } else {
        value.reserve(shapeSize);
        for (auto it : j[JSD::value].items()) {
          value.push_back(it.value().template get<V>());
        }
      }

      n->setShape(std::move(shape));
      n->setValue(std::move(value));

      return n;
    }

    virtual std::shared_ptr<typename DB::StringNode> visitStringNode(const T& j) {
      return visitShapeNode<typename DB::StringNode, std::string>(j);
    }

    virtual std::shared_ptr<typename DB::DoubleNode> visitDoubleNode(const T& j) {
      return visitShapeNode<typename DB::DoubleNode, double>(j);
    }
    virtual std::shared_ptr<typename DB::BoolNode> visitBoolNode(const T& j) {
      return visitShapeNode<typename DB::BoolNode, bool>(j);
    };
    virtual std::shared_ptr<typename DB::LongNode> visitLongNode(const T& j) {
      return visitShapeNode<typename DB::LongNode, long>(j);
    }

    virtual std::shared_ptr<typename DB::JsonNode> visitJsonNode(const T& j) {
      auto n = mks<typename DB::JsonNode>(j);
      n->open(true);

      auto shapeJ = j.contains(JSD::shape) ? j[JSD::shape] : json::object();
      std::size_t shapeSize = shapeJ.size();

      std::vector<std::size_t> shape;
      std::vector<std::string> value;

      shape.reserve(shapeSize);

      for (auto it : shapeJ.items()) {
        shape.push_back(it.value().template get<std::size_t>());
      }
      if (shapeSize == 0) {
        value.push_back(j[JSD::value].dump());
      } else {
        value.reserve(j[JSD::value].size());
        for (auto it : j[JSD::value].items()) {
          value.push_back(it.value().dump());
        }
      }
      n->setShape(std::move(shape));
      n->setValue(std::move(value));
      n->open(false);
      return n;
    }

    virtual std::shared_ptr<DataBase> visitGlobalArrayNode(const T& j) {
      auto n = mks<typename DB::ShapeNode>(j);
      n->open(true);
      // Load the shape.

      auto shapeJ = j.contains(JSD::shape) ? j[JSD::shape] : json::object();
      std::size_t shapeSize = shapeJ.size();

      std::vector<std::size_t> shape;
      std::vector<std::shared_ptr<DataBase>> value;

      for (auto it : shapeJ.items()) {
        shape.push_back(it.value().template get<std::size_t>());
      }
      long long key = j[JSD::key].template get<long long>();

      int count = 0;
      value.reserve(j[JSD::children].size());

      for (auto& it : j[JSD::children].items()) {
        auto elm = mks_str<typename DB::DataNode>(std::to_string(count++));
        elm->setlocal(true);
        elm->setkey(key);

        // Push elm to the top of this stream.
        jstream->push(elm);
        int count1 = 0;
        for (auto& itt : it.value().items()) {
          visit(itt.value(), count1++);
        }
        jstream->pop();
        value.push_back(elm);
      }

      n->setShape(std::move(shape));
      n->setValue(std::move(value));

      n->open(false);
      return n;
    }

    virtual std::shared_ptr<typename DB::InfoNode> visitInfoNode(const T& j) {
      auto n = mks<typename DB::InfoNode>(j);
      n->open(true);
      n->settitle(j[JSD::title].template get<std::string>());
      n->setstart(j[JSD::date].template get<long>());
      
      
      n->setprov(std::make_shared<VnVProv>(j[JSD::prov]));
      
      n->setworkflow(j[JSD::workflow].template get<std::string>());
      n->setjobName(j[JSD::jobName].template get<std::string>());
      n->setfileStub(j[JSD::filestub].template get<std::string>());
      rootInternal()->setspec(j[JSD::spec]);
      auto cim = std::dynamic_pointer_cast<typename DB::CommInfoNode>(rootInternal()->getCommInfoNode());
      cim->setworldSize(j[JSD::worldSize].template get<int>());
      cim->setnodeMap(j[JSD::nodeMap]);
      cim->setversion(j[JSD::mpiversion].template get<std::string>());
      n->open(false);
      return n;
    };

    virtual void visitFileNode(const T& j) {

      std::shared_ptr<ProvFile> pf = std::make_shared<ProvFile>(j[JSD::prov]);
      bool input = j[JSD::input].template get<bool>();

      if (input) {
        rootInternal()->getInfoNode()->addInputFile(pf);
      } else {
        rootInternal()->getInfoNode()->addOutputFile(pf);
      }
    }

    virtual std::shared_ptr<typename DB::LogNode> visitLogNode(const T& j) {
      auto n = mks<typename DB::LogNode>(j);
      n->open(true);
      n->setpackage(j[JSD::package].template get<std::string>());
      n->setlevel(j[JSD::level].template get<std::string>());
      n->setmessage(j[JSD::message].template get<std::string>());
      n->setstage(std::to_string(j[JSD::stage].template get<int>()));
      n->setcomm(std::to_string(j[JSD::comm].template get<long>()));
      n->open(false);

      return n;
    };

    virtual std::shared_ptr<typename DB::TestNode> visitActionNodeStarted(const T& j) {
      std::string name = j[JSD::name].template get<std::string>();
      std::string package = j[JSD::package].template get<std::string>();
      std::string pn = package + ":" + name;

      if (!rootInternal()->getActions()->contains(pn)) {
        auto n = mks<typename DB::TestNode>(j);
        n->setusage(ITestNode::TestNodeUsage::ACTION);
        n->setpackage(package);
        n->open(true);
        rootInternal()->getActions()->insert(pn, n);
        return n;
      }
      return std::dynamic_pointer_cast<typename DB::TestNode>(rootInternal()->getActions()->get(pn));
    };

    virtual std::shared_ptr<typename DB::TestNode> visitActionNodeEnded(const T& j, std::shared_ptr<DataBase> node) {
      auto n = std::dynamic_pointer_cast<typename DB::TestNode>(node);
      ActionStage::type stage = j[JSD::stage].template get<ActionStage::type>();
      if (stage == ActionStage::final) {
        n->open(false);
      }
      return n;
    };

    virtual std::shared_ptr<typename DB::WorkflowNode> visitWorkflowStartedNode(const T& j) {
      auto n = mks<typename DB::WorkflowNode>(j);
      n->open(true);
      n->setpackage(j[JSD::package].template get<std::string>());
      n->setname(j[JSD::name].template get<std::string>());
      n->setinfo(j[JSD::info]);
      n->setstate("Started");
      return n;
    }

    virtual std::shared_ptr<typename DB::WorkflowNode> visitWorkflowUpdatedNode(const T& j) {
      auto n = std::dynamic_pointer_cast<typename DB::WorkflowNode>(rootInternal()->getWorkflowNode());
      n->setinfo(j[JSD::info]);
      n->setstate("Updated");
      return n;
    }

    virtual std::shared_ptr<typename DB::WorkflowNode> visitWorkflowEndedNode(const T& j) {
      auto n = std::dynamic_pointer_cast<typename DB::WorkflowNode>(rootInternal()->getWorkflowNode());
      n->setinfo(j[JSD::info]);
      n->setstate("Done");
      n->open(false);
      return n;
    }

    virtual std::shared_ptr<typename DB::TestNode> visitPackageNodeStarted(const T& j) {
      auto n = mks_str<typename DB::TestNode>("Information");
      n->setusage(ITestNode::TestNodeUsage::PACKAGE);
      n->open(true);
      n->setpackage(j[JSD::package].template get<std::string>());
      return n;
    };

    virtual std::shared_ptr<typename DB::TestNode> visitPackageNodeEnded(const T& j, std::shared_ptr<DataBase> node) {
      auto n = std::dynamic_pointer_cast<typename DB::TestNode>(node);
      n->open(false);
      return n;
    };

    virtual std::shared_ptr<typename DB::TestNode> visitInitializationStarted(const T& j) {
      auto n = std::dynamic_pointer_cast<typename DB::TestNode>(rootInternal()->getInitialization());
      n->setusage(ITestNode::TestNodeUsage::PACKAGE);
      n->open(true);
      n->setpackage(j[JSD::package].template get<std::string>());
      return n;
    };

    virtual std::shared_ptr<typename DB::TestNode> visitInitializationEnded(const T& j,
                                                                            std::shared_ptr<DataBase> node) {
      auto n = std::dynamic_pointer_cast<typename DB::TestNode>(node);
      n->open(false);
      return n;
    };

    virtual std::shared_ptr<typename DB::UnitTestNode> visitUnitTestNodeStarted(const T& j) {
      auto n = mks<typename DB::UnitTestNode>(j);
      n->open(true);
      n->setpackage(j[JSD::package].template get<std::string>());
      return n;
    };

    virtual std::shared_ptr<typename DB::UnitTestNode> visitUnitTestNodeEnded(const T& j,
                                                                              std::shared_ptr<DataBase> node) {
      auto n = std::dynamic_pointer_cast<typename DB::UnitTestNode>(node);

      auto results = std::dynamic_pointer_cast<typename DB::UnitTestResultsNode>(n->getResults());

      for (auto& it : j[JSD::results].items()) {
        auto r = mks<typename DB::UnitTestResultNode>(it.value());
        r->setdesc(it.value()[JSD::description].template get<std::string>());
        r->setresult(it.value()[JSD::result].template get<bool>());
        results->insert(r->getname(), r);
      }
      n->open(false);
      return n;
    }

    virtual std::shared_ptr<DataBase> visitDataNodeStarted(const T& j) {
      auto n = mks<typename DB::DataNode>(j);
      n->open(true);
      n->setkey(j[JSD::dtype].template get<long long>());
      return n;
    }

    virtual std::shared_ptr<IDataNode> visitDataNodeEnded(const T& j, std::shared_ptr<DataBase> node) {
      node->open(false);
      return std::dynamic_pointer_cast<typename DB::DataNode>(node);
    }

    virtual std::shared_ptr<typename DB::TestNode> visitTestNodeStarted(const T& j) {
      auto n = mks<typename DB::TestNode>(j);
      n->open(true);
      n->setuid(j[JSD::testuid].template get<long>());
      n->setpackage(j[JSD::package].template get<std::string>());

      auto b = j[JSD::internal].template get<bool>();
      n->setusage(b ? ITestNode::TestNodeUsage::INTERNAL : ITestNode::TestNodeUsage::TEST);
      n->setinternal(b);
      return n;
    }

    virtual std::shared_ptr<typename DB::TestNode> visitTestNodeIterStarted(
        const T& j, std::shared_ptr<typename DB::TestNode> node) {
      return node;
    };

    virtual std::shared_ptr<typename DB::TestNode> visitTestNodeIterEnded(const T& j, std::shared_ptr<DataBase> node) {
      return std::dynamic_pointer_cast<typename DB::TestNode>(node);
    };

    virtual std::shared_ptr<typename DB::TestNode> visitTestNodeEnded(const T& j, std::shared_ptr<DataBase> node) {
      auto n = std::dynamic_pointer_cast<typename DB::TestNode>(node);
      n->setresult(j[JSD::result].template get<bool>());
      n->open(false);
      return n;
    };

    virtual std::shared_ptr<typename DB::InjectionPointNode> visitInjectionPointStartedNode(const T& j,
                                                                                            long elementId) {
      auto n = mks<typename DB::InjectionPointNode>(j);
      n->setpackage(j[JSD::package].template get<std::string>());
      n->setcommId(j[JSD::comm].template get<long>());
      n->setstartIndex(elementId);
      // n->setstartTime(time);
      n->open(true);
      std::cout << n->getcommId() << " is the commId " << std::endl;
      return n;
    }

    virtual std::shared_ptr<typename DB::TestNode> visitFetchNode(const T& j,
                                                                  std::shared_ptr<typename DB::TestNode> node,
                                                                  long elementId) {
      std::string schema = j["schema"].dump();
      long expiry = j["expires"].template get<long>();
      long id = j["id"].template get<long>();
      long jid = j["jid"].template get<long>();
      std::string message = j["message"].template get<std::string>();

      node->setFetchRequest(schema, id, jid, expiry, message);
      return node;
    }

    virtual std::shared_ptr<typename DB::TestNode> visitFetchFailedNode(const T& j,
                                                                        std::shared_ptr<typename DB::TestNode> node,
                                                                        long elementId) {
      node->resetFetchRequest();
      return node;
    }
    virtual std::shared_ptr<typename DB::TestNode> visitFetchSuccessNode(const T& j,
                                                                         std::shared_ptr<typename DB::TestNode> node,
                                                                         long elementId) {
      node->resetFetchRequest();
      return node;
    }

    virtual std::shared_ptr<typename DB::InjectionPointNode> visitInjectionPointEndedNode(
        const T& j, std::shared_ptr<DataBase> node, long elementId) {
      auto n = std::dynamic_pointer_cast<typename DB::InjectionPointNode>(node);
      n->setendIndex(elementId);
      // n->setendTime(time);
      n->open(false);

      return n;
    }

    virtual std::shared_ptr<typename DB::InjectionPointNode> visitInjectionPointIterStartedNode(
        const T& j, std::shared_ptr<DataBase> node, long elementId) {
      auto n = std::dynamic_pointer_cast<typename DB::InjectionPointNode>(node);
      return n;
    };

    virtual std::shared_ptr<typename DB::InjectionPointNode> visitInjectionPointIterEndedNode(
        const T& j, std::shared_ptr<DataBase> node, long elementId) {
      auto n = std::dynamic_pointer_cast<typename DB::InjectionPointNode>(node);
      return n;
    }

    ParserVisitor() {}

    virtual void set(std::shared_ptr<Iterator<T>> jstream_, typename DB::RootNode* rootNode) {
      jstream = jstream_;
      _rootInternal = rootNode;
    }

    virtual ~ParserVisitor() {}

    std::atomic_bool read_lock = ATOMIC_VAR_INIT(false);
    std::atomic_bool write_lock = ATOMIC_VAR_INIT(false);
    std::atomic_bool kill_lock = ATOMIC_VAR_INIT(false);

    void kill() { kill_lock.store(true, std::memory_order_relaxed); }

    virtual void process() {
      jstream->start_stream_reader();

      rootInternal()->markReaderThread();

      long i = 0;
      long j = 0;
      bool changed = false;
      while (!jstream->isDone()) {
        if (kill_lock.load(std::memory_order_relaxed)) {
          break;
        }

        i = 0;
        changed = false;
        // Lets grab the write lock for 10000 lines -- see if that speeds it up a little.
        setWriteLock();
        while (i++ < 10000) {
          if (jstream->hasNext()) {
            auto p = jstream->next();
            visit(p.first, p.second);
            changed = true;
            j++;
          }
        }
        j++;
        if (changed) {
          rootInternal()->cache_persist(false);
          std::cout << rootInternal()->getId() << ": " << j << " lines processed" << std::endl;
        }
        releaseWriteLock();
      }

      rootInternal()->cache_persist(true);
      rootInternal()->setProcessing(false);
      rootInternal()->open(false);
      jstream->stop_stream_reader();
      std::cout << rootInternal()->getId() << ": File Parsing Complete " << std::endl;
    }
    virtual void setWriteLock() {
      while (read_lock.load(std::memory_order_relaxed)) {
      }
      write_lock.store(true, std::memory_order_relaxed);
    }

    virtual void releaseWriteLock() { write_lock.store(false, std::memory_order_relaxed); }

    void lock() override {
      read_lock.store(true, std::memory_order_relaxed);
      while (write_lock.load(std::memory_order_relaxed)) {
      }
    }

    void release() override { read_lock.store(false, std::memory_order_relaxed); }

    void childNodeDispatcher(std::shared_ptr<DataBase> child) {
      std::shared_ptr<DataBase> parent = jstream->top();

      DataBase::DataType ptype = (parent == nullptr) ? DataBase::DataType::Root : parent->getType();
      DataBase::DataType ctype = child->getType();

      if (ptype == DataBase::DataType::Shape) {
        auto p = std::dynamic_pointer_cast<typename DB::ShapeNode>(parent);
        p->add(child);

      } else if (ptype == DataBase::DataType::Test) {
        std::shared_ptr<ITestNode> p1 = std::dynamic_pointer_cast<ITestNode>(parent);
        if (ctype == DataBase::DataType::Log) {
          p1->getLogs()->add(child);
        } else {
          p1->getData()->insert(child->getName(), child);
        }

      } else if (ptype == DataBase::DataType::UnitTest) {
        auto p = std::dynamic_pointer_cast<typename DB::UnitTestNode>(parent);
        if (ctype == DataBase::DataType::Log) {
          p->getLogs()->add(child);
        } else {
          p->getData()->insert(child->getName(), child);
        }

      } else if (ptype == DataBase::DataType::Data) {
        auto p = std::dynamic_pointer_cast<typename DB::DataNode>(parent);
        if (ctype == DataBase::DataType::Log) {
          p->getLogs()->add(child);
        } else {
          p->getData()->insert(child->getName(), child);
        }

      } else if (ptype == DataBase::DataType::InjectionPoint &&
                 std::dynamic_pointer_cast<typename DB::InjectionPointNode>(parent)->getisOpen()) {
        auto p = std::dynamic_pointer_cast<typename DB::InjectionPointNode>(parent);

        if (ctype == DataBase::DataType::Test) {
          if (child->getAsTestNode(child)->isInternal()) {
            auto a = std::dynamic_pointer_cast<typename DB::TestNode>(child);
            p->setinternal(a);
          } else {
            p->getTests()->add(child);
            std::cout << "Adding test to tests" << p->getTests()->size() << std::endl;
            p->getTestByUID(0);
          }

        } else if (ctype == DataBase::DataType::Log) {
          p->getLogs()->add(child);
        } else {
          INJECTION_EXCEPTION(
              "This should not happen -- Valid children for an injection point are types Test or Log, but this is type "
              "%s",
              child->getTypeStr().c_str());
        }

      } else if (ctype == DataBase::DataType::InjectionPoint) {
      } else if (ctype == DataBase::DataType::Log) {
        rootInternal()->getLogs()->add(child);
      } else {
        throw INJECTION_EXCEPTION("Unsupported Parent element type %s", parent->getTypeStr().c_str());
      }
    }

    void visit(const T& j, long elementId) {
      std::string node = j[JSD::node].template get<std::string>();

      if (node == JSN::finalTime) {
        auto i = rootInternal()->getInfoNode();
        std::dynamic_pointer_cast<typename DB::InfoNode>(i)->setend(j[JSD::time].template get<long>());

      } else if (node == JSN::done) {
        // DONE
      } else if (node == JSN::commInfo) {
        auto p = visitCommNode(j);
        rootInternal()->getCommInfoNode()->add(p.first, p.second);

      } else if (node == JSN::file) {
        visitFileNode(j);
      } else if (node == JSN::dataTypeEnded) {
        visitDataNodeEnded(j, jstream->pop());

      } else if (node == JSN::dataTypeStarted) {
        auto n = visitDataNodeStarted(j);
        childNodeDispatcher(n);
        jstream->push(n);
      } else if (node == JSN::workflowStarted) {
        rootInternal()->setworkflowNode(visitWorkflowStartedNode(j));
      } else if (node == JSN::workflowUpdated) {
        visitWorkflowUpdatedNode(j);
      } else if (node == JSN::workflowFinished) {
        visitWorkflowEndedNode(j);
      } else if (node == JSN::info) {
        rootInternal()->setinfoNode(visitInfoNode(j));
      } else if (node == JSN::fetch) {
        if (jstream->top()->check(DataBase::DataType::Test)) {
          std::shared_ptr<typename DB::TestNode> p = std::dynamic_pointer_cast<typename DB::TestNode>(jstream->top());
          visitFetchNode(j, p, elementId);
        }
      } else if (node == JSN::fetchFail) {
        if (jstream->top()->check(DataBase::DataType::Test)) {
          std::shared_ptr<typename DB::TestNode> p = std::dynamic_pointer_cast<typename DB::TestNode>(jstream->top());
          visitFetchFailedNode(j, p, elementId);
        }
      } else if (node == JSN::fetchSuccess) {
        if (jstream->top()->check(DataBase::DataType::Test)) {
          std::shared_ptr<typename DB::TestNode> p = std::dynamic_pointer_cast<typename DB::TestNode>(jstream->top());
          visitFetchSuccessNode(j, p, elementId);
        }
      } else if (node == JSN::injectionPointEnded) {
        // This injection point is done.
        std::shared_ptr<typename DB::InjectionPointNode> p =
            std::dynamic_pointer_cast<typename DB::InjectionPointNode>(jstream->pop());
        p->setisOpen(false);
        visitInjectionPointEndedNode(j, p, elementId);

        // Close the tests
        auto tests = p->getTests();
        for (int i = 0; i < tests->size(); i++) {
          tests->get(i)->open(false);
        }

        rootInternal()->addIDN(p->getId(), p->getstreamId(), node_type::END, elementId, "End");

      } else if (node == JSN::injectionPointStarted) {
        std::shared_ptr<typename DB::InjectionPointNode> p = visitInjectionPointStartedNode(j, elementId);

        p->setisOpen(true);
        childNodeDispatcher(p);
        jstream->push(p);

        rootInternal()->addIDN(p->getId(), p->getstreamId(), node_type::START, elementId, "Begin");

      } else if (node == JSN::injectionPointIterEnded) {
        std::shared_ptr<typename DB::InjectionPointNode> p =
            std::dynamic_pointer_cast<typename DB::InjectionPointNode>(jstream->top());
        visitInjectionPointIterEndedNode(j, p, elementId);
        p->setisOpen(false);
        p->setisIter(false);

      } else if (node == JSN::injectionPointIterStarted) {
        assert(jstream->top()->getType() == DataBase::DataType::InjectionPoint);
        std::shared_ptr<typename DB::InjectionPointNode> p =
            std::dynamic_pointer_cast<typename DB::InjectionPointNode>(jstream->top());

        visitInjectionPointIterStartedNode(j, p, elementId);
        std::string stage = j[JSD::stageId].template get<std::string>();
        p->setisOpen(true);
        p->setisIter(true);

      } else if (node == JSN::log) {
        std::shared_ptr<typename DB::LogNode> n = visitLogNode(j);
        n->setidentity(elementId);
        childNodeDispatcher(n);

      } else if (node == JSN::testFinished) {
        auto p = jstream->pop();

        assert(jstream->top()->getType() == DataBase::DataType::InjectionPoint);
        auto pp = std::dynamic_pointer_cast<typename DB::InjectionPointNode>(jstream->top());
        if (pp->getisIter()) {
          visitTestNodeIterEnded(j, p);
        } else {
          visitTestNodeEnded(j, p);
        }

      } else if (node == JSN::testStarted) {
        auto p = jstream->top();
        if (p->getType() != DataBase::DataType::InjectionPoint) {
          throw INJECTION_EXCEPTION("Bad Heirrarchy: Test Started called when top of stack is %s",
                                    p->getTypeStr().c_str());
        }

        std::shared_ptr<typename DB::InjectionPointNode> pp =
            std::dynamic_pointer_cast<typename DB::InjectionPointNode>(p);

        if (pp->getisIter()) {
          long uid = j[JSD::testuid].template get<long>();
          auto tests = pp->getTests();

          if (j[JSD::internal].template get<bool>()) {
            auto t = std::dynamic_pointer_cast<typename DB::TestNode>(pp->getinternal());
            if (t->getuid() != uid) {
              throw INJECTION_EXCEPTION("Test UID is %d and message uid is %d", t->getuid(), uid);
            }
            visitTestNodeIterStarted(j, t);
            jstream->push(t);
          } else {
            bool found = false;

            auto t = pp->getTestByUID(uid);
            if (t != nullptr) {
              visitTestNodeIterStarted(j, t);
              jstream->push(t);
            } else {
              throw INJECTION_EXCEPTION("Test UID does not exist : %d", uid);
            }
          }
        } else {
          std::shared_ptr<typename DB::TestNode> t = visitTestNodeStarted(j);
          childNodeDispatcher(t);
          jstream->push(t);
        }

      } else if (node == JSN::unitTestFinished) {
        visitUnitTestNodeEnded(j, jstream->pop());

      } else if (node == JSN::unitTestStarted) {
        auto u = visitUnitTestNodeStarted(j);
        rootInternal()->getUnitTests()->add(u);
        jstream->push(u);
      } else if (node == JSN::actionStarted) {
        auto po = visitActionNodeStarted(j);
        jstream->push(po);
      } else if (node == JSN::actionFinished) {
        auto u = visitActionNodeEnded(j, jstream->pop());
      } else if (node == JSN::packageOptionsStarted) {
        auto po = visitPackageNodeStarted(j);
        rootInternal()->getPackages()->insert(po->getPackage(), po);

        jstream->push(po);
      } else if (node == JSN::packageOptionsFinished) {
        auto u = visitPackageNodeEnded(j, jstream->pop());
      } else if (node == JSN::initializationStarted) {
        auto po = visitInitializationStarted(j);
        jstream->push(po);
      } else if (node == JSN::initializationEnded) {
        auto u = visitInitializationEnded(j, jstream->pop());
      }

      else if (node == JSN::shape) {
        std::string type = j[JSD::dtype].template get<std::string>();

        if (type == JST::String) {
          childNodeDispatcher(visitShapeNode<typename DB::StringNode, std::string>(j));

        } else if (type == JST::Bool) {
          childNodeDispatcher(visitShapeNode<typename DB::BoolNode, bool>(j));

        } else if (type == JST::Long) {
          childNodeDispatcher(visitShapeNode<typename DB::LongNode, long>(j));

        } else if (type == JST::Double) {
          childNodeDispatcher(visitShapeNode<typename DB::DoubleNode, double>(j));

        } else if (type == JST::Json) {
          childNodeDispatcher(visitJsonNode(j));

        } else if (type == JST::GlobalArray) {
          childNodeDispatcher(visitGlobalArrayNode(j));

        } else {
          throw INJECTION_EXCEPTION("Bad data type %s", type.c_str());
        }

      } else {
        throw INJECTION_EXCEPTION("Unrecognized Node Type %s", node.c_str());
      }
    }
  };

  template <class T> class NoLockParserVisitor : public ParserVisitor<T> {
   public:
    virtual void setWriteLock() override {}
    virtual void releaseWriteLock() override {}
  };

  template <typename T, typename V> class RootNodeWithThread : public DB::RootNode {
   public:
    std::shared_ptr<ParserVisitor<V>> visitor;
    std::shared_ptr<T> stream;

    std::thread tworker;
    bool running = false;

    void run(bool async) {
      if (async) {
        running = true;
        tworker = std::thread(&ParserVisitor<V>::process, visitor.get());
      } else {
        visitor->process();
      }
    }

    void kill() override {
      if (running) {
        visitor->kill();
        if (tworker.joinable()) {
          tworker.join();
        }
        running = false;
      }
    }
    virtual ~RootNodeWithThread() {
      // We SHOULD be calling kill before destruction. The thread calls virtual methods on the IRootNode
      // as part of the loop. If we don't kill this first, then the thread could call virtual methods
      // of a derived class that is already destroyed (or something ). In other words, this class is a topsy-turvy
      // mess :{}. Just in case, we kill here to (so it doesnt seg fault)

      if (running) {
        kill();
      }
    }

    void lock() override { visitor->lock(); }
    void release() override { visitor->release(); }

    virtual void respond(long id, long jid, const std::string& response) override {
      if (stream != nullptr) {
        stream->respond(id, jid, json::parse(response));
      }
    }

    virtual std::thread* getThread() override { return &tworker; }

    static std::shared_ptr<IRootNode> parse(bool async, std::shared_ptr<T> stream,
                                            std::shared_ptr<ParserVisitor<V>> visitor = nullptr) {
      std::shared_ptr<RootNodeWithThread> root = std::make_shared<RootNodeWithThread>();
      root->registerNode(root);
      root->setname("Root Node");
      root->setreportDirectory(stream->getFileStub());
      root->stream = stream;
      root->visitor = (visitor == nullptr) ? std::make_shared<ParserVisitor<V>>() : visitor;

      root->visitor->set(stream, root.get());
      root->open(true);
      root->run(async);
      return root;
    }
  };
};

  }
}

#endif
