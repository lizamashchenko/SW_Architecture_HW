import hazelcast
import threading
import time

def producer(queue):
  for i in range(1, 101):
    queue.put(i)
    print(f"Producing: {i}")
    time.sleep(0.1)
    
  print(f"Producing poison pill")
  queue.put(-1)

def consumer(queue, consumer_id):
  while True:
    item = queue.take()

    if (item == -1):
      queue.put(-1)
      print(f'Consumer-{consumer_id} ate a poison pill')
      break
    print(f"Consumer-{consumer_id} consumed: {item}")

def main():
  client = hazelcast.HazelcastClient(
    cluster_name="haz-cluster", 
  ) 

  bounded_queue = client.get_queue("bounded-queue").blocking()

  producer_thread = threading.Thread(target=producer, args=(bounded_queue,))
  consumer_thread1 = threading.Thread(target=consumer, args=(bounded_queue, 1))
  consumer_thread2 = threading.Thread(target=consumer, args=(bounded_queue, 2))
  
  producer_thread.start()
  consumer_thread1.start()
  consumer_thread2.start()

  producer_thread.join()
  consumer_thread1.join()
  consumer_thread2.join()

  client.shutdown()

if __name__ == "__main__":
  main()
