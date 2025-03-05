import hazelcast

client = hazelcast.HazelcastClient(
  cluster_name="haz-cluster", 
) 

map = client.get_map("number-map").blocking()
map.remove("key_pessimistic")

client.shutdown()
