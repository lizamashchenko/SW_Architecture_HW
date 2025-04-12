import hazelcast

client = hazelcast.HazelcastClient(
  cluster_name="haz-cluster", 
) 

map = client.get_map("logs").blocking()
map.destroy()

client.shutdown()
