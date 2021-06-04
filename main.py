"""
the problem as i understand it: there is need for an inventory management and order processing system.
it needs to
	start with an empty inventory,
	capture a list of data to represent potential products to be stocked into inventory and ordered by customers,
	receive orders from customers,
	divide orders up into packages that respect the weight limit and inventory quantities,
	ship each package as soon as it's completed and return relative shipping information,
	handle orders that cannot be completed due to inventory shortage,
	replenish inventory and revisit unfilled orders.
	
a few things about this problem immediately jumped out at me, i need to make sure the inventory reflects the outgoing
products, i need to make sure i responsibly store the orders that could not be wholly completed, and that there probably
was some kind of algorithm to make combining possible products for shipments easier. then i remembered knapsack, and i
did some research on how it works and how to properly implement it.

a typical knapsack problem is about finding a subset of an array that produces the biggest "profit" while staying
under a given capacity, two integer arrays represent the weight and "profit" of 'N' items, each item can only
be chosen once, and items that are not chosen are (usually) no longer regarded.

2 hours for research and design
2.5 hours of implementation

"""
from collections import defaultdict, deque

# (0, 1, 2) for future index reference
product_id, product_name, product_mass = range(3)
# 1800kg
MAX_CAPACITY = 1800


class Zipline:
	def __init__(self):
		self.inventory = defaultdict(int)
		self.catalog = dict()
		self.unfulfilled = deque()
	
	def init_catalog(self, product_info):
		"""
		initialize the catalog with product id, name, and price
		does necessary data preprocessing
		self.inventory should still be empty after this function runs
		:param product_info: sample catalog
		:return: void
		"""
		for item in product_info:
			self.inventory[item['product_id']] = 0
			self.catalog[item['product_id']] = (item['product_id'], item['product_name'], item['mass_g'])
	
	def _chunk(self, requested, items, quantity, mass):
		"""
		check for items in inventory, and sorts them into shipments based on weight limits
		:param requested: product id and quantity for each item a customer is ordering
		:param items: [product ids]
		:param quantity: [quantities]
		:param mass: [mass of respective items]
		:return: void
		"""
		
		counts = [0 for _ in range(len(items))]  # [0, 0]
		result = [0 for _ in range(len(items))]  # [0, 0]
		
		closest_sum = 0
		
		def knap(c, i):
			"""
			implement knapsack algorithm,
			find possible combinations of products where their mass does not exceed capacity
			i researched multiple implementations of this and tried my best to implement it
			:param c: capacity int
			:param i: [items]
			:return: a dictionary with the best combination of product id and quantity
							where total mass does not exceed capacity
			"""
			nonlocal closest_sum, result
			#  base case
			if c < 0:
				return
			
			# if there are no items left in list or the capacity has been fully met
			if i >= len(items) or c == 0:
				# capacity amount that has not been utilized
				total_mass = sum([mass[i] * counts[i] for i in range(len(counts))])
				# if max capacity minus the amount of capacity that has not been used yet
				# is less than max capacity minus the amount that has been used
				if MAX_CAPACITY - total_mass < MAX_CAPACITY - closest_sum:
					closest_sum = total_mass
					result = counts[:]
				return
			
			# if the quantity of requested items is not 0 and the inventory for the item is not 0 and we have some capacity left
			if requested[items[i]] > 0 and self.inventory[items[i]] > 0 and mass[i] <= c:
				counts[i] += 1
				requested[items[i]] -= 1
				self.inventory[items[i]] -= 1
				# this knap call subtracts the mass of the selected product from the capacity, and recurses the same index point
				knap(c - mass[i], i)
				counts[i] -= 1
				requested[items[i]] += 1
				self.inventory[items[i]] += 1
			
			# this call moves the index one element without selecting an item
			knap(c, i + 1)
			
			# return array representing subset of items that together, do not exceed the max capacity
			return result
		
		# initial call to knap function
		knap(MAX_CAPACITY, 0)
		
		# returns optimum combination that will be used to ship
		return result
	
	def process_order(self, order):
		"""
		massage incoming order data to be processed by _process order
		and stores orders with no available inventory to unfulfilled list
		after chunking and processing the available invetnory for shipment
		:param order: requested item product ids and quantities
		:return: void
		"""
		order_id = order['order_id']
		requested = {r['product_id']: r['quantity'] for r in order['requested']}
		
		self._process_order(order_id, requested)
		# after processing an order, if any requested items are left, append to unfulfilled list
		if sum(requested.values()) > 0:
			self.unfulfilled.append((order_id, requested))
	
	def _process_order(self, order_id, requested):
		"""
		organizes the product ids, quantities, and mass amounts used for _chunk
		calls the ship_package method for each organized order
		and subtracts the shipped items from the inventory
		:param order_id: id for individual orders
		:param requested: product id and quantity for each item a customer is ordering
		:return: void
		"""
		items, quantities = zip(*list(requested.items()))
		mass = [self.catalog[item_id][product_mass] for item_id in items]
		
		order_chunk = self._chunk(requested, items, quantities, mass)
		
		# while there are still processed items that have not been shipped
		while sum(order_chunk) > 0:
			receipt = list(zip(items, order_chunk))
			self.ship_package(order_id, receipt)
			# subtract sent items from the requested and inventory
			for key, amount in receipt:
				requested[key] -= amount
				self.inventory[key] -= amount
			
			order_chunk = self._chunk(requested, items, quantities, mass)
	
	def _process_unfulfilled(self):
		"""
		from oldest, unfulfilled orders first, check if they can be processed
		if order is successfully fulfilled, it does not go back into this queue
		:return: void
		"""
		for _ in range(len(self.unfulfilled)):
			(order_id, requested) = self.unfulfilled.popleft()
			self._process_order(order_id, requested)
			if sum(requested.values()) > 0:
				self.unfulfilled.append((order_id, requested))
	
	def process_restock(self, restock):
		"""
		take a list of items and increment their quantities in the inventory dictionary
		after update, calls _process_unfulfilled function to fulfill older orders
		:param restock: inventory being restocked
		:return: void
		"""
		for item in restock:
			self.inventory[item['product_id']] += item['quantity']
		
		self._process_unfulfilled()
	
	def ship_package(self, order_id, receipt):
		"""
		takes order id, and shipped product ids and quantities and "ships"
		:param order_id: order id
		:param receipt: contains prodcut id and quantity
		:return: readable receipt form with order id and shipment details
		"""
		return print({"order_id": order_id, "shipped": [{"product_id": id, "quantity": q} for id, q in receipt]})


