import hazelcast

# key_name = "key"
# key_name = "key_pessimistic"
key_name = "key_optimistic"

if __name__ == "__main__":
  client = hazelcast.HazelcastClient(
  cluster_name="haz-cluster", 
  ) 

  map = client.get_map("number-map").blocking() 
  
  value = map.get(key_name)
  print("Final value from this client:", value)

  client.shutdown()
