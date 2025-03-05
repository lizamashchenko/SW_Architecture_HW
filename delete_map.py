import hazelcast

client = hazelcast.HazelcastClient(
  cluster_name="haz-cluster", 
) 

map = client.get_map("").blocking()
map.destroy()

client.shutdown()
