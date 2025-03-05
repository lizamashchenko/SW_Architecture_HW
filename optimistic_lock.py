import hazelcast

success_count = 0
max_increments = 10_000

if __name__ == "__main__":
  client = hazelcast.HazelcastClient(
  cluster_name="haz-cluster", 
  ) 

  map = client.get_map("number-map").blocking() 
  
  map.put_if_absent("key_optimistic", 0)

  while success_count < max_increments:
    current_value = map.get("key_optimistic")
    new_value = current_value + 1
    
    if map.replace_if_same("key_optimistic", current_value, new_value):
        success_count += 1

  client.shutdown()
