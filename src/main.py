import redis
r =  redis.Redis(host="redis", port=6379)
r.lpush("list", "hello world!")
print(r.lpop("list"))
