from datetime import datetime
from proactive.priority.order import Order
from unittest import TestCase


class TestOrder(TestCase):
  def setUp(self):
    self.orderID = "test1234"
    self.status = Order.Status.UNPROCESSED
    self.processing = 100
    self.customerCoordinates = {"lat": 53.345466, "lng": -6.278987}
    self.cost = 2.56
    self.createdAt = datetime.now()


  def test_init(self):
    order = Order(
      orderID=self.orderID,
      status=self.status,
      processing=self.processing,
      customerCoordinates=self.customerCoordinates,
      cost=self.cost,
      createdAt=self.createdAt
    )
    self.assertEqual(order.orderID, self.orderID)
    self.assertEqual(order.status, self.status)
    self.assertEqual(order.processing, self.processing)
    self.assertEqual(order.customerCoordinates, self.customerCoordinates)
    self.assertEqual(order.cost, self.cost)
    self.assertEqual(order.createdAt, self.createdAt)
