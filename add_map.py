import hazelcast

if __name__ == "__main__":
  client = hazelcast.HazelcastClient(
  cluster_name="haz-cluster", 
  ) 

  map = client.get_map("number-map").blocking() 
  
  for i in range(1000):
    map.put(i, f"value-{i}")