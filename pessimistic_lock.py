import hazelcast

if __name__ == "__main__":
  client = hazelcast.HazelcastClient(
  cluster_name="haz-cluster", 
  ) 

  map = client.get_map("number-map").blocking() 
  
  map.put_if_absent("key_pessimistic", 0)

  for k in range(10_000):
    map.lock("key_pessimistic")
    try:
        value = map.get("key_pessimistic")
        value += 1
        map.put("key_pessimistic", value)
    finally:
        map.unlock("key_pessimistic")

