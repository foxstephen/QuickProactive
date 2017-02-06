from datetime import datetime
from dateutil import parser as dateparser
from proactive.utils import timeutil
from .priority import Priority


class TaskUnit(Priority):
  def __init__(self, createdAt, deadline, profit, processing, release=None, taskID=None, data=None):
    """
      A task unit is a schedulable piece of work that needs to be completed
      before a deadline.

      A TaskUnit is composed of the following properties:
        t_unit = (c, r,d,p,w)
        c - createdAt
        r - release time
        d - deadline
        p - processing time
        w - weight profit.

      @param createdAt:(datetime) The time the task arrived into the system or was made.
      @param deadline: The deadline. In seconds from now or datetime format.
      @param profit:(double) The potential profit from getting this task finished on on time.
      @param processing:(int) The number of seconds the task will take to process.
      @param release Release time in datetime format.
      @param taskID:(str) The id of the task.
      @param data:(object) Optionally an TaskUnit can encapsulate another object that
        has a relationship with the unit of work. For example, the most common scenario
        for this application would be customer orders. An order itself can be viewed
        as a unit of work, however it makes more sense to encapsulate it into a generic form
        i.e this class.
    """
    self._createdAt = createdAt
    self._createdAtISO = createdAt.isoformat()
    self._processing = processing
    self._deadline = deadline

    if not isinstance(self._deadline, datetime): #check deadline type
      self._deadlineISO = timeutil.addSeconds(createdAt, self._deadline).isoformat()
    else:
      self._deadlineISO = self._deadline.isoformat()
    if release is None:
      from . import release
      self._release = release.releaseAt(self.deadline, self._processing, self.createdAt)
    else:
      # as release is given, make sure its not after deadline.
      if release > self._deadline:
        raise ValueError(
          "Release time is later than deadline, this is not allowed."
        )
      else:
        self._release = release

    self._releaseISO = self._release.isoformat()
    self._profit = profit
    self._taskID = taskID
    self._data = data

  @property
  def createdAt(self):
    return self._createdAt

  @property
  def createdAtISO(self):
    return self._createdAtISO

  @property
  def deadline(self):
    return self._deadline

  @property
  def deadlineISO(self):
    return self._deadlineISO

  @property
  def processing(self):
    return self._processing

  @property
  def release(self):
    return self._release

  @property
  def releaseISO(self):
    return self._releaseISO

  @property
  def profit(self):
    return self._profit

  @property
  def taskID(self):
    return self._taskID

  @property
  def data(self):
    return self._data

  def __lt__(self, other):
    return self.priority() < other.priority()

  def priority(self):
    return self.release

  def asDict(self):
    return {
      "id": self.taskID,
      "releaseISO": self._releaseISO,
      "deadlineISO": self._deadlineISO,
      "deadline": self._deadline,
      "profit": self._profit,
      "processing": self._processing,
      "createdAtISO": self._createdAtISO
    }