items = [{"mass_g": 700, "product_name": "RBC A+ Adult", "product_id": 0},
         {"mass_g": 700, "product_name": "RBC B+ Adult", "product_id": 1},
         {"mass_g": 750, "product_name": "RBC AB+ Adult", "product_id": 2},
         {"mass_g": 680, "product_name": "RBC O- Adult", "product_id": 3},
         {"mass_g": 350, "product_name": "RBC A+ Child", "product_id": 4},
         {"mass_g": 200, "product_name": "RBC AB+ Child", "product_id": 5},
         {"mass_g": 120, "product_name": "PLT AB+", "product_id": 6},
         {"mass_g": 80, "product_name": "PLT O+", "product_id": 7},
         {"mass_g": 40, "product_name": "CRYO A+", "product_id": 8},
         {"mass_g": 80, "product_name": "CRYO AB+", "product_id": 9},
         {"mass_g": 300, "product_name": "FFP A+", "product_id": 10},
         {"mass_g": 300, "product_name": "FFP B+", "product_id": 11},
         {"mass_g": 300, "product_name": "FFP AB+", "product_id": 12}]

rest = [{"product_id": 0, "quantity": 4}, {"product_id": 1, "quantity": 25}, {"product_id": 2, "quantity": 25},
        {"product_id": 3, "quantity": 12}, {"product_id": 4, "quantity": 15}, {"product_id": 5, "quantity": 10},
        {"product_id": 6, "quantity": 8}, {"product_id": 7, "quantity": 8}, {"product_id": 8, "quantity": 20},
        {"product_id": 9, "quantity": 10}, {"product_id": 10, "quantity": 5}, {"product_id": 11, "quantity": 5},
        {"product_id": 12, "quantity": 5}]

zep = Zipline()
zep.init_catalog(items)
print(zep.catalog)

zep.process_restock(rest)
print(zep.inventory)

order = {"order_id": 123, "requested": [{"product_id": 0, "quantity": 6}, {"product_id": 10, "quantity": 4}]}
zep.process_order(order)

order = {"order_id": 124, "requested": [{"product_id": 12, "quantity": 6}, {"product_id": 8, "quantity": 4}]}
zep.process_order(order)

order = {"order_id": 125, "requested": [{"product_id": 4, "quantity": 61}, {"product_id": 5, "quantity": 4}]}
zep.process_order(order)

order = {"order_id": 126, "requested": [{"product_id": 9, "quantity": 9}, {"product_id": 2, "quantity": 40}]}
zep.process_order(order)

order = {"order_id": 127, "requested": [{"product_id": 9, "quantity": 0}, {"product_id": 2, "quantity": 0}]}
zep.process_order(order)

print(zep.inventory)
print(zep.unfulfilled)

print('Restocking...')
zep.process_restock(rest)

print(zep.inventory)
print(zep.unfulfilled)
