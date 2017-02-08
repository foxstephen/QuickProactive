from datetime import datetime
from intervaltree import IntervalTree
from .exceptions import LateDeadlineException, ExceededWorkerMultitaskLimit
from .taskunitpriorityqueue import TaskUnitPriorityQueue
from .workerqueue import WorkerQueue
from .worker import Worker

class ConflictSet(object):
  def __init__(self, conflicts):
    self._conflicts = conflicts

  def allLessThanOrEqual(self, value):
    conflicts = []
    for conflict in self._conflicts:
      if len(conflict) <= value:
        conflicts.append(conflict)
    return conflicts

  def allGreaterThan(self, value):
    conflicts = []
    for conflict in self._conflicts:
      if len(conflict) > value:
        conflicts.append(conflict)
    return conflicts

  def max(self):
    maxConflict = None
    maxSize = 0
    for conflict in self._conflicts:
      if len(conflict) > maxSize:
        maxConflict = conflict
        maxSize = len(conflict)
    return maxConflict

  def flatten(self):
    intervals = []
    for x in self._conflicts:
      for y in x:
        intervals.append(y)
    return intervals



class TaskManager(object):
  def __init__(self, period):
    self._tasksQ = TaskUnitPriorityQueue()
    self._tasks = []
    self._intervalTree = IntervalTree()
    self._workers = WorkerQueue()
    self._assignedTasks = []
    self._unassignedTasks = []
    if isinstance(period[0], datetime) and isinstance(period[1], datetime):
      self.__start = period[0]
      self.__end = period[1]
    else:
      raise TypeError(
        "period[0] and period[1] should be type<'datetime'>."
      )

  @property
  def assignedTasks(self):
    return self._assignedTasks

  @property
  def unassignedTasks(self):
    return self._unassignedTasks

  @property
  def tasks(self):
    """
      Returns all the tasks the manager currently holds.
      The tasks are return in no particular order.
    """
    return self._tasksQ.items()

  def addTask(self, task):
    if task.deadline > self.__end:
      raise LateDeadlineException(
        "Cannot process this task as it's deadline is %s is after %s"
        % (task.deadline, self.__end)
      )
    if task not in self._tasks:
      self._tasks.append(task)
      self._tasksQ.push(task)
      self._addTaskToTree(task)

  def addTasks(self, tasks):
    for task in tasks:
      self.addTask(task)

  def _addTaskToTree(self, task):
    self._intervalTree.addi(
      begin=task.release,
      end=task.deadline,
      data=task.taskID
    )

  def findConflicts(self):
    """
      Finds all the conflicts within the tasks set.
      A conflict being, any two or more tasks that need
      to be proccessed at some point simultaneously.
      In terms of an interval tree, the two task times 'overlap'.

      This method finds all the conflicts of the current task set
      held by this class.
    """
    begin = self._intervalTree.begin()
    end = self._intervalTree.end()
    conflicts = []
    intervals = sorted(self._intervalTree[begin:end])
    for interval in intervals:
      _intervals = self._intervalTree[interval.begin:interval.end]
      if len(_intervals) > 1: # theres a conflict
        if _intervals not in conflicts:
          conflicts.append(_intervals)
    return ConflictSet(conflicts)

  def findNonConflicts(self):
    conflicts = self.findConflicts().flatten()
    return self._intervalTree.difference(conflicts).items()

  def highestNumberOfWorkersNeeded(self, multitask=1):
    """
      Calculates the highest number of employees needed
      to service the tasks set.
      @param multitask:(int) The maximum amount of tasks a single
        worker can complete at any given time simultaneously.
    """
    conflict = self.findConflicts().max()
    return self.workersNeeded(len(conflict), multitask)

  def workersNeeded(self, k, m):
    """
      Calculates the number of employees needed to deal with a conflict.
      @param k:() The number of conflicts
      @param m:() The highest number of tasks employees can service simultaneously.
    """
    # formula: k/m
    from math import ceil
    return ceil(float(k)/float(m))

  def addWorker(self, worker):
    if isinstance(worker, Worker):
      self._workers.put(worker)
    else:
      raise TypeError(
        "Cannot add worker type %s, should be type<'Worker'>" % type(worker)
      )

  def addWorkers(self, workers):
    for w in workers:
      self.addWorker(w)

  def assignTasksToWorkers(self):
    for task in self._tasksQ:
      worker = self._workers.next()
      self._intervalTree.removei(task.release, task.deadline, task.taskID)
      try:
        worker.assignTask(task)
        task.assignWorker(worker)
        self._assignedTasks.append(task)
      except ExceededWorkerMultitaskLimit:
        self._unassignedTasks.append(task)
