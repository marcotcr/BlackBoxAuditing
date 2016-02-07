import random

def load_data():
  headers = ["Feature A (i)", "Feature B (2i)", "Feature C (-i)",
             "Constant Feature", "Random Feature", "Outcome"]
  train = [[i, 2*i, -i, 1, random.random(), "A"] for i in range(0,1000)] + \
          [[i, 2*i, -i, 1, random.random(), "B"] for i in range(1000,2000)]
  test = [[i, 2*i, -i, 1, random.random(), "A"] for i in range(0,1000)] + \
          [[i, 2*i, -i, 1, random.random(), "B"] for i in range(1000,2000)]
  return headers, train, test

def test():
  headers, train, test = load_data()
  print "load_data -- unpacks correctly? -- ", (headers != None and train != None and test != None)

if __name__=="__main__":
  test()


