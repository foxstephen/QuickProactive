from apscheduler.schedulers.background import BackgroundScheduler
from proactive.config import Configuration
from proactive.travel import Travel, metric
from .order import Order
from .taskunit import TaskUnit
from .queueworker import QueueWorker


class PriorityWorker(QueueWorker):
  def __init__(self, business, ordersDBConn, queue, refresh=5000):
    """
      @param ordersDBConn:(db.prioritydb.PriorityDB) Database connection to read orders from.

      @param businessID:(str) The id of the business.

      @param queue:(orderpriority.TaskUnitPriorityQueue) A OrderPriorityQueue instance.

      @param refresh:(int) - milliseconds: How often the database should be read to when checking
        for new orders. How often the database should be written to with the current state of the
        priority queue.
    """
    self._businessCoordinates = business["coordinates"]
    self._businessID = business["id"]
    self._ordersDBConn = ordersDBConn
    self._pQueue = queue
    self._refresh = refresh
    self._config = Configuration()
    self._travel = Travel(gmapsKey=self._config.read([Configuration.GMAPS_KEY])[0])
    self.__scheduler = BackgroundScheduler()
    self.__queueState = None


  def __readUnprocessedOrders(self):
    return self._ordersDBConn.read(self._businessID)

  def run(self):
    self.__scheduler.add_job(self.__monitor, 'interval', seconds=self._refresh/1000)
    self.__scheduler.start()

  def stop(self):
    self.__scheduler.shutdown()


  def __monitor(self):
    """
      Monitors the unprocessed orders and keeps the queue attribute
      in order according to how the orders should be released.
    """
    from threading import current_thread
    print(current_thread())
    try:
      self._pQueue.popAll()
    except IndexError:
      pass

    freshOrders = self.__readUnprocessedOrders()
    for order in freshOrders:
      orderObj = Order(
        orderID=str(order["id"]),
        status=order["status"],
        processing=order["processing"],
        customerCoordinates=order["coordinates"],
        createdAt=order["createdAt"],
        cost=order["cost"]
      )
      deadline = self._customerArrivalTime(orderObj.customerCoordinates)

      taskUnit = TaskUnit(
        orderObj.createdAt,
        deadline,
        orderObj.cost,
        orderObj.processing,
        orderObj.orderID
      )
      self._pQueue.add(taskUnit)
      self._pQueue.printQueue()
      self.__queueState = self._pQueue.asDict()


  def _customerArrivalTime(self, customerCoordinates):
    return self._travel.find(
      self._businessCoordinates,
      customerCoordinates,
      metric.DURATION,
      measure="value"
    )

  def _calculateCustomerDistance(self, order):
    pass

  def currentQueueState(self):
    return self.__queueState

