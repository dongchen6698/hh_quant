import tensorflow as tf
from tensorflow.keras.layers import Dense, Layer, Input, Concatenate
from tensorflow.keras.models import Model
from customLayer import SENetLayer


class CrossLayer(Layer):
    def __init__(self, **kwargs):
        super(CrossLayer, self).__init__(**kwargs)

    def build(self, input_shape):
        self.b = self.add_weight(name="b", shape=(input_shape[1],), initializer="zeros", trainable=True)

    def call(self, inputs):
        x0, x = inputs
        xT = tf.linalg.transpose(x)
        dot = tf.matmul(tf.expand_dims(x0, axis=1), tf.expand_dims(xT, axis=2))
        cross = tf.nn.bias_add(dot, self.b)
        return x0 + tf.squeeze(cross, axis=1)


class DCNModel(Model):
    def __init__(self, input_dim, num_cross_layers=3, deep_units=(256, 128, 64), **kwargs):
        super(DCNModel, self).__init__(**kwargs)
        self.input_dim = input_dim
        self.num_cross_layers = num_cross_layers
        self.deep_units = deep_units

        self.dense = Dense(input_dim)
        self.cross_layers = [CrossLayer() for _ in range(num_cross_layers)]
        self.deep_layers = [Dense(units, activation="relu") for units in deep_units]
        self.se_layer = SENetLayer()
        self.concat_layer = Concatenate()
        self.output_layer = Dense(1, activation="sigmoid")

    def call(self, inputs):
        x0 = x = self.dense(inputs)
        for cross_layer in self.cross_layers:
            x = cross_layer([x0, x])

        deep = inputs
        for deep_layer in self.deep_layers:
            deep = deep_layer(deep)

        x = self.concat_layer([x, deep])
        x = self.se_layer(x)
        return self.output_layer(x)

    def get_config(self):
        config = super(DCNModel, self).get_config()
        config.update({"input_dim": self.input_dim, "num_cross_layers": self.num_cross_layers, "deep_units": self.deep_units})
        return config
