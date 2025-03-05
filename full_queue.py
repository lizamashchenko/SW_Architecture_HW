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

def main():
  client = hazelcast.HazelcastClient(
    cluster_name="haz-cluster", 
  ) 

  bounded_queue = client.get_queue("bounded-queue").blocking()

  producer_thread = threading.Thread(target=producer, args=(bounded_queue,))
  
  producer_thread.start()

  producer_thread.join()

  client.shutdown()

if __name__ == "__main__":
  main()
