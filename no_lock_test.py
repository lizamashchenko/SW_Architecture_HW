import hazelcast

if __name__ == "__main__":
  client = hazelcast.HazelcastClient(
  cluster_name="haz-cluster", 
  ) 

  map = client.get_map("number-map").blocking() 
  
  map.put_if_absent("key", 0)

  for k in range(10_000):
    value = map.get("key")
    value += 1
    map.put("key", value)