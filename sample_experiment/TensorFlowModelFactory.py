from AbstractModelFactory import AbstractModelFactory
from AbstractModelVisitor import AbstractModelVisitor

import os
import numpy as np
import tensorflow as tf

TMP_DIR = "tmp/"
CHECKPOINT_DIR = "tmp/tensorflow_checkpoints/"
for directory in [TMP_DIR, CHECKPOINT_DIR]:
  if not os.path.exists(directory):
    os.makedirs(directory)


class ModelFactory(AbstractModelFactory):

  def __init__(self, *args, **kwargs):
    super(ModelFactory, self).__init__(*args, **kwargs)

    self.num_epochs = 100
    self.batch_size = 50

    self.response_index = self.headers.index(self.response_header)

    possible_values = set(row[self.response_index] for row in self.all_data)
    self.num_labels = len(possible_values)

    self.hidden_layer_sizes = [50, 25] # If empty, no hidden layers are used.
    self.layer_types = [tf.nn.softmax,  # Input Layer
                        tf.nn.tanh,     # 1st Hidden Layer
                        tf.nn.tanh]     # 2nd Hidden Layer

  def build(self, train_set):
    train_matrix, train_labels = list_to_tf_input(train_set, self.response_index, self.num_labels)
    train_size, num_features = train_matrix.shape

    # Construct the layer architecture.
    x = tf.placeholder("float", shape=[None, num_features]) # Input
    y_ = tf.placeholder("float", shape=[None, self.num_labels]) # Output.

    layer_sizes = [num_features] + self.hidden_layer_sizes + [self.num_labels]
    # Generate a layer for the input and for each additional hidden layer.
    layers = [x] # Count the input as the first layer.
    for i in xrange(len(layer_sizes)-1):
      layer_size = layer_sizes[i]
      layer_type = self.layer_types[i]

      prev_layer = layers[-1]
      next_layer_size = layer_sizes[i+1]

      # Create and train a new layer.
      W = tf.Variable(tf.zeros([layer_size, next_layer_size]))
      b = tf.Variable(tf.zeros([next_layer_size]))
      new_layer = layer_type(tf.matmul(prev_layer, W) + b)

      layers.append( new_layer )

    y = layers[-1]

    # Optimization.
    cross_entropy = -tf.reduce_sum(y_*tf.log(y))
    train_step = tf.train.GradientDescentOptimizer(0.01).minimize(cross_entropy)

    saver = tf.train.Saver()  # Defaults to saving all variables.

    # Create a local session to run this computation.
    with tf.Session() as tf_session:
      # For the test data, hold the entire dataset in one constant node.
      tf.initialize_all_variables().run()

      # Iterate and train.
      for step in xrange(self.num_epochs * train_size // self.batch_size):

        offset = (step * self.batch_size) % train_size
        batch_data = train_matrix[offset:(offset + self.batch_size), :]
        batch_labels = train_labels[offset:(offset + self.batch_size)]
        train_step.run(feed_dict={x: batch_data, y_: batch_labels})

        # Save the model file each step.
        saver.save(tf_session, CHECKPOINT_DIR + 'model.ckpt', global_step=step+1)

    return ModelVisitor(saver, self.response_index, self.num_labels, x, y_, y)


class ModelVisitor(AbstractModelVisitor):

  def __init__(self, model_saver, response_index, num_labels, x, y_, y):
    self.model_saver = model_saver
    self.response_index = response_index
    self.num_labels = num_labels
    self.x = x
    self.y_ = y_
    self.y = y

  def test(self, test_set):
    test_matrix, test_labels = list_to_tf_input(test_set, self.response_index, self.num_labels)

    with tf.Session() as tf_session:
      ckpt = tf.train.get_checkpoint_state(CHECKPOINT_DIR)
      self.model_saver.restore(tf_session, ckpt.model_checkpoint_path)
      predictions = tf.argmax(self.y, 1).eval(feed_dict={self.x: test_matrix, self.y_:test_labels}, session=tf_session)

    # Produce a confusion matrix in a dictionary format from those predictions.
    conf_table = {}
    for entry, guess in zip(test_set, predictions):
      actual = entry[self.response_index]

      if not actual in conf_table:
        conf_table[actual] = {}

      if not guess in conf_table[actual]:
        conf_table[actual][guess] = 1
      else:
        conf_table[actual][guess] += 1

    return conf_table

def list_to_tf_input(data, response_index, num_labels):
  matrix = np.matrix([row[:response_index] + row[response_index+1:] for row in data])

  labels = np.asarray([row[response_index] for row in data], dtype=np.uint8)
  labels_onehot = (np.arange(num_labels) == labels[:, None]).astype(np.float32)

  return matrix, labels_onehot

def test():
  headers = ["predictor 1", "predictor 2", "response"]
  response = "response"

  train_set = [[i,0,0] for i in range(1,50)] + [[0,i,1] for i in range(1,50)]
  # Purposefully replace class "B" with "C" so that we *should* fail them.
  test_set = [[i,0,0] for i in range(1,50)] + [[0,i,1] for i in range(1,50)]
  all_data = train_set + test_set

  factory = ModelFactory(all_data, headers, response, name_prefix="test")
  print "factory settings valid? -- ",len(factory.hidden_layer_sizes)+1 == len(factory.layer_types)

  model = factory.build(train_set)
  print "factory builds ModelVisitor? -- ", isinstance(model, ModelVisitor)


  predictions = model.test(test_set)
  intended_predictions = {0: {0: 49}, 1: {1: 49}}
  print "predicting correctly? -- ", predictions == intended_predictions
  print predictions

if __name__=="__main__":
  test()